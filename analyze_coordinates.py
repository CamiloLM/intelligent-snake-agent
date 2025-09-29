#!/usr/bin/env python3
"""
Script para analizar las coordenadas detectadas vs las esperadas.
"""

from game_scanner import Scanner
import cv2
import numpy as np

def analyze_coordinates():
    """
    Analiza las coordenadas detectadas y las compara con las esperadas.
    """
    print("=== Análisis de Coordenadas ===\n")
    
    print("Coordenadas esperadas según la imagen:")
    print("  - Cabeza: [15, 7] (columna 15, fila 7)")
    print("  - Comida: [3, 8] (columna 3, fila 8)")
    print("  - Grid: 17x15 (17 columnas, 15 filas)")
    print("  - Límites: x=[0-16], y=[0-14]")
    
    try:
        # Crear scanner
        print("\n🔧 Creando scanner...")
        scanner = Scanner(save_debug_images=True)
        print("✅ Scanner creado\n")
        
        # Realizar captura
        print("📸 Realizando captura...")
        head_position, food_position = scanner.capture()
        print(f"✅ Resultado: Cabeza: {head_position}, Comida: {food_position}\n")
        
        # Analizar las coordenadas
        print("🔍 Análisis detallado:")
        print(f"  - Cabeza detectada: {head_position} (tipo: {type(head_position[0])})")
        print(f"  - Cabeza esperada: [15, 7]")
        print(f"  - Comida detectada: {food_position} (tipo: {type(food_position[0])})")
        print(f"  - Comida esperada: [3, 8]")
        
        # Calcular diferencias
        if head_position != [-1, -1]:
            head_diff_x = head_position[0] - 15
            head_diff_y = head_position[1] - 7
            print(f"  - Diferencia cabeza: x={head_diff_x}, y={head_diff_y}")
        
        if food_position != [-1, -1]:
            food_diff_x = food_position[0] - 3
            food_diff_y = food_position[1] - 8
            print(f"  - Diferencia comida: x={food_diff_x}, y={food_diff_y}")
        
        # Verificar si las coordenadas están dentro de los límites
        print(f"\n📏 Verificación de límites:")
        print(f"  - Límites del grid: x=[0-16], y=[0-14]")
        
        if head_position != [-1, -1]:
            head_in_bounds = (0 <= head_position[0] <= 16 and 0 <= head_position[1] <= 14)
            print(f"  - Cabeza dentro de límites: {head_in_bounds}")
        
        if food_position != [-1, -1]:
            food_in_bounds = (0 <= food_position[0] <= 16 and 0 <= food_position[1] <= 14)
            print(f"  - Comida dentro de límites: {food_in_bounds}")
        
        # Limpiar recursos
        scanner.cleanup()
        print("\n✅ Recursos limpiados")
        
        print("\n🎉 Análisis completado")
        
    except Exception as e:
        print(f"❌ Error durante el análisis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_coordinates()

