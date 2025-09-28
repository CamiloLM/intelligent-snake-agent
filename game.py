"""
Versión simple en Pygame del juego Snake que integra con la arquitectura existente.
- Usa clases desde snake.base (Map, Snake, Pos, PointType, Direc).
- Solver que solo se mueve a la derecha.
- Dibuja mapa (patrón de verdes), muros (negro), cabeza (blanco), cuerpo (azul),
  manzana (rojo). Muestra puntaje (manzanas comidas). Muestra Game Over con R/ESC.
"""

import sys

import pygame
from pygame.locals import K_ESCAPE, KEYDOWN, QUIT, K_r

# Ajustes (cambia si quieres otro tamaño)
MAP_ROWS = 8  # interior rows (igual al default en GameConf)
MAP_COLS = 8
CELL_PIX = 40  # tamaño pixel por celda (cuadrada)
FPS = 10

# Colores (según petición)
COLOR_BODY_BLUE = (0, 102, 204)  # azul para el cuerpo
COLOR_HEAD_WHITE = (255, 255, 255)  # blanco para la cabeza
COLOR_APPLE_RED = (200, 0, 0)  # rojo para la manzana
COLOR_WALL_BLACK = (0, 0, 0)  # negro para los muros
COLOR_GREEN_LIGHT = (198, 239, 206)  # verde claro
COLOR_GREEN_DARK = (183, 225, 193)  # verde oscuro
COLOR_TEXT = (250, 250, 250)

# --- Integración con tu base ---
# Asume que tienes snake.base.* importable como en el repo original.
from base import Direc, Map, PointType, Pos, Snake


class RightSolver:
    """Solver trivial que siempre devuelve la dirección RIGHT."""

    def __init__(self, snake):
        self.snake = snake

    def next_direc(self):
        return Direc.RIGHT

    def close(self):
        pass

    def plot(self):
        pass


def draw_board(screen, game_map, cell_w, cell_h):
    """Dibuja el terreno (patrón de verdes) y los muros/food según map."""
    # Dibujo del patrón del terreno alternando verdes (solo interior)
    rows = game_map.num_rows - 2
    cols = game_map.num_cols - 2
    for r in range(rows):
        for c in range(cols):
            x = c * cell_w
            y = r * cell_h
            # patrón tipo tablero: alternado
            use_light = (r + c) % 2 == 0
            color = COLOR_GREEN_LIGHT if use_light else COLOR_GREEN_DARK
            pygame.draw.rect(screen, color, (x, y, cell_w, cell_h))

    # Ahora dibujar cada celda según el PointType (considerando offsets)
    for i in range(game_map.num_rows):
        for j in range(game_map.num_cols):
            pos = Pos(i, j)
            try:
                t = game_map.point(pos).type
            except Exception:
                # si map.point falla con ciertas celdas (por seguridad), saltar
                continue

            # convertimos i,j (map incluye paredes). Queremos dibujar solo interior
            # interior draw offset: subtract 1 from i/j to map into screen coordinates
            screen_i = i - 1
            screen_j = j - 1
            if screen_i < 0 or screen_j < 0 or screen_i >= rows or screen_j >= cols:
                # esto incluye muros (borders) -> dibujar muros en todo borde
                # Dibujamos muros en su posición de borde (alineado fuera del terreno)
                # Pero para simplicidad, solo dibujamos muros que coincidan con borde visible:
                if t == PointType.WALL:
                    # calcular la posición aproximada de la pared: si i == 0 -> arriba, i == num_rows-1 -> abajo
                    # limitamos dentro de la ventana (bordes aparecen como filas/cols externas)
                    # ignoramos muros que no caen dentro de la ventana interior
                    # (esto evita dibujar fuera del área cuando map tiene paredes externas)
                    if 0 <= screen_j < cols and 0 <= screen_i < rows:
                        pygame.draw.rect(
                            screen,
                            COLOR_WALL_BLACK,
                            (screen_j * cell_w, screen_i * cell_h, cell_w, cell_h),
                        )
                continue

            x = screen_j * cell_w
            y = screen_i * cell_h

            if t == PointType.WALL:
                pygame.draw.rect(screen, COLOR_WALL_BLACK, (x, y, cell_w, cell_h))
            elif t == PointType.FOOD:
                # manzana centrada con pequeño padding
                pad = int(min(cell_w, cell_h) * 0.15)
                pygame.draw.rect(
                    screen,
                    COLOR_APPLE_RED,
                    (x + pad, y + pad, cell_w - 2 * pad, cell_h - 2 * pad),
                )


def draw_snake(screen, snake, cell_w, cell_h):
    """Dibuja la serpiente usando el PointType para saber cabeza/cuerpo positions."""
    # Usamos snake bodies (si la clase snake expone una forma fácil, usarla).
    # Como no queremos depender de la representación interna, recorremos el mapa y
    # comprobamos dónde está la cabeza/cuerpo por tipo, como en gui.py.
    # Necesitamos acceso al map para obtener los PointType; asumiremos snake tiene referencia al map.
    game_map = (
        snake._map
    )  # depende de tu implementación; en game.py Snake fue creado con map y guardado.
    rows = game_map.num_rows - 2
    cols = game_map.num_cols - 2

    for i in range(game_map.num_rows):
        for j in range(game_map.num_cols):
            pos = Pos(i, j)
            try:
                t = game_map.point(pos).type
            except Exception:
                continue

            screen_i = i - 1
            screen_j = j - 1
            if not (0 <= screen_i < rows and 0 <= screen_j < cols):
                continue
            x = screen_j * cell_w
            y = screen_i * cell_h

            # dibujamos cabeza y cuerpo según tipos de PointType (similar a gui.py)
            if (
                t == PointType.HEAD_L
                or t == PointType.HEAD_U
                or t == PointType.HEAD_R
                or t == PointType.HEAD_D
            ):
                # cabeza blanca (llenando parcialmente como en GUI)
                pad = int(min(cell_w, cell_h) * 0.08)
                pygame.draw.rect(
                    screen,
                    COLOR_HEAD_WHITE,
                    (x + pad, y + pad, cell_w - 2 * pad, cell_h - 2 * pad),
                )
            elif t != PointType.EMPTY and t != PointType.FOOD and t != PointType.WALL:
                # cualquier otro tipo de cuerpo -> azul
                pad = int(min(cell_w, cell_h) * 0.10)
                pygame.draw.rect(
                    screen,
                    COLOR_BODY_BLUE,
                    (x + pad, y + pad, cell_w - 2 * pad, cell_h - 2 * pad),
                )


def main():
    pygame.init()
    rows = MAP_ROWS
    cols = MAP_COLS
    # Construimos Map con bordes como en tu repo (sumamos 2)
    game_map = Map(rows + 2, cols + 2)

    # Inicial bodies default (si tu Snake permite otros init, ajusta)
    # Intentamos usar el mismo init que GameConf por defecto: Pos(1,4), etc.
    # Para prevenir errores si las dimensiones cambian, calculamos un init simple:
    init_bodies = []
    start_r = 1
    start_c = 1
    # crear serpiente horizontal de longitud 3
    init_bodies = [Pos(start_r, start_c + i) for i in range(0, 3)][::-1]
    init_types = [PointType.HEAD_R] + [PointType.BODY_HOR] * 3

    # create a snake
    snake = Snake(game_map, Direc.RIGHT, init_bodies, init_types)

    solver = RightSolver(snake)

    # prepare window
    cell_w = CELL_PIX
    cell_h = CELL_PIX
    screen_w = cols * cell_w
    screen_h = rows * cell_h

    screen = pygame.display.set_mode((screen_w, screen_h))
    pygame.display.set_caption("Snake - Pygame (solver: always RIGHT)")

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 20)

    # score tracking: contamos manzanas comidas por diferencia de longitud
    prev_len = snake.len()
    score = 0

    running = True
    paused = False
    game_over = False

    # Asegurar que haya comida
    if not game_map.has_food():
        game_map.create_rand_food()

    while running:
        for ev in pygame.event.get():
            if ev.type == QUIT:
                running = False
            elif ev.type == KEYDOWN:
                if ev.key == K_ESCAPE:
                    running = False
                elif ev.key == K_r and game_over:
                    # reiniciar: intentamos replicar Game._reset (call snake.reset())
                    try:
                        snake.reset()
                    except Exception:
                        # si reset no está implementado como esperamos, recreamos instancia
                        snake = Snake(game_map, Direc.RIGHT, init_bodies, None)
                    score = 0
                    prev_len = snake.len()
                    game_over = False
                    paused = False

        if not paused and not game_over:
            # aseguramos comida
            if not game_map.has_food():
                game_map.create_rand_food()

            # solver decide (siempre RIGHT)
            try:
                new_d = solver.next_direc()
                snake.direc_next = new_d
            except Exception:
                # fallback: intentar asignar Direc.RIGHT en la API antigua
                try:
                    snake.direc_next = Direc.RIGHT
                except Exception:
                    pass

            # mover serpiente
            try:
                snake.move()
            except Exception:
                # si move lanza, considerar muerto
                pass

            # actualizar puntaje si creció
            cur_len = snake.len()
            if cur_len > prev_len:
                score += cur_len - prev_len
                prev_len = cur_len

            # condiciones de fin
            if snake.dead or game_map.is_full():
                game_over = True

        # dibujado
        draw_board(screen, game_map, cell_w, cell_h)
        draw_snake(screen, snake, cell_w, cell_h)

        # marcador
        score_surf = font.render(f"Puntaje: {score}", True, COLOR_TEXT)
        screen.blit(score_surf, (8, 8))

        # Game Over overlay
        if game_over:
            overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))  # semitransparente
            screen.blit(overlay, (0, 0))
            go_text = [
                "GAME OVER",
                "Presiona R para reiniciar o ESC para salir",
                f"Puntaje final: {score}",
            ]
            large = pygame.font.SysFont("Arial", 48)
            small = pygame.font.SysFont("Arial", 20)
            # centrar textos
            y0 = screen_h // 2 - 60
            surf = large.render(go_text[0], True, (255, 255, 255))
            rect = surf.get_rect(center=(screen_w // 2, y0))
            screen.blit(surf, rect)
            surf2 = small.render(go_text[1], True, (220, 220, 220))
            rect2 = surf2.get_rect(center=(screen_w // 2, y0 + 50))
            screen.blit(surf2, rect2)
            surf3 = small.render(go_text[2], True, (220, 220, 220))
            rect3 = surf3.get_rect(center=(screen_w // 2, y0 + 85))
            screen.blit(surf3, rect3)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
