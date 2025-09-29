import cv2
import mss
import numpy as np
import time
import struct
import os
import subprocess
from collections import deque

# Importar módulos del directorio scanner
from scanner.superReadScore import capture as read_score, SCREEN_REGION, templates_bin, DIGIT_W
from scanner.superVisor import (
    capture_region, 
    get_color_masks, 
    ratio_blocks_v3,
    color_ranges,
    screen_region as default_screen_region
)

# Importar detector automático
from auto_game_detector import AutoGameDetector

# Excepción personalizada para cuando el juego termina
class GameOverException(Exception):
    """Excepción lanzada cuando la serpiente muere y el juego termina."""
    pass

class Scanner:
    """
    Scanner que utiliza la lógica principal de la carpeta scanner/
    para detectar la posición de la cabeza y comida de la serpiente.
    """
    
    def __init__(self, screen_region=None, auto_detect=True, save_debug_images=True):
        """
        Inicializa el scanner con la región de pantalla a capturar.
        
        Args:
            screen_region: (left, top, width, height) - región de la pantalla a capturar
            auto_detect: Si True, detecta automáticamente la región del juego
            save_debug_images: Si True, guarda imágenes de debug en cada iteración
        """
        # Configuración de debug
        self.save_debug_images = save_debug_images
        self.iteration_count = 0
        self.current_movement_decision = None
        
        if self.save_debug_images:
            import os
            self.debug_folder = "debug_images"
            if not os.path.exists(self.debug_folder):
                os.makedirs(self.debug_folder)
        
        # Detección automática de región
        if auto_detect:
            self.auto_detector = AutoGameDetector()
            self.screen_region = self._detect_game_region()
            if self.screen_region is None:
                self.screen_region = screen_region or default_screen_region
        else:
            self.screen_region = screen_region or default_screen_region
        
        self.ROWS, self.COLS = 15, 17  # 15 filas, 17 columnas (grid del juego)
        
        # Configuración de colores
        self.color_ranges = color_ranges
        self.color_names = list(self.color_ranges.keys())
        self.num_colors = len(self.color_names)
        
        # Índices de colores
        self.blue_idx = self.color_names.index("blue")
        self.red_idx = self.color_names.index("red")
        self.white_idx = self.color_names.index("white")
        
        # Pre-allocación de arrays para eficiencia
        self._setup_arrays()
        
        # Estado del juego - posiciones conocidas del juego Snake de Google
        self.last_head_position = [7, 4]  # Posición inicial conocida de la cabeza [x, y]
        self.last_food_position = [7, 12]  # Posición inicial conocida de la comida [x, y]
        self.last_score = 0
    
    def _detect_game_region(self):
        """
        Detecta automáticamente la región del juego.
        
        Returns:
            Tuple[int, int, int, int]: (left, top, width, height) o None
        """
        try:
            region = self.auto_detector.detect_game_region()
            if region:
                return region
            else:
                return None
        except Exception as e:
            return None
    
    def set_movement_decision(self, direc):
        """
        Establece la decisión de movimiento para incluirla en el resumen de debug.
        
        Args:
            direc: Dirección calculada por el GreedySolver
        """
        self.current_movement_decision = direc
        
        # Actualizar el resumen de debug si existe
        if self.save_debug_images and self.iteration_count > 0:
            self._update_debug_summary()
    
    def _update_debug_summary(self):
        """
        Actualiza el resumen de debug con la decisión de movimiento.
        """
        try:
            import os
            debug_summary = f"{self.debug_folder}/iter_{self.iteration_count:03d}_summary.txt"
            if os.path.exists(debug_summary):
                # Leer el contenido actual
                with open(debug_summary, 'r') as f:
                    content = f.read()
                
                # Agregar la decisión de movimiento si no está presente
                if "Decisión de movimiento:" not in content:
                    with open(debug_summary, 'a') as f:
                        f.write(f"Decisión de movimiento: {self.current_movement_decision.name if self.current_movement_decision else 'None'}\n")
        except Exception as e:
            pass
    
    def _calculate_coordinates(self, matrix_idx, image_shape):
        """
        Calcula las coordenadas correctas usando el tamaño real de la imagen.
        
        Args:
            matrix_idx: (row, col) índice en la matriz de ratios (15x17)
            image_shape: (height, width) de la imagen capturada
            
        Returns:
            [x, y]: coordenadas en el sistema del juego (0-indexed)
        """
        import math
        
        row, col = matrix_idx
        img_h, img_w = image_shape[:2]
        
        # Calcular el tamaño de cada bloque basándose en las dimensiones reales
        # El grid del juego es 17x15, pero necesitamos +1 para los bordes
        total_cols = self.COLS + 1  # 17 + 1 = 18 (incluyendo borde derecho)
        total_rows = self.ROWS + 1  # 15 + 1 = 16 (incluyendo borde inferior)
        
        # Calcular el tamaño de cada bloque
        block_width = math.ceil(img_w / total_cols)
        block_height = math.ceil(img_h / total_rows)
        
        # Calcular las coordenadas del juego
        # El grid empieza después del borde izquierdo (1 bloque)
        game_x = int(col)  # col ya está en el rango 0-16 (17 columnas)
        game_y = int(row)  # row ya está en el rango 0-14 (15 filas)
        
        # Ajustar por el offset del scoreboard (aproximadamente 1 bloque)
        adjusted_y = max(0, game_y - 1)
        
        return [game_x, adjusted_y]
    
    def _detect_eyes_pattern(self, white_matrix):
        """
        Detecta el patrón de dos ojos blancos paralelos.
        
        Args:
            white_matrix: Matriz de valores blancos
            
        Returns:
            eyes_pattern_matrix: Matriz con patrón de ojos detectado
        """
        rows, cols = white_matrix.shape
        eyes_pattern_matrix = np.zeros_like(white_matrix)
        
        # Umbral para considerar un píxel como blanco
        white_threshold = np.percentile(white_matrix[white_matrix > 0], 50) if np.any(white_matrix > 0) else 0
        
        # Buscar patrones de ojos paralelos
        for row in range(rows):
            for col in range(cols):
                if white_matrix[row, col] > white_threshold:
                    # Verificar patrón de ojos verticales (uno encima del otro)
                    # Indica serpiente va izquierda ↔ derecha
                    if (row > 0 and white_matrix[row-1, col] > white_threshold):
                        # Dos ojos verticales encontrados
                        eyes_pattern_matrix[row, col] = white_matrix[row, col] + white_matrix[row-1, col]
                        eyes_pattern_matrix[row-1, col] = white_matrix[row, col] + white_matrix[row-1, col]
                    
                    # Verificar patrón de ojos horizontales (uno al lado del otro)
                    # Indica serpiente va arriba ↔ abajo
                    elif (col > 0 and white_matrix[row, col-1] > white_threshold):
                        # Dos ojos horizontales encontrados
                        eyes_pattern_matrix[row, col] = white_matrix[row, col] + white_matrix[row, col-1]
                        eyes_pattern_matrix[row, col-1] = white_matrix[row, col] + white_matrix[row, col-1]
        
        return eyes_pattern_matrix
    
    def _setup_arrays(self):
        """Pre-asigna arrays para mejorar el rendimiento."""
        # Usar dimensiones estándar esperadas por ratio_blocks_v3
        expected_h = self.ROWS * 35  # 15 * 35 = 525
        expected_w = self.COLS * 35  # 17 * 35 = 595
        
        # Arrays pre-asignados con dimensiones estándar
        self.masks_stack = np.zeros((self.num_colors, expected_h, expected_w), dtype=np.uint8)
        
    def capture(self):
        """
        Captura el estado actual del juego usando la lógica principal del scanner.
        
        Returns:
            tuple: (head_position, food_position) - posición de la cabeza [x,y] y posición de la comida [x,y]
        """
        # Incrementar contador de iteraciones
        self.iteration_count += 1
        
        try:
            # 1. Capturar imagen de la pantalla usando la lógica principal
            frame = capture_region(self.screen_region)
            if frame is None:
                return self.last_head_position, self.last_food_position
            
            # Verificar dimensiones de la imagen
            H, W = frame.shape[:2]
            expected_h = self.ROWS * 35  # 15 * 35 = 525
            expected_w = self.COLS * 35  # 17 * 35 = 595
            
            # Redimensionar la imagen si es necesario
            if H != expected_h or W != expected_w:
                frame = cv2.resize(frame, (expected_w, expected_h))
            
            # Guardar solo imagen original si está habilitado el debug
            if self.save_debug_images:
                original_filename = f"{self.debug_folder}/iter_{self.iteration_count:03d}_original.jpg"
                cv2.imwrite(original_filename, frame)
                
            # 2. Obtener máscaras de colores usando la lógica principal
            get_color_masks(frame, self.color_ranges, self.masks_stack)
            
            # 3. Calcular ratios por bloque usando la lógica principal
            ratios = ratio_blocks_v3(self.masks_stack)
            
            # 4. Obtener matrices de colores específicos
            blue_matrix = ratios[self.blue_idx]
            red_matrix = ratios[self.red_idx]
            
            # Detectar si el juego se ha terminado (todos los valores son 0)
            if np.max(blue_matrix) == 0.0 and np.max(red_matrix) == 0.0:
                print("💀 JUEGO TERMINADO: La serpiente ha muerto")
                raise GameOverException("La serpiente ha muerto - no se detectan elementos del juego")
            
            # 5. Detectar posición de la cabeza usando patrón de ojos paralelos
            # Obtener matriz blanca (ojos de la serpiente)
            white_matrix = ratios[self.white_idx]
            
            # Filtrar azul claro (cabeza) vs azul oscuro (cola)
            blue_light_threshold = np.percentile(blue_matrix[blue_matrix > 0], 70)  # 70% más claro
            blue_light_matrix = np.where(blue_matrix >= blue_light_threshold, blue_matrix, 0)
            
            # Detectar patrón de ojos paralelos (dos ojos blancos)
            eyes_pattern_matrix = self._detect_eyes_pattern(white_matrix)
            
            # Combinar azul claro y patrón de ojos para detectar la cabeza
            # La cabeza tiene azul claro (cuerpo) + patrón de ojos paralelos
            combined_matrix = blue_light_matrix + eyes_pattern_matrix
            
            head_idx = np.unravel_index(np.argmax(combined_matrix), combined_matrix.shape)
            head_combined_val = combined_matrix[head_idx]
            
            # Si no hay suficiente azul claro + patrón de ojos, usar posición anterior
            if head_combined_val < 50.0:  # umbral más bajo para mayor sensibilidad
                head_position = self.last_head_position
            else:
                # Usar el nuevo sistema de cálculo de coordenadas
                head_position = self._calculate_coordinates(head_idx, frame.shape)
                
            # Validar que la posición esté dentro de los límites del tablero
            if (head_position[0] < 0 or head_position[0] >= self.COLS or 
                head_position[1] < 0 or head_position[1] >= self.ROWS):
                head_position = self.last_head_position
            
            # 6. Detectar posición de la comida (roja) usando la lógica principal
            max_idx = np.unravel_index(np.argmax(red_matrix), red_matrix.shape)
            max_red_val = red_matrix[max_idx]
            
            # Si no hay suficiente rojo, no hay comida
            if max_red_val < 0.005:  # umbral aún más bajo para mayor sensibilidad
                food_position = [-1, -1]
            else:
                # Usar el nuevo sistema de cálculo de coordenadas
                food_position = self._calculate_coordinates(max_idx, frame.shape)
                
            # Validar que la posición de comida esté dentro de los límites del tablero
            if food_position != [-1, -1] and (food_position[0] < 0 or food_position[0] >= self.COLS or food_position[1] < 0 or food_position[1] >= self.ROWS):
                print(f"⚠️  Comida fuera de límites: {food_position}, usando posición anterior")
                food_position = self.last_food_position
            
            # 7. Leer puntaje actual usando la lógica principal
            current_score = read_score(SCREEN_REGION, templates_bin, digit_w=DIGIT_W)
            
            # Crear resumen de debug si está habilitado
            if self.save_debug_images:
                debug_summary = f"{self.debug_folder}/iter_{self.iteration_count:03d}_summary.txt"
                with open(debug_summary, 'w') as f:
                    f.write(f"=== Resumen de Debug - Iteración {self.iteration_count} ===\n")
                    f.write(f"Región capturada: {self.screen_region}\n")
                    f.write(f"Dimensiones: {frame.shape}\n")
                    f.write(f"Posición cabeza detectada: {head_position}\n")
                    f.write(f"Posición comida detectada: {food_position}\n")
                    f.write(f"Valor azul máximo: {np.max(blue_matrix):.3f}\n")
                    f.write(f"Valor rojo máximo: {np.max(red_matrix):.3f}\n")
                    f.write(f"Puntaje actual: {current_score}\n")
                    f.write(f"Decisión de movimiento: {self.current_movement_decision.name if self.current_movement_decision else 'None'}\n")
            
            # Actualizar estado
            self.last_head_position = head_position
            self.last_food_position = food_position
            self.last_score = current_score
            
            return head_position, food_position
            
        except Exception as e:
            print(f"❌ Error en captura: {e}")
            return self.last_head_position, self.last_food_position
            
    def cleanup(self):
        """Limpia recursos."""
        # No hay recursos específicos que limpiar en esta implementación
        pass
                    
    def __del__(self):
        """Destructor para limpiar recursos."""
        self.cleanup()