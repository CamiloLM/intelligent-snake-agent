#!/usr/bin/env python3
"""
Sistema de detección automática del juego Snake de Google.
Detecta automáticamente la posición y tamaño del juego en cualquier configuración de pantalla.
"""

import cv2
import numpy as np
import mss
from typing import Tuple, Optional, List

class AutoGameDetector:
    """
    Detecta automáticamente el juego Snake de Google en la pantalla.
    """
    
    def __init__(self):
        """Inicializa el detector automático."""
        print("(auto_game_detector.py) <__init__> Inicializando detector automático...")
        
        # Características del juego Snake de Google
        self.game_features = {
            # Color del fondo del juego (verde claro)
            'background_color': {
                'hsv_lower': np.array([35, 40, 40]),
                'hsv_upper': np.array([85, 255, 255])
            },
            # Color del borde del juego (verde oscuro)
            'border_color': {
                'hsv_lower': np.array([35, 100, 50]),
                'hsv_upper': np.array([85, 255, 150])
            },
            # Color de la serpiente (azul)
            'snake_color': {
                'hsv_lower': np.array([100, 50, 50]),
                'hsv_upper': np.array([130, 255, 255])
            },
            # Color de la comida (rojo)
            'food_color': {
                'hsv_lower': np.array([0, 70, 50]),
                'hsv_upper': np.array([10, 255, 255])
            }
        }
        
        # Tamaño mínimo esperado del juego (en píxeles)
        self.min_game_size = (400, 400)  # ancho, alto mínimo
        
        print("(auto_game_detector.py) <__init__> Características del juego configuradas")
        print("(auto_game_detector.py) <__init__> Detector automático inicializado")
    
    def detect_game_region(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Detecta automáticamente la región del juego Snake.
        
        Returns:
            Tuple[int, int, int, int]: (left, top, width, height) o None si no se encuentra
        """
        print("(auto_game_detector.py) <detect_game_region> Iniciando detección automática...")
        
        try:
            # 1. Capturar pantalla completa
            print("(auto_game_detector.py) <detect_game_region> Capturando pantalla completa...")
            with mss.mss() as sct:
                monitor = sct.monitors[1]  # Monitor principal
                screenshot = sct.grab(monitor)
                img = np.array(screenshot)
                img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                print(f"(auto_game_detector.py) <detect_game_region> Pantalla capturada: {img_bgr.shape}")
            
            # 2. Buscar regiones con características del juego
            print("(auto_game_detector.py) <detect_game_region> Analizando características del juego...")
            game_regions = self._find_game_candidates(img_bgr)
            print(f"(auto_game_detector.py) <detect_game_region> Regiones candidatas encontradas: {len(game_regions)}")
            
            # 3. Evaluar cada región candidata
            best_region = None
            best_score = 0
            
            for region in game_regions:
                print(f"(auto_game_detector.py) <detect_game_region> Evaluando región: {region}")
                score = self._evaluate_game_region(img_bgr, region)
                print(f"(auto_game_detector.py) <detect_game_region> Puntuación: {score}")
                
                if score > best_score:
                    best_score = score
                    best_region = region
            
            if best_region:
                print(f"(auto_game_detector.py) <detect_game_region> Mejor región encontrada: {best_region} (puntuación: {best_score})")
                return best_region
            else:
                print("(auto_game_detector.py) <detect_game_region> No se encontró el juego")
                return None
                
        except Exception as e:
            print(f"(auto_game_detector.py) <detect_game_region> Error en detección: {e}")
            return None
    
    def _find_game_candidates(self, img: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Encuentra regiones candidatas que podrían contener el juego.
        
        Args:
            img: Imagen de la pantalla completa
            
        Returns:
            List[Tuple[int, int, int, int]]: Lista de regiones candidatas
        """
        print("(auto_game_detector.py) <_find_game_candidates> Buscando regiones candidatas...")
        
        candidates = []
        
        # Convertir a HSV para mejor detección de color
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Buscar específicamente el borde verde oscuro del juego
        print("(auto_game_detector.py) <_find_game_candidates> Detectando borde verde oscuro...")
        border_mask = cv2.inRange(hsv, 
                                 self.game_features['border_color']['hsv_lower'],
                                 self.game_features['border_color']['hsv_upper'])
        
        # Encontrar contornos del borde
        contours, _ = cv2.findContours(border_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"(auto_game_detector.py) <_find_game_candidates> Contornos de borde encontrados: {len(contours)}")
        
        for contour in contours:
            # Obtener rectángulo del contorno
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filtrar por tamaño mínimo
            if w >= self.min_game_size[0] and h >= self.min_game_size[1]:
                # Verificar que la región sea aproximadamente cuadrada (juego Snake es cuadrado)
                aspect_ratio = w / h
                if 0.7 <= aspect_ratio <= 1.3:  # Permitir cierta variación
                    # Verificar que el contorno tenga forma de rectángulo (borde del juego)
                    area = cv2.contourArea(contour)
                    rect_area = w * h
                    if area / rect_area > 0.8:  # El contorno debe llenar la mayor parte del rectángulo
                        candidates.append((x, y, w, h))
                        print(f"(auto_game_detector.py) <_find_game_candidates> Candidato válido: ({x}, {y}, {w}, {h}) - ratio: {aspect_ratio:.2f}, área: {area/rect_area:.2f}")
        
        return candidates
    
    def _evaluate_game_region(self, img: np.ndarray, region: Tuple[int, int, int, int]) -> float:
        """
        Evalúa qué tan probable es que una región contenga el juego Snake.
        
        Args:
            img: Imagen completa
            region: (x, y, width, height) de la región a evaluar
            
        Returns:
            float: Puntuación de 0 a 1 (1 = muy probable que sea el juego)
        """
        x, y, w, h = region
        
        # Extraer la región
        roi = img[y:y+h, x:x+w]
        if roi.size == 0:
            return 0.0
        
        # Convertir a HSV
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        score = 0.0
        
        # 1. Verificar presencia de color de fondo verde
        green_mask = cv2.inRange(hsv_roi,
                               self.game_features['background_color']['hsv_lower'],
                               self.game_features['background_color']['hsv_upper'])
        green_ratio = np.sum(green_mask > 0) / green_mask.size
        if green_ratio > 0.3:  # Al menos 30% de verde
            score += 0.4
            print(f"(auto_game_detector.py) <_evaluate_game_region> Verde detectado: {green_ratio:.2f}")
        
        # 2. Verificar presencia de color azul (serpiente)
        blue_mask = cv2.inRange(hsv_roi,
                              self.game_features['snake_color']['hsv_lower'],
                              self.game_features['snake_color']['hsv_upper'])
        blue_ratio = np.sum(blue_mask > 0) / blue_mask.size
        if blue_ratio > 0.01:  # Al menos algo de azul
            score += 0.3
            print(f"(auto_game_detector.py) <_evaluate_game_region> Azul detectado: {blue_ratio:.2f}")
        
        # 3. Verificar presencia de color rojo (comida)
        red_mask = cv2.inRange(hsv_roi,
                             self.game_features['food_color']['hsv_lower'],
                             self.game_features['food_color']['hsv_upper'])
        red_ratio = np.sum(red_mask > 0) / red_mask.size
        if red_ratio > 0.001:  # Al menos algo de rojo
            score += 0.3
            print(f"(auto_game_detector.py) <_evaluate_game_region> Rojo detectado: {red_ratio:.2f}")
        
        print(f"(auto_game_detector.py) <_evaluate_game_region> Puntuación total: {score:.2f}")
        return score
    
    def test_detection(self) -> None:
        """
        Prueba la detección automática y guarda imágenes de debug.
        """
        print("(auto_game_detector.py) <test_detection> Probando detección automática...")
        
        # Detectar región
        region = self.detect_game_region()
        
        if region:
            print(f"(auto_game_detector.py) <test_detection> ✓ Región detectada: {region}")
            
            # Capturar y guardar la región detectada
            with mss.mss() as sct:
                screenshot = sct.grab(region)
                img = np.array(screenshot)
                img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                
                cv2.imwrite("auto_detected_region.jpg", img_bgr)
                print("(auto_game_detector.py) <test_detection> ✓ Región guardada como 'auto_detected_region.jpg'")
        else:
            print("(auto_game_detector.py) <test_detection> ✗ No se pudo detectar el juego")
            print("(auto_game_detector.py) <test_detection> Asegúrate de que el juego Snake esté abierto y visible")

if __name__ == "__main__":
    detector = AutoGameDetector()
    detector.test_detection()
