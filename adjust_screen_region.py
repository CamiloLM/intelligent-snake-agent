#!/usr/bin/env python3
"""
Script para ajustar la región de captura de pantalla interactivamente.
"""

import cv2
import numpy as np
import mss
from scanner.superVisor import capture_region, screen_region

def adjust_screen_region():
    """
    Ajusta la región de captura de pantalla.
    """
    print("=== Ajuste de Región de Captura ===\n")
    
    try:
        print("Instrucciones:")
        print("1. Abre el juego Snake de Google en tu navegador")
        print("2. Asegúrate de que el juego esté visible")
        print("3. Presiona Enter para capturar la pantalla completa")
        print("4. Selecciona la región del juego con el mouse")
        print("5. Presiona Enter para confirmar")
        
        input("\nPresiona Enter cuando estés listo...")
        
        # Capturar pantalla completa
        with mss.mss() as sct:
            # Obtener información de la pantalla
            monitor = sct.monitors[1]  # Monitor principal
            print(f"Monitor principal: {monitor}")
            
            # Capturar pantalla completa
            screenshot = sct.grab(monitor)
            img = np.array(screenshot)
            img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            print(f"Pantalla completa capturada: {img_bgr.shape}")
            
            # Guardar imagen completa
            cv2.imwrite("debug_full_screen.jpg", img_bgr)
            print("✓ Imagen completa guardada como 'debug_full_screen.jpg'")
            
            # Mostrar imagen y permitir selección de región
            print("\nSelecciona la región del juego Snake:")
            print("- Haz clic y arrastra para seleccionar la región")
            print("- Presiona 'r' para reiniciar la selección")
            print("- Presiona 'q' para salir")
            
            # Función para manejar la selección de región
            def mouse_callback(event, x, y, flags, param):
                if event == cv2.EVENT_LBUTTONDOWN:
                    param['start_point'] = (x, y)
                elif event == cv2.EVENT_LBUTTONUP:
                    param['end_point'] = (x, y)
                    param['selected'] = True
            
            # Variables para la selección
            selection_data = {'start_point': None, 'end_point': None, 'selected': False}
            
            # Mostrar imagen y permitir selección
            cv2.namedWindow('Selecciona la región del juego Snake', cv2.WINDOW_NORMAL)
            cv2.setMouseCallback('Selecciona la región del juego Snake', mouse_callback, selection_data)
            
            while True:
                img_copy = img_bgr.copy()
                
                # Dibujar rectángulo de selección
                if selection_data['start_point'] and selection_data['end_point']:
                    cv2.rectangle(img_copy, selection_data['start_point'], selection_data['end_point'], (0, 255, 0), 2)
                
                cv2.imshow('Selecciona la región del juego Snake', img_copy)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    selection_data['start_point'] = None
                    selection_data['end_point'] = None
                    selection_data['selected'] = False
                elif selection_data['selected']:
                    break
            
            cv2.destroyAllWindows()
            
            # Procesar la selección
            if selection_data['start_point'] and selection_data['end_point']:
                x1, y1 = selection_data['start_point']
                x2, y2 = selection_data['end_point']
                
                # Asegurar que x1 < x2 y y1 < y2
                left = min(x1, x2)
                top = min(y1, y2)
                width = abs(x2 - x1)
                height = abs(y2 - y1)
                
                print(f"\nRegión seleccionada:")
                print(f"  Left: {left}")
                print(f"  Top: {top}")
                print(f"  Width: {width}")
                print(f"  Height: {height}")
                
                # Probar la nueva región
                new_region = (left, top, width, height)
                print(f"\nProbando nueva región: {new_region}")
                
                # Capturar con la nueva región
                test_frame = capture_region(new_region)
                if test_frame is not None:
                    cv2.imwrite("debug_new_region.jpg", test_frame)
                    print("✓ Nueva región probada y guardada como 'debug_new_region.jpg'")
                    
                    # Mostrar cómo actualizar el código
                    print(f"\nPara usar esta región, actualiza scanner/superVisor.py:")
                    print(f"screen_region = {new_region}")
                else:
                    print("✗ Error al capturar con la nueva región")
            else:
                print("✗ No se seleccionó ninguna región")
        
    except Exception as e:
        print(f"✗ Error durante el ajuste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    adjust_screen_region()

