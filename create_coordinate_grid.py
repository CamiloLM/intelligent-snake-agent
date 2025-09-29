#!/usr/bin/env python3
"""
Script para crear una imagen con cuadrícula de coordenadas superpuesta
sobre la imagen original del juego, mostrando cómo se interpretan las posiciones.
"""

import cv2
import numpy as np
import os

def create_coordinate_grid(image_path, head_pos=None, food_pos=None):
    """Crea una imagen con cuadrícula de coordenadas superpuesta solo dentro del área de juego."""
    
    # Cargar imagen original
    if not os.path.exists(image_path):
        print(f"❌ No se encontró la imagen: {image_path}")
        return None
    
    # Leer imagen
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ No se pudo cargar la imagen: {image_path}")
        return None
    
    print(f"📷 Imagen cargada: {img.shape}")
    
    # Dimensiones del grid (17x15)
    COLS = 17
    ROWS = 15
    
    # Tamaño de cada celda (35x35 píxeles)
    CELL_SIZE = 35
    
    # Calcular dimensiones totales del grid
    grid_width = COLS * CELL_SIZE
    grid_height = ROWS * CELL_SIZE
    
    print(f"📐 Grid: {COLS}x{ROWS}, Celda: {CELL_SIZE}x{CELL_SIZE}")
    print(f"📐 Dimensiones totales del grid: {grid_width}x{grid_height}")
    
    # Crear copia de la imagen para dibujar
    img_with_grid = img.copy()
    
    # El grid debe estar exactamente dentro del área de juego
    # Asumiendo que la imagen ya está recortada al área de juego (525x595)
    offset_x = 0  # Comenzar desde el borde izquierdo
    offset_y = 0  # Comenzar desde el borde superior
    
    # Obtener dimensiones de la imagen
    img_h, img_w = img.shape[:2]
    
    print(f"📍 Grid posicionado en: x={offset_x}, y={offset_y}")
    
    # Dibujar líneas verticales
    for col in range(COLS + 1):
        x = offset_x + col * CELL_SIZE
        if 0 <= x < img_w:
            cv2.line(img_with_grid, (x, offset_y), (x, offset_y + grid_height), (0, 0, 255), 1)
    
    # Dibujar líneas horizontales
    for row in range(ROWS + 1):
        y = offset_y + row * CELL_SIZE
        if 0 <= y < img_h:
            cv2.line(img_with_grid, (offset_x, y), (offset_x + grid_width, y), (0, 0, 255), 1)
    
    # Dibujar coordenadas en cada celda
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.3
    font_color = (0, 255, 255)  # Amarillo
    thickness = 1
    
    for row in range(ROWS):
        for col in range(COLS):
            # Calcular posición del centro de la celda
            center_x = offset_x + col * CELL_SIZE + CELL_SIZE // 2
            center_y = offset_y + row * CELL_SIZE + CELL_SIZE // 2
            
            # Dibujar coordenadas
            coord_text = f"[{col},{row}]"
            text_size = cv2.getTextSize(coord_text, font, font_scale, thickness)[0]
            text_x = center_x - text_size[0] // 2
            text_y = center_y + text_size[1] // 2
            
            cv2.putText(img_with_grid, coord_text, (text_x, text_y), font, font_scale, font_color, thickness)
    
    # Marcar posiciones detectadas si se proporcionan
    if head_pos and len(head_pos) == 2:
        head_col, head_row = head_pos
        head_x = offset_x + head_col * CELL_SIZE + CELL_SIZE // 2
        head_y = offset_y + head_row * CELL_SIZE + CELL_SIZE // 2
        
        # Dibujar marcador de cabeza
        cv2.circle(img_with_grid, (head_x, head_y), 8, (0, 255, 255), -1)  # Círculo amarillo
        cv2.putText(img_with_grid, "H", (head_x - 5, head_y + 5), font, 0.5, (0, 0, 0), 2)
        cv2.putText(img_with_grid, f"H:[{head_col},{head_row}]", (head_x + 10, head_y - 10), font, 0.4, (0, 255, 255), 1)
    
    if food_pos and len(food_pos) == 2:
        food_col, food_row = food_pos
        food_x = offset_x + food_col * CELL_SIZE + CELL_SIZE // 2
        food_y = offset_y + food_row * CELL_SIZE + CELL_SIZE // 2
        
        # Dibujar marcador de comida
        cv2.circle(img_with_grid, (food_x, food_y), 8, (255, 0, 0), -1)  # Círculo azul
        cv2.putText(img_with_grid, "F", (food_x - 5, food_y + 5), font, 0.5, (255, 255, 255), 2)
        cv2.putText(img_with_grid, f"F:[{food_col},{food_row}]", (food_x + 10, food_y - 10), font, 0.4, (255, 0, 0), 1)
    
    # Guardar imagen con grid
    output_path = image_path.replace("_original.jpg", "_original_grid.jpg")
    cv2.imwrite(output_path, img_with_grid)
    
    print(f"✅ Imagen con grid guardada: {output_path}")
    if head_pos:
        print(f"📍 Cabeza marcada en: {head_pos}")
    if food_pos:
        print(f"📍 Comida marcada en: {food_pos}")
    
    return output_path

if __name__ == "__main__":
    # Ejemplo de uso
    create_coordinate_grid("debug_images/iter_001_original.jpg", [4, 7], [12, 7])
