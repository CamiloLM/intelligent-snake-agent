import cv2
import numpy as np
import pyautogui

class GameScanner:
    def __init__(self, apple_asset, eye_asset, tile_size=25):
        # Cargar assets
        self.apple_asset = cv2.imread(apple_asset, cv2.IMREAD_UNCHANGED)
        self.eye_asset = cv2.imread(eye_asset, cv2.IMREAD_UNCHANGED)

        # Convertir a BGR si tienen canal alfa
        if self.apple_asset is not None and self.apple_asset.shape[2] == 4:
            self.apple_asset = cv2.cvtColor(self.apple_asset, cv2.COLOR_BGRA2BGR)
        if self.eye_asset is not None and self.eye_asset.shape[2] == 4:
            self.eye_asset = cv2.cvtColor(self.eye_asset, cv2.COLOR_BGRA2BGR)

        # 🔥 Escalar al tamaño de la celda
        self.apple_asset = cv2.resize(self.apple_asset, (tile_size, tile_size), interpolation=cv2.INTER_AREA)
        self.eye_asset = cv2.resize(self.eye_asset, (tile_size, tile_size), interpolation=cv2.INTER_AREA)

        self.tile_size = tile_size

    def capture_board(self):
        """Captura la pantalla y recorta automáticamente el tablero usando bordes"""
        screenshot = pyautogui.screenshot()
        frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # Convertir a gris y buscar bordes
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return frame

        # Buscar el contorno más grande (probable tablero)
        board_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(board_contour)
        board = frame[y:y+h, x:x+w]
        return board

    def match_template(self, board, template, threshold=0.8):
        """Busca coincidencias del template en la imagen"""
        if template is None or board is None:
            return []

        # ⚠️ Validación de tamaño
        if board.shape[0] < template.shape[0] or board.shape[1] < template.shape[1]:
            return []

        result = cv2.matchTemplate(board, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(result >= threshold)
        matches = list(zip(*loc[::-1]))  # (x, y) de cada match
        return matches

    def map_grid(self, board):
        """Mapea la grilla del tablero detectando manzanas y ojos"""
        grid_h = board.shape[0] // self.tile_size
        grid_w = board.shape[1] // self.tile_size
        grid = np.zeros((grid_h, grid_w), dtype=int)

        # Detectar manzanas
        apples = self.match_template(board, self.apple_asset)
        for (x, y) in apples:
            grid[y // self.tile_size][x // self.tile_size] = 2  # 2 = apple

        # Detectar ojos
        eyes = self.match_template(board, self.eye_asset)
        for (x, y) in eyes:
            grid[y // self.tile_size][x // self.tile_size] = 1  # 1 = snake eye

        return grid


if __name__ == "__main__":
    scanner = GameScanner("content/apple.png", "content/snake_eyes.png", tile_size=25)

    while True:
        board = scanner.capture_board()
        grid = scanner.map_grid(board)

        print(grid)  # Para debug

        # Mostrar la detección en ventana (opcional)
        cv2.imshow("Board", board)
        if cv2.waitKey(100) & 0xFF == ord("q"):
            break

    cv2.destroyAllWindows()
