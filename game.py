import sys
import pygame
from pygame.locals import K_ESCAPE, KEYDOWN, QUIT, K_r, K_p
from base import Direc, Map, PointType, Pos, Snake
from solver import GreedySolver

from config import *


def draw_board(screen, game_map, cell_w, cell_h):
    rows, cols = game_map.num_rows - 2, game_map.num_cols - 2
    for i in range(rows):
        for j in range(cols):
            x, y = j * cell_w, i * cell_h
            color = COLOR_GREEN_DARK if (i + j) % 2 == 0 else COLOR_GREEN_LIGHT
            pygame.draw.rect(screen, color, (x, y, cell_w, cell_h))

    for i in range(1, game_map.num_rows - 1):
        for j in range(1, game_map.num_cols - 1):
            if game_map.point(Pos(i, j)).type.name == "FOOD":
                pad = int(min(cell_w, cell_h) * 0.15)
                x, y = (j - 1) * cell_w, (i - 1) * cell_h
                pygame.draw.rect(screen, COLOR_APPLE_RED, (x + pad, y + pad, cell_w - 2 * pad, cell_h - 2 * pad))


def draw_snake(screen, snake, cell_w, cell_h):
    head = {"HEAD_L", "HEAD_U", "HEAD_R", "HEAD_D"}
    body = {"BODY_LU", "BODY_UR", "BODY_RD", "BODY_DL", "BODY_HOR", "BODY_VER"}
    pad = int(min(cell_w, cell_h) * 0.12)

    for i in range(1, snake.map.num_rows - 1):
        for j in range(1, snake.map.num_cols - 1):
            t = snake.map.point(Pos(i, j)).type.name
            if t in head or t in body:
                x, y = (j - 1) * cell_w, (i - 1) * cell_h
                color = COLOR_HEAD_WHITE if t in head else COLOR_BODY_BLUE
                pygame.draw.rect(screen, color, (x + pad, y + pad, cell_w - 2 * pad, cell_h - 2 * pad))


def main():
    pygame.init()
    game_map = Map(MAP_ROWS + 2, MAP_COLS + 2)

    if MAP_ROWS == 15 and MAP_COLS == 17:

        init_bodies = [Pos(7, 4), Pos(7, 3), Pos(7, 2), Pos(7, 1)]
        init_types = [PointType.HEAD_D] + [PointType.BODY_HOR] * (len(init_bodies)- 1)
        
        init_direc = Direc.RIGHT  # La dirección inicial no puede ser NONE

        snake = Snake(game_map, init_direc, init_bodies, init_types)

        game_map.create_food(Pos(7, 13))
    else:
        game_map = Map(MAP_ROWS + 2, MAP_COLS + 2)
        snake = Snake(game_map)
        game_map.create_rand_food()
    
    solver = GreedySolver(snake)

    cell_w = cell_h = CELL_PIX
    screen = pygame.display.set_mode((MAP_COLS * cell_w, MAP_ROWS * cell_h))
    pygame.display.set_caption("Snake - Pygame")

    clock, font = pygame.time.Clock(), pygame.font.SysFont("Arial", 20)
    prev_len, score, running, paused, game_over = snake.len(), 0, True, False, False

    while running:
        for ev in pygame.event.get():
            if ev.type == QUIT or (ev.type == KEYDOWN and ev.key == K_ESCAPE):
                running = False
            elif ev.type == KEYDOWN and ev.key == K_r:
                snake.reset()
                if MAP_ROWS == 15 and MAP_COLS == 17:
                    snake.map.create_food(Pos(7, 13))
                score, prev_len, game_over, paused = 0, snake.len(), False, False
            elif ev.type == KEYDOWN and ev.key == K_p:
                paused = not paused

        if not paused and not game_over:
            if not game_map.has_food():
                game_map.create_rand_food()
            
            snake.direc_next = solver.next_direc()
            snake.move()
            
            cur_len = snake.len()
            if cur_len > prev_len:
                score += cur_len - prev_len
                prev_len = cur_len
            
            if snake.dead or game_map.is_full():
                game_over = True

        draw_board(screen, game_map, cell_w, cell_h)
        draw_snake(screen, snake, cell_w, cell_h)
        screen.blit(font.render(f"Puntaje: {score}", True, COLOR_TEXT), (8, 8))

        if game_over:
            overlay = pygame.Surface((MAP_COLS * cell_w, MAP_ROWS * cell_h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
            go_text = ["GAME OVER", "Presiona R para reiniciar o ESC para salir", f"Puntaje final: {score}"]
            large, small = pygame.font.SysFont("Arial", 48), pygame.font.SysFont("Arial", 20)
            y0 = (MAP_ROWS * cell_h) // 2 - 60
            screen.blit(large.render(go_text[0], True, (255, 255, 255)), large.render(go_text[0], True, (255, 255, 255)).get_rect(center=((MAP_COLS * cell_w) // 2, y0)))
            screen.blit(small.render(go_text[1], True, (220, 220, 220)), small.render(go_text[1], True, (220, 220, 220)).get_rect(center=((MAP_COLS * cell_w) // 2, y0 + 50)))
            screen.blit(small.render(go_text[2], True, (220, 220, 220)), small.render(go_text[2], True, (220, 220, 220)).get_rect(center=((MAP_COLS * cell_w) // 2, y0 + 85)))

        if paused and not game_over:
            overlay = pygame.Surface((MAP_COLS * cell_w, MAP_ROWS * cell_h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            screen.blit(overlay, (0, 0))
            pause_text = pygame.font.SysFont("Arial", 36).render("PAUSA", True, (255, 255, 255))
            screen.blit(pause_text, pause_text.get_rect(center=(MAP_COLS * cell_w // 2, MAP_ROWS * cell_h // 2)))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
