import time
from typing import List

import pyautogui

# NOTA: Se asume que las clases Actuator, Map, PointType, Pos, Snake
# y la clase GreedySolver existen y están disponibles.
from actuator import Actuator
from base import Map, PointType, Pos, Snake
from scanner import Scanner
from solver.greedy import GreedySolver


class Main:
    """
    Agente principal:
    - Scanner: sensor
    - Snake (instancia local): estado en memoria (se actualiza desde scanner)
    - GreedySolver: decide siguiente Direc
    - Actuator: ejecuta la acción en el ambiente con pyautogui
    """

    def __init__(
        self,
        region: tuple,
        rows: int = 15,
        cols: int = 17,
        cell_size: int = 35,
        fps: int = 120,
        # 'debounce_frames' se ignora al inicializar Scanner, pero se mantiene aquí
        # por si se usa en otras partes del sistema principal.
        debounce_frames: int = 3,
        focus_on_start: bool = True,
    ):
        # 1. Ajuste de Inicialización del Scanner:
        # Se eliminan los argumentos 'rows', 'cols', y 'debounce_frames'
        # que no existen en el __init__ de tu clase Scanner.
        self.scanner = Scanner(
            region=region,
            cell_size=cell_size,
        )

        # crear mapa y snake locales (para que GreedySolver tenga la misma API que en pygame)
        self.map = Map(rows + 2, cols + 2)  # bordes incluido
        self.snake = Snake(self.map)
        # solver espera un objeto Snake (igual que en tu pygame)
        self.solver = GreedySolver(self.snake)
        self.actuator = Actuator()
        self.rows = rows
        self.cols = cols
        self.fps = fps
        self.focus_on_start = focus_on_start

    def _update_snake_from_grid(self, grid: List[List[PointType]]):
        """
        Actualiza self.snake.map con la grilla detectada (grid = rows x cols).
        El mapa interno tiene bordes (1..rows, 1..cols en la representación de Map),
        por eso usamos offset +1 al asignar.
        """
        for i in range(self.rows):
            for j in range(self.cols):
                val = grid[i][j]
                # Modificado para manejar el caso PointType.NONE que devuelve tu clasificar_color
                if val == PointType.NONE:
                    # Asumimos que si no se detecta nada específico, es un espacio vacío.
                    val = PointType.EMPTY

                # Pos toma (row, col) en la API del mapa
                pos = Pos(i + 1, j + 1)
                try:
                    self.map.point(pos).type = val
                except Exception:
                    # si la API de Map es distinta, evitamos romper; en debug mostrar info
                    # (pero no fallamos el bucle)
                    pass

        # Opcional: imprimir la grilla detectada para depuración
        # print(f"\n--- Frame {self.frame} Mapeado ---")
        # self.scanner.print_grid(grid)

    def run(self, max_frames: int = None):
        """
        Bucle principal (agente externo). Guarda screenshots, actualiza estado,
        pide acción al solver y la manda con el actuator.
        - max_frames: opcional para correr solo N frames (útil para pruebas).
        """

        # Se asume que en algún momento se cambió el nombre del método en Scanner,
        # pero para usar tu código original de scanner.py:
        # 2. Ajuste para usar el método real del Scanner:
        # Se usa _clear_screenshots() de tu clase Scanner
        self.scanner._clear_screenshots()
        print("Limpiando directorio de screenshots...")

        # opcional: llevar foco al juego
        if self.focus_on_start:
            print("Cambiando foco a la ventana del juego...")
            pyautogui.hotkey("alt", "tab")
            time.sleep(0.6)

        prev_action = None
        frame = 0

        try:
            while True:
                # limite opcional
                if max_frames is not None and frame >= max_frames:
                    break

                # 1. sensor: capturar tablero
                board = self.scanner.capture_board()

                # 1.a detectar game over por color (celeste)
                if self.scanner.is_game_over(board):
                    print("⚠️ Game Over detectado por Scanner. Terminando.")
                    break

                # 1.b guardar screenshot (se generan muchos archivos, nombramos por frame)
                fname = f"frame_{frame:06d}.png"
                self.scanner.save_screenshot(board, fname)

                # 2. construir grilla y actualizar estado interno
                # 3. REEMPLAZO: Usamos mapear_grid() en lugar de get_stable_grid_from_board()
                grid = self.scanner.mapear_grid(board, rows=self.rows, cols=self.cols)
                self.scanner.print_grid(grid)  # Opcional: imprime la grilla
                self._update_snake_from_grid(grid)

                # 3. decidir acción con el solver (GreedySolver usa self.snake)
                try:
                    action = self.solver.next_direc()
                except Exception:
                    # si la firma es distinta a next_direc, intentar next_action()
                    action = getattr(self.solver, "next_action", lambda: None)()

                print(f"Frame {frame} | Acción: {action}")

                # 4. actuador: solo enviar si cambió (evita spam)
                if action is not None and action != prev_action:
                    self.actuator.send(action)
                    prev_action = action

                # 5. avance temporal
                frame += 1
                self.frame = frame  # Para depuración interna
                time.sleep(1.0 / max(1, self.fps))

        except KeyboardInterrupt:
            print("Interrumpido por usuario.")
        finally:
            print("Run finalizado. Frames procesados:", frame)


if __name__ == "__main__":
    # Ajusta la REGION a la que uses en tu entorno
    # (left, top, width, height)
    # REGION de ejemplo usada en tu archivo scanner.py: (387, 217, 594, 525)
    # **¡Asegúrate de que estas dimensiones coincidan con tu tablero!**
    # Si las filas son 15 y columnas 17 con cell_size=35, el tamaño debe ser:
    # Ancho: 17 * 35 = 595. Alto: 15 * 35 = 525.
    # El ejemplo (387, 217, 594, 525) es casi correcto para (17x15) * 35.
    REGION = (387, 217, 595, 525)  # Asumiendo un ancho de 595 para 17*35

    # Crea el agente y corre.
    # Se usa fps=120, lo cual es muy rápido y puede fallar la detección.
    # Para empezar, prueba un FPS más bajo (e.g., 20).
    FPS_DEFAULT = 20  # Recomendado: 20-30 FPS para estabilidad inicial

    agent = Main(
        region=REGION,
        rows=15,
        cols=17,
        cell_size=35,
        fps=FPS_DEFAULT,
        debounce_frames=3,
    )
    print(f"Iniciando agente a {FPS_DEFAULT} FPS...")
    agent.run(max_frames=None)  # None => correr hasta detectar game-over o Ctrl+C
