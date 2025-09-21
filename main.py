import cv2
import numpy as np
import pyautogui
import logging
from datetime import datetime
import os

class GameScanner:
    def __init__(self, apple_asset, eye_asset, tile_size=25):
        # Configurar logging
        self.setup_logging()
        
        # Cargar assets
        self.apple_asset = cv2.imread(apple_asset, cv2.IMREAD_UNCHANGED)
        self.eye_asset = cv2.imread(eye_asset, cv2.IMREAD_UNCHANGED)
        
        self.logger.info(f"🔧 Inicializando GameScanner con tile_size={tile_size}")
        self.logger.info(f"📁 Cargando assets: {apple_asset}, {eye_asset}")

        # Convertir a BGR si tienen canal alfa
        if self.apple_asset is not None and self.apple_asset.shape[2] == 4:
            self.apple_asset = cv2.cvtColor(self.apple_asset, cv2.COLOR_BGRA2BGR)
            self.logger.info("🍎 Asset de manzana convertido de BGRA a BGR")
        if self.eye_asset is not None and self.eye_asset.shape[2] == 4:
            self.eye_asset = cv2.cvtColor(self.eye_asset, cv2.COLOR_BGRA2BGR)
            self.logger.info("👁️ Asset de ojos convertido de BGRA a BGR")

        # 🔥 Escalar al tamaño de la celda
        self.apple_asset = cv2.resize(self.apple_asset, (tile_size, tile_size), interpolation=cv2.INTER_AREA)
        self.eye_asset = cv2.resize(self.eye_asset, (tile_size, tile_size), interpolation=cv2.INTER_AREA)
        
        self.logger.info(f"📏 Assets escalados a {tile_size}x{tile_size} píxeles")
        self.tile_size = tile_size

    def setup_logging(self):
        """Configura el sistema de logging"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_timestamp = timestamp
        log_filename = f"game_scanner_log_{timestamp}.txt"
        
        # Crear directorio para imágenes de esta sesión
        self.images_dir = f"detection_images_{timestamp}"
        os.makedirs(self.images_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()  # También muestra en consola
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"📝 Log iniciado en archivo: {log_filename}")
        self.logger.info(f"📁 Directorio de imágenes: {self.images_dir}")

    def capture_board(self):
        """Captura la pantalla y recorta automáticamente el tablero usando bordes"""
        self.logger.info("📸 Capturando pantalla...")
        screenshot = pyautogui.screenshot()
        frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        self.logger.info(f"🖼️ Screenshot capturado: {frame.shape[1]}x{frame.shape[0]} píxeles")

        # Convertir a gris y buscar bordes
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        self.logger.info(f"🔍 Encontrados {len(contours)} contornos")

        if not contours:
            self.logger.warning("⚠️ No se encontraron contornos, devolviendo frame completo")
            return frame

        # Buscar el contorno más grande (probable tablero)
        board_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(board_contour)
        board = frame[y:y+h, x:x+w]
        
        self.logger.info(f"🎯 Tablero detectado: posición ({x},{y}), tamaño {w}x{h}")
        self.logger.info(f"📐 Tablero recortado: {board.shape[1]}x{board.shape[0]} píxeles")
        
        return board

    def match_template(self, board, template, threshold=0.8, template_name="template"):
        """Busca coincidencias del template en la imagen"""
        if template is None or board is None:
            self.logger.warning(f"⚠️ Template o board es None para {template_name}")
            return []

        # ⚠️ Validación de tamaño
        if board.shape[0] < template.shape[0] or board.shape[1] < template.shape[1]:
            self.logger.warning(f"⚠️ Board muy pequeño para {template_name}: {board.shape} vs {template.shape}")
            return []

        result = cv2.matchTemplate(board, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(result >= threshold)
        matches = list(zip(*loc[::-1]))  # (x, y) de cada match
        
        self.logger.info(f"🎯 {template_name}: {len(matches)} coincidencias encontradas (threshold={threshold})")
        if matches:
            self.logger.info(f"📍 Posiciones de {template_name}: {matches[:5]}{'...' if len(matches) > 5 else ''}")
        
        return matches

    def save_detection_image(self, board, apples, eyes, frame_num):
        """Guarda una imagen con las detecciones marcadas"""
        # Crear una copia del board para marcar las detecciones
        detection_img = board.copy()
        
        # Marcar manzanas con círculos rojos
        for (x, y) in apples:
            cv2.circle(detection_img, (x + self.tile_size//2, y + self.tile_size//2), 
                      self.tile_size//2, (0, 0, 255), 2)  # Rojo
            cv2.putText(detection_img, "APPLE", (x, y-5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
        
        # Marcar ojos con círculos azules
        for (x, y) in eyes:
            cv2.circle(detection_img, (x + self.tile_size//2, y + self.tile_size//2), 
                      self.tile_size//2, (255, 0, 0), 2)  # Azul
            cv2.putText(detection_img, "EYE", (x, y-5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
        
        # Guardar la imagen
        filename = f"{self.images_dir}/detection_frame_{frame_num:03d}.png"
        cv2.imwrite(filename, detection_img)
        self.logger.info(f"💾 Imagen de detección guardada: {filename}")
        
        return detection_img

    def save_grid_visualization(self, grid, frame_num):
        """Guarda una visualización del grid como imagen"""
        if grid.size == 0:
            return
            
        # Crear imagen del grid (escalada para mejor visualización)
        scale = 20  # Cada celda será 20x20 píxeles
        h, w = grid.shape
        grid_img = np.zeros((h * scale, w * scale, 3), dtype=np.uint8)
        
        # Colorear según el contenido de cada celda
        for y in range(h):
            for x in range(w):
                cell_value = grid[y, x]
                y1, y2 = y * scale, (y + 1) * scale
                x1, x2 = x * scale, (x + 1) * scale
                
                if cell_value == 1:  # Ojo de serpiente
                    grid_img[y1:y2, x1:x2] = (255, 0, 0)  # Azul
                elif cell_value == 2:  # Manzana
                    grid_img[y1:y2, x1:x2] = (0, 0, 255)  # Rojo
                else:  # Vacío
                    grid_img[y1:y2, x1:x2] = (50, 50, 50)  # Gris oscuro
        
        # Agregar líneas de grid
        for i in range(h + 1):
            cv2.line(grid_img, (0, i * scale), (w * scale, i * scale), (100, 100, 100), 1)
        for i in range(w + 1):
            cv2.line(grid_img, (i * scale, 0), (i * scale, h * scale), (100, 100, 100), 1)
        
        # Agregar texto informativo
        cv2.putText(grid_img, f"Frame {frame_num} - Grid {w}x{h}", 
                   (5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        cv2.putText(grid_img, "Blue=Snake Eye, Red=Apple, Gray=Empty", 
                   (5, h * scale - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
        
        # Guardar la imagen
        filename = f"{self.images_dir}/grid_frame_{frame_num:03d}.png"
        cv2.imwrite(filename, grid_img)
        self.logger.info(f"🗺️ Visualización de grid guardada: {filename}")
        
        return grid_img

    def show_final_summary(self, total_frames):
        """Muestra un resumen final de todas las imágenes generadas"""
        self.logger.info("📋 === RESUMEN FINAL ===")
        self.logger.info(f"🎬 Total de frames procesados: {total_frames}")
        self.logger.info(f"📁 Directorio de imágenes: {self.images_dir}")
        
        # Contar archivos generados
        if os.path.exists(self.images_dir):
            detection_files = [f for f in os.listdir(self.images_dir) if f.startswith("detection_frame_")]
            grid_files = [f for f in os.listdir(self.images_dir) if f.startswith("grid_frame_")]
            
            self.logger.info(f"🖼️ Imágenes de detección generadas: {len(detection_files)}")
            self.logger.info(f"🗺️ Visualizaciones de grid generadas: {len(grid_files)}")
            
            if detection_files:
                self.logger.info("📸 Archivos de detección:")
                for f in sorted(detection_files):
                    self.logger.info(f"   - {f}")
            
            if grid_files:
                self.logger.info("🗺️ Archivos de grid:")
                for f in sorted(grid_files):
                    self.logger.info(f"   - {f}")
        
        self.logger.info("✅ Proceso completado. Revisa las imágenes en el directorio para analizar las detecciones.")

    def map_grid(self, board, frame_num=None):
        """Mapea la grilla del tablero detectando manzanas y ojos"""
        grid_h = board.shape[0] // self.tile_size
        grid_w = board.shape[1] // self.tile_size
        grid = np.zeros((grid_h, grid_w), dtype=int)
        
        self.logger.info(f"🗺️ Mapeando grid: {grid_w}x{grid_h} celdas (tile_size={self.tile_size})")

        # Detectar manzanas
        apples = self.match_template(board, self.apple_asset, template_name="manzanas")
        apple_count = 0
        for (x, y) in apples:
            grid_x, grid_y = x // self.tile_size, y // self.tile_size
            if 0 <= grid_x < grid_w and 0 <= grid_y < grid_h:
                grid[grid_y][grid_x] = 2  # 2 = apple
                apple_count += 1
                self.logger.info(f"🍎 Manzana detectada en grid ({grid_x},{grid_y}) - pixel ({x},{y})")

        # Detectar ojos
        eyes = self.match_template(board, self.eye_asset, template_name="ojos")
        eye_count = 0
        for (x, y) in eyes:
            grid_x, grid_y = x // self.tile_size, y // self.tile_size
            if 0 <= grid_x < grid_w and 0 <= grid_y < grid_h:
                grid[grid_y][grid_x] = 1  # 1 = snake eye
                eye_count += 1
                self.logger.info(f"👁️ Ojo detectado en grid ({grid_x},{grid_y}) - pixel ({x},{y})")

        self.logger.info(f"📊 Resumen detección: {apple_count} manzanas, {eye_count} ojos")
        self.logger.info(f"🎮 Grid final:\n{grid}")
        
        # Guardar imágenes si se proporciona frame_num
        if frame_num is not None:
            self.save_detection_image(board, apples, eyes, frame_num)
            self.save_grid_visualization(grid, frame_num)
        
        return grid


if __name__ == "__main__":
    scanner = GameScanner("content/apple.png", "content/two_eyes.png", tile_size=15)
    
    scanner.logger.info("🚀 Iniciando bucle principal de detección")
    frame_count = 0

    try:
        while True:
            frame_count += 1
            scanner.logger.info(f"🔄 === FRAME {frame_count} ===")
            
            board = scanner.capture_board()
            grid = scanner.map_grid(board, frame_count)

            print(f"\n--- Frame {frame_count} ---")
            print(grid)  # Para debug en consola

            # Mostrar la detección en ventana (opcional)
            cv2.imshow("Board", board)
            if cv2.waitKey(100) & 0xFF == ord("q"):
                scanner.logger.info("🛑 Usuario presionó 'q' para salir")
                break
                
    except KeyboardInterrupt:
        scanner.logger.info("🛑 Interrupción por teclado (Ctrl+C)")
    except Exception as e:
        scanner.logger.error(f"❌ Error inesperado: {e}")
    finally:
        scanner.logger.info(f"🏁 Finalizando después de {frame_count} frames")
        scanner.show_final_summary(frame_count)
        cv2.destroyAllWindows()
