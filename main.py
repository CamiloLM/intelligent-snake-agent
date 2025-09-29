import time
from base import Snake, Pos, Direc, PointType, Map
from solver import GreedySolver
from actuator import Actuator
from scanner import Scanner
import pyautogui

class Agent:
    """Agente Inteligente que juega Snake de Google automáticamente."""
    def __init__(self):
        """
        scanner: instancia de Scanner para leer el estado del juego.
        actuator: instancia de Actuator para enviar teclas.
        map: instancia de Map que representa el tablero.
        snake: instancia de Snake que representa la serpiente de forma local.
        solver: instancia del algorimo para decidir la próxima acción.
        """
        self.scanner = Scanner()
        self.actuator = Actuator()
        self.map = Map(17, 19)
        self.last_direc = Direc.RIGHT
        self.solver = GreedySolver(self.snake)
        self.map.create_food(Pos(7, 13))

        init_body = [Pos(8, 7), Pos(8, 6), Pos(8, 5)]
        init_types = [PointType.HEAD_R, PointType.BODY_HOR, PointType.BODY_HOR]
        self.snake = Snake(self.map, Direc.RIGHT, init_body, init_types)

    def run(self):
        """Bucle principal"""
        while True:
            # 1. Leer estado desde pantalla
            snake_body, food_position = self.scanner.capture()

            # 2. Actualizar snake local
            self._update_snake(snake_body, food_position)

            # 3. Calcular dirección
            direc = self.solver.next_direc()
            # self.snake.move(direc)  # Opcional: mover la serpiente localmente

            # 4. Mandar acción
            self.actuator.send(direc)
            self.last_direc = direc

            # 5. Pausa opcional
            time.sleep(0.2)


    def _update_snake(self, snake_body, food_position):
        """
        Actualiza el Snake local con los datos del Scanner.
        snake_body: deque de Pos (cabeza primero).
        food_position: Pos
        """
        # --- Cabeza ---
        head = Pos(snake_body[0])
        direc = self._head_type_from_direc(self.last_direc)
        new_bodies = [head]
        new_types = [direc]
        
        # --- Cuerpo ---
        for i in range(1, len(snake_body)):
            new_bodies.append(Pos(snake_body[i]))

        for i in range(1, len(snake_body) - 1):
            prev = snake_body[i - 1]  # segmento anterior
            curr = snake_body[i]
            nxt = snake_body[i + 1]  # segmento siguiente
            new_types.append(self._body_type(prev, curr, nxt))

        # --- Cola ---
        if len(snake_body) > 1:
            tail = snake_body[-1]
            before_tail = snake_body[-2]
            if before_tail.row == tail.row:
                t_type = PointType.BODY_HOR
            else:
                t_type = PointType.BODY_VER
            new_types[-1] = t_type
        
        # --- Crear la serpiente ---
        game_map = self.map
        if direc != Direc.NONE and len(snake_body) > 1 and len(new_bodies) == len(new_types):
            self.snake = Snake(game_map, direc, new_bodies, new_types)
        else:
            self.snake = Snake(game_map)

        # --- Comida ---
        food = Pos(food_position)
        if food is not None:
            if game_map.has_food():
                game_map.remove_food()
                if game_map.isempty(food):
                    game_map.create_food(food_position)
                else:
                    raise ValueError("La posición de la comida no es vacía.")
                    

    def _head_type_frm_direc(self, direc):
        """Devuelve el PointType correcto para la cabeza según la última dirección."""
        if direc == Direc.LEFT:
            return PointType.HEAD_L
        elif direc == Direc.UP:
            return PointType.HEAD_U
        elif direc == Direc.RIGHT:
            return PointType.HEAD_R
        elif direc == Direc.DOWN:
            return PointType.HEAD_D
        return PointType.HEAD_R  # por defecto

    def _body_type(self, prev: Pos, curr: Pos, nxt: Pos):
        """Decide el tipo de segmento del cuerpo según posiciones adyacentes."""
        # Movimiento desde prev -> curr -> nxt
        dr1, dc1 = curr.row - prev.row, curr.col - prev.col
        dr2, dc2 = nxt.row - curr.row, nxt.col - curr.col

        # recto
        if dr1 == dr2:  # mismo desplazamiento vertical
            return PointType.BODY_VER
        if dc1 == dc2:  # mismo desplazamiento horizontal
            return PointType.BODY_HOR

        # esquinas
        if (dr1, dc1) == (0, 1) and (dr2, dc2) == (1, 0):  # → luego ↓
            return PointType.BODY_RD
        if (dr1, dc1) == (0, -1) and (dr2, dc2) == (-1, 0):  # ← luego ↑
            return PointType.BODY_LU
        if (dr1, dc1) == (0, 1) and (dr2, dc2) == (-1, 0):  # → luego ↑
            return PointType.BODY_UR
        if (dr1, dc1) == (0, -1) and (dr2, dc2) == (1, 0):  # ← luego ↓
            return PointType.BODY_DL
        if (dr1, dc1) == (1, 0) and (dr2, dc2) == (0, 1):  # ↓ luego →
            return PointType.BODY_RD
        if (dr1, dc1) == (-1, 0) and (dr2, dc2) == (0, -1):  # ↑ luego ←
            return PointType.BODY_LU
        if (dr1, dc1) == (-1, 0) and (dr2, dc2) == (0, 1):  # ↑ luego →
            return PointType.BODY_UR
        if (dr1, dc1) == (1, 0) and (dr2, dc2) == (0, -1):  # ↓ luego ←
            return PointType.BODY_DL

        return PointType.BODY_VER  # fallback

if __name__ == "__main__":
    agent = Agent()
    pyautogui.hotkey("alt", "tab")
    time.sleep(0.3)
    agent.run()