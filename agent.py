import heapq
from collections import deque

import pygame

import config
from config import COLS, ROWS

PLANNED_PATH = (180, 180, 180)


class Snake:
    """Clase base mínima para la serpiente (posición, movimiento, dibujo)."""

    def __init__(self):
        # comienzo en el centro
        self.body = [(COLS // 2, ROWS // 2)]
        # dirección actual (tupla dx,dy)
        self.direction = config.RIGHT
        # camino planeado (lista de celdas) — usado por agentes para dibujar
        self.planned_path = []

    def move(self):
        head_x, head_y = self.body[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)
        self.body.insert(0, new_head)

    def shrink(self):
        # remover cola (se llama cuando no comió)
        if len(self.body) > 0:
            self.body.pop()

    def set_direction(self, new_dir):
        # new_dir debe ser una tupla (dx,dy)
        self.direction = new_dir

    def check_collision(self):
        head = self.body[0]
        # choque consigo misma
        if head in self.body[1:]:
            return True
        # choque con bordes
        if head[0] < 0 or head[0] >= COLS or head[1] < 0 or head[1] >= ROWS:
            return True
        return False

    def draw(self, screen, color):
        """Dibuja primero el camino planeado en gris y luego la serpiente."""
        # dibujar camino planeado (rectángulos grises)
        for cell in self.planned_path:
            x, y = cell
            pygame.draw.rect(
                screen,
                PLANNED_PATH,
                (
                    x * config.CELL_SIZE,
                    y * config.CELL_SIZE,
                    config.CELL_SIZE,
                    config.CELL_SIZE,
                ),
            )

        # dibujar cuerpo (cabeza blanca, resto color)
        for i, segment in enumerate(self.body):
            segment_color = color if i > 0 else (255, 255, 255)
            x, y = segment
            pygame.draw.rect(
                screen,
                segment_color,
                (
                    x * config.CELL_SIZE,
                    y * config.CELL_SIZE,
                    config.CELL_SIZE,
                    config.CELL_SIZE,
                ),
            )


class AStarAgent(Snake):
    def __init__(self):
        super().__init__()

    def compute(self, perceptions):
        head = perceptions["head"]
        food = perceptions["food"]
        snake_body = set(perceptions["snake"])

        path = self.astar(head, food, snake_body)
        if path:
            # path es lista desde start hasta goal
            # la ruta planeada para dibujar será toda la ruta (excluyendo la cabeza)
            self.planned_path = path[1:]
            if len(path) > 1:
                next_step = path[1]
                dx = next_step[0] - head[0]
                dy = next_step[1] - head[1]
                return (dx, dy)
        # si no encuentra camino, no dibujar (vaciar planned_path) y mantener dirección
        self.planned_path = []
        # TODO: manejar caso sin ruta (devolver None y terminar juego)
        return None
        # return self.direction

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    # vecinos válidos (4-direcciones)
    def neighbors(self, node):
        x, y = node
        for dx, dy in [config.UP, config.DOWN, config.LEFT, config.RIGHT]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS:
                yield (nx, ny)

    def astar(self, start, goal, snake_body):
        """Implementación estándar de A* (Manhattan). Evita las celdas ocupadas por cuerpo de la serpiente."""

        open_heap = []
        # f_score, g_score dictionaries
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, goal)}
        heapq.heappush(open_heap, (f_score[start], start))

        came_from = {}

        closed = set()

        while open_heap:
            _, current = heapq.heappop(open_heap)

            if current == goal:
                # reconstruir camino
                path = [current]
                while path[-1] in came_from:
                    path.append(came_from[path[-1]])
                path.reverse()
                return path

            if current in closed:
                continue
            closed.add(current)

            for nb in self.neighbors(current):
                # si la celda está ocupada por el cuerpo (y no es la meta), ignorar
                if nb in snake_body and nb != goal:
                    continue

                tentative_g = g_score[current] + 1
                if tentative_g < g_score.get(nb, float("inf")):
                    came_from[nb] = current
                    g_score[nb] = tentative_g
                    f = tentative_g + self.heuristic(nb, goal)
                    heapq.heappush(open_heap, (f, nb))

        # sin ruta encontrada
        print("Head:", start)
        print("Food:", goal)
        print("Snake body:", snake_body)
        return None


class BFSAgent(Snake):
    """Agente que usa BFS para llegar a la comida y dibuja el camino en gris."""

    def __init__(self):
        super().__init__()

    def compute(self, perceptions):
        head = perceptions["head"]
        food = perceptions["food"]
        snake_body = set(perceptions["snake"])

        path = self.bfs(head, food, snake_body)

        if path and len(path) > 1:
            # guardar el camino (sin incluir la cabeza) para dibujar
            self.planned_path = path[1:]
            next_step = path[1]
            dx = next_step[0] - head[0]
            dy = next_step[1] - head[1]
            return (dx, dy)

        # si no hay camino: limpiar planned_path y mantener dirección
        self.planned_path = []
        return self.direction

    def bfs(self, start, goal, snake_body):
        queue = deque([[start]])
        visited = set([start])

        while queue:
            path = queue.popleft()
            x, y = path[-1]

            if (x, y) == goal:
                return path

            for dx, dy in [config.UP, config.DOWN, config.LEFT, config.RIGHT]:
                nx, ny = x + dx, y + dy
                next_pos = (nx, ny)

                if (
                    0 <= nx < COLS
                    and 0 <= ny < ROWS
                    and next_pos not in visited
                    and next_pos not in snake_body
                ):
                    new_path = list(path)
                    new_path.append(next_pos)
                    queue.append(new_path)
                    visited.add(next_pos)

        return None


if __name__ == "__main__":
    agent = AStarAgent()

    COLS, ROWS = 17, 15  # tablero 7x7

    # Caso de prueba:
    head = (1, 1)             # cabeza de la serpiente
    food = (5, 5)             # comida
    snake_body = {(3, 3), (3, 4), (3, 5)}  # obstáculos (parte del cuerpo)

    print("Head:", head)
    print("Food:", food)
    print("Snake body:", snake_body)

    path = agent.astar(head, food, snake_body)

    if path:
        print("Ruta encontrada:", path)
    else:
        print("No se encontró ruta")

