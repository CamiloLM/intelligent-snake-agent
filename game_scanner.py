import cv2
import mss
import numpy as np
import time
import struct
import os
import subprocess
import threading
from collections import deque

# Importar módulos del directorio scanner
from scanner import superReadScore
from scanner import superVisor

# Configurar imports específicos
read_score = superReadScore.capture
SCREEN_REGION = superReadScore.SCREEN_REGION
templates_bin = superReadScore.templates_bin
DIGIT_W = superReadScore.DIGIT_W

capture_region = superVisor.capture_region
get_color_masks = superVisor.get_color_masks
ratio_blocks_v3 = superVisor.ratio_blocks_v3
color_ranges = superVisor.color_ranges
default_screen_region = superVisor.screen_region

class Scanner:
    """
    Scanner integrado que combina la funcionalidad de superVisor, superSnake y superReadScore
    para capturar el estado del juego y comunicarse con el algoritmo C.
    """
    
    def __init__(self, screen_region=None):
        """
        Inicializa el scanner con la región de pantalla a capturar.
        
        Args:
            screen_region: (left, top, width, height) - región de la pantalla a capturar
        """
        self.screen_region = screen_region or default_screen_region
        self.ROWS, self.COLS = 15, 17
        
        # Configuración de colores
        self.color_ranges = color_ranges
        self.color_names = list(self.color_ranges.keys())
        self.num_colors = len(self.color_names)
        
        # Índices de colores
        self.blue_idx = self.color_names.index("blue")
        self.red_idx = self.color_names.index("red")
        self.white_idx = self.color_names.index("white")
        
        # Configuración de FIFOs para comunicación con C
        self.fifo_py_to_c = "py_to_c.fifo"
        self.fifo_c_to_py = "c_to_py.fifo"
        
        # Pre-allocación de arrays para eficiencia
        self._setup_arrays()
        
        # Configuración de FIFOs
        self._setup_fifos()
        
        # Proceso C
        self.c_process = None
        self.fd_out = None
        self.fd_in = None
        
        # Estado del juego
        self.last_snake_body = None
        self.last_food_position = None
        self.last_score = 0
        
    def _setup_arrays(self):
        """Pre-asigna arrays para mejorar el rendimiento."""
        # Capturar una imagen de prueba para obtener dimensiones
        test_frame = capture_region(self.screen_region)
        H, W, _ = test_frame.shape
        
        # Arrays pre-asignados
        self.masks_stack = np.zeros((self.num_colors, H, W), dtype=np.uint8)
        
    def _setup_fifos(self):
        """Configura los FIFOs para comunicación con el proceso C."""
        # Crear FIFOs si no existen
        for fifo in (self.fifo_py_to_c, self.fifo_c_to_py):
            if not os.path.exists(fifo):
                os.mkfifo(fifo)
                
    def _start_c_process(self):
        """Inicia el proceso C que ejecuta el algoritmo de decisión."""
        if self.c_process is None:
            # Compilar el código C si es necesario
            c_file = "scanner/superSnake_v2.c"
            h_file = "scanner/superSnake_v2.h"
            
            if os.path.exists(c_file) and os.path.exists(h_file):
                # Compilar el código C
                compile_cmd = ["gcc", "-o", "superSnake_c", c_file]
                try:
                    subprocess.run(compile_cmd, check=True, capture_output=True)
                    print("Código C compilado exitosamente")
                except subprocess.CalledProcessError as e:
                    print(f"Error compilando código C: {e}")
                    return False
                    
                # Ejecutar el proceso C
                self.c_process = subprocess.Popen(["./superSnake_c"])
                
                # Abrir FIFOs
                self.fd_out = open(self.fifo_py_to_c, "wb", buffering=0)
                self.fd_in = open(self.fifo_c_to_py, "rb", buffering=0)
                
                return True
            else:
                print("Archivos C no encontrados")
                return False
        return True
        
    def _stop_c_process(self):
        """Detiene el proceso C y cierra las conexiones."""
        if self.c_process:
            self.c_process.terminate()
            self.c_process.wait()
            self.c_process = None
            
        if self.fd_out:
            self.fd_out.close()
            self.fd_out = None
            
        if self.fd_in:
            self.fd_in.close()
            self.fd_in = None
            
    def capture(self):
        """
        Captura el estado actual del juego y obtiene la decisión del algoritmo C.
        
        Returns:
            tuple: (snake_body, food_position) - cuerpo de la serpiente y posición de la comida
        """
        try:
            # 1. Capturar imagen de la pantalla
            frame = capture_region(self.screen_region)
            if frame is None:
                return self.last_snake_body, self.last_food_position
                
            # 2. Obtener máscaras de colores
            get_color_masks(frame, self.color_ranges, self.masks_stack)
            
            # 3. Calcular ratios por bloque
            ratios = ratio_blocks_v3(self.masks_stack)
            
            # 4. Obtener matrices de colores específicos
            blue_matrix = ratios[self.blue_idx]
            red_matrix = ratios[self.red_idx]
            
            # 5. Detectar posición de la comida (roja)
            max_idx = np.unravel_index(np.argmax(red_matrix), red_matrix.shape)
            max_red_val = red_matrix[max_idx]
            
            # Si no hay suficiente rojo, no hay comida
            if max_red_val < 0.12:  # umbral ajustado
                food_position = (-1, -1)
            else:
                food_position = (max_idx[0], max_idx[1])
                
            # 6. Leer puntaje actual
            current_score = read_score(SCREEN_REGION, templates_bin, digit_w=DIGIT_W)
            
            # 7. Preparar datos para el algoritmo C
            blue_matrix_float = blue_matrix.astype(np.float32)
            extra_info = (food_position[0], food_position[1], current_score)
            
            # 8. Enviar datos al proceso C y obtener decisión
            move = self._get_c_decision(blue_matrix_float, extra_info)
            
            # 9. Convertir decisión a movimiento de serpiente
            snake_body, new_food_position = self._process_c_decision(move, food_position, current_score)
            
            # Actualizar estado
            self.last_snake_body = snake_body
            self.last_food_position = new_food_position
            self.last_score = current_score
            
            return snake_body, new_food_position
            
        except Exception as e:
            print(f"Error en captura: {e}")
            return self.last_snake_body, self.last_food_position
            
    def _get_c_decision(self, blue_matrix, extra_info):
        """
        Envía datos al proceso C y obtiene la decisión de movimiento.
        
        Args:
            blue_matrix: matriz de ratios azules
            extra_info: información adicional (comida, puntaje)
            
        Returns:
            int: código de movimiento del algoritmo C
        """
        if not self._start_c_process():
            return 0
            
        try:
            # Construir payload
            payload = blue_matrix.tobytes() + struct.pack("3i", *extra_info)
            
            # Enviar datos
            self.fd_out.write(payload)
            
            # Leer respuesta
            data = self.fd_in.read(4)
            if len(data) == 4:
                response, = struct.unpack("i", data)
                return response
            else:
                return 0
                
        except Exception as e:
            print(f"Error comunicándose con proceso C: {e}")
            return 0
            
    def _process_c_decision(self, move, food_position, score):
        """
        Procesa la decisión del algoritmo C y actualiza el estado de la serpiente.
        
        Args:
            move: código de movimiento del algoritmo C
            food_position: posición de la comida
            score: puntaje actual
            
        Returns:
            tuple: (snake_body, food_position)
        """
        # Si no hay decisión válida, mantener estado anterior
        if move == 0:
            return self.last_snake_body, self.last_food_position
            
        # Convertir código de movimiento a dirección
        direction = self._decode_move(move)
        
        # Actualizar cuerpo de la serpiente basado en la decisión
        snake_body = self._update_snake_body(direction, food_position, score)
        
        return snake_body, food_position
        
    def _decode_move(self, move):
        """
        Decodifica el código de movimiento del algoritmo C.
        
        Args:
            move: código de movimiento (8=Norte, 4=Sur, 2=Este, 1=Oeste)
            
        Returns:
            str: dirección ('up', 'down', 'right', 'left')
        """
        if move == 8:  # Norte
            return 'up'
        elif move == 4:  # Sur
            return 'down'
        elif move == 2:  # Este
            return 'right'
        elif move == 1:  # Oeste
            return 'left'
        else:
            return 'right'  # dirección por defecto
            
    def _update_snake_body(self, direction, food_position, score):
        """
        Actualiza el cuerpo de la serpiente basado en la decisión del algoritmo.
        
        Args:
            direction: dirección del movimiento
            food_position: posición de la comida
            score: puntaje actual
            
        Returns:
            list: nuevo cuerpo de la serpiente
        """
        if self.last_snake_body is None:
            # Estado inicial
            return [(8, 7), (8, 6), (8, 5)]
            
        # Simular movimiento de la serpiente
        head = self.last_snake_body[0]
        new_head = self._move_head(head, direction)
        
        # Crear nuevo cuerpo
        new_body = [new_head] + self.last_snake_body[:-1]
        
        # Si comió comida, agregar segmento
        if food_position != (-1, -1) and new_head == food_position:
            new_body.append(self.last_snake_body[-1])
            
        return new_body
        
    def _move_head(self, head, direction):
        """
        Calcula la nueva posición de la cabeza basada en la dirección.
        
        Args:
            head: posición actual de la cabeza (row, col)
            direction: dirección del movimiento
            
        Returns:
            tuple: nueva posición de la cabeza
        """
        row, col = head
        
        if direction == 'up':
            return (max(0, row - 1), col)
        elif direction == 'down':
            return (min(self.ROWS - 1, row + 1), col)
        elif direction == 'left':
            return (row, max(0, col - 1))
        elif direction == 'right':
            return (row, min(self.COLS - 1, col + 1))
        else:
            return head
            
    def cleanup(self):
        """Limpia recursos y detiene procesos."""
        self._stop_c_process()
        
        # Limpiar FIFOs
        for fifo in (self.fifo_py_to_c, self.fifo_c_to_py):
            if os.path.exists(fifo):
                try:
                    os.unlink(fifo)
                except:
                    pass
                    
    def __del__(self):
        """Destructor para limpiar recursos."""
        self.cleanup()