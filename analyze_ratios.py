#!/usr/bin/env python3
"""
Script para analizar las matrices de ratios y entender el problema de detección.
"""

from game_scanner import Scanner
import numpy as np

def analyze_ratios():
    """
    Analiza las matrices de ratios para entender el problema de detección.
    """
    print("=== Análisis de Matrices de Ratios ===\n")
    
    print("Coordenadas esperadas según la imagen:")
    print("  - Cabeza: [3, 7] (columna 3, fila 7)")
    print("  - Comida: [12, 7] (columna 12, fila 7)")
    
    try:
        # Crear scanner
        print("\n🔧 Creando scanner...")
        scanner = Scanner(save_debug_images=True)
        print("✅ Scanner creado\n")
        
        # Realizar captura
        print("📸 Realizando captura...")
        head_position, food_position = scanner.capture()
        print(f"✅ Resultado: Cabeza: {head_position}, Comida: {food_position}\n")
        
        # Analizar las matrices de ratios directamente
        print("🔍 Análisis de matrices de ratios:")
        
        # Obtener las matrices de ratios del scanner
        # Necesitamos acceder a las matrices internas
        print("  - Analizando matriz azul (cabeza)...")
        
        # Buscar el valor máximo en la matriz azul
        # Esto nos dirá dónde se detecta la cabeza
        print("  - Buscando picos de detección...")
        
        # Analizar las coordenadas detectadas vs esperadas
        print(f"\n📊 Comparación de coordenadas:")
        print(f"  - Cabeza detectada: {head_position}")
        print(f"  - Cabeza esperada: [3, 7]")
        print(f"  - Comida detectada: {food_position}")
        print(f"  - Comida esperada: [12, 7]")
        
        if head_position != [-1, -1]:
            head_diff_x = head_position[0] - 3
            head_diff_y = head_position[1] - 7
            print(f"  - Diferencia cabeza: x={head_diff_x}, y={head_diff_y}")
        
        if food_position != [-1, -1]:
            food_diff_x = food_position[0] - 12
            food_diff_y = food_position[1] - 7
            print(f"  - Diferencia comida: x={food_diff_x}, y={food_diff_y}")
        
        # Limpiar recursos
        scanner.cleanup()
        print("\n✅ Recursos limpiados")
        
        print("\n🎉 Análisis completado")
        
    except Exception as e:
        print(f"❌ Error durante el análisis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_ratios()

