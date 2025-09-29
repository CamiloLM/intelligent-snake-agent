#!/usr/bin/env python3
"""
Script de prueba para verificar la integración del sistema scanner.
"""

import sys
import os
import time

def test_scanner_imports():
    """Prueba que se pueden importar todos los módulos necesarios."""
    print("Probando imports...")
    
    try:
        from game_scanner import Scanner
        print("✓ Scanner importado correctamente")
    except ImportError as e:
        print(f"✗ Error importando Scanner: {e}")
        return False
        
    try:
        from scanner.superReadScore import capture as read_score
        print("✓ superReadScore importado correctamente")
    except ImportError as e:
        print(f"✗ Error importando superReadScore: {e}")
        return False
        
    try:
        from scanner.superVisor import capture_region, get_color_masks
        print("✓ superVisor importado correctamente")
    except ImportError as e:
        print(f"✗ Error importando superVisor: {e}")
        return False
        
    return True

def test_scanner_initialization():
    """Prueba la inicialización del scanner."""
    print("\nProbando inicialización del scanner...")
    
    try:
        from game_scanner import Scanner
        scanner = Scanner()
        print("✓ Scanner inicializado correctamente")
        
        # Verificar que tiene los atributos necesarios
        assert hasattr(scanner, 'screen_region'), "Falta screen_region"
        assert hasattr(scanner, 'color_ranges'), "Falta color_ranges"
        assert hasattr(scanner, 'masks_stack'), "Falta masks_stack"
        print("✓ Atributos del scanner verificados")
        
        # Limpiar
        scanner.cleanup()
        print("✓ Scanner limpiado correctamente")
        
        return True
        
    except Exception as e:
        print(f"✗ Error inicializando scanner: {e}")
        return False

def test_agent_initialization():
    """Prueba la inicialización del agente."""
    print("\nProbando inicialización del agente...")
    
    try:
        from main import Agent
        
        # Probar modo integrado
        agent_integrated = Agent(use_integrated_scanner=True)
        print("✓ Agente en modo integrado inicializado")
        
        # Probar modo original
        agent_original = Agent(use_integrated_scanner=False)
        print("✓ Agente en modo original inicializado")
        
        # Limpiar
        if hasattr(agent_integrated.scanner, 'cleanup'):
            agent_integrated.scanner.cleanup()
        if hasattr(agent_original.scanner, 'cleanup'):
            agent_original.scanner.cleanup()
            
        return True
        
    except Exception as e:
        print(f"✗ Error inicializando agente: {e}")
        return False

def test_file_structure():
    """Verifica que todos los archivos necesarios existen."""
    print("\nVerificando estructura de archivos...")
    
    required_files = [
        'scanner/superReadScore.py',
        'scanner/superVisor.py', 
        'scanner/superSnake.py',
        'scanner/superSnake_v2.c',
        'scanner/superSnake_v2.h',
        'assets/digits/0.png',
        'assets/digits/1.png',
        'assets/digits/2.png',
        'assets/digits/3.png',
        'assets/digits/4.png',
        'assets/digits/5.png',
        'assets/digits/6.png',
        'assets/digits/7.png',
        'assets/digits/8.png',
        'assets/digits/9.png',
        'assets/digits/empty.png'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("✗ Archivos faltantes:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    else:
        print("✓ Todos los archivos necesarios están presentes")
        return True

def main():
    """Función principal de prueba."""
    print("=== Prueba de Integración del Sistema Scanner ===\n")
    
    tests = [
        ("Estructura de archivos", test_file_structure),
        ("Imports de módulos", test_scanner_imports),
        ("Inicialización del scanner", test_scanner_initialization),
        ("Inicialización del agente", test_agent_initialization),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Ejecutando: {test_name}")
        print('='*50)
        
        if test_func():
            passed += 1
            print(f"✓ {test_name}: PASÓ")
        else:
            print(f"✗ {test_name}: FALLÓ")
    
    print(f"\n{'='*50}")
    print(f"RESULTADOS: {passed}/{total} pruebas pasaron")
    print('='*50)
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! La integración está lista.")
        return 0
    else:
        print("❌ Algunas pruebas fallaron. Revisa los errores arriba.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
