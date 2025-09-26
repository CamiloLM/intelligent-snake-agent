import random
import sys

import pygame

import config
from agent import AStarAgent, BFSAgent

# Colores (mantener aquí porque son específicos del dibujo en Pygame)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
WHITE = (255, 255, 255)


class Food:
    def __init__(self, snake_body):
        self.position = self.random_position(snake_body)

    def random_position(self, snake_body):
        while True:
            # Usa config.COLS y config.ROWS
            pos = (
                random.randint(0, config.COLS - 1),
                random.randint(0, config.ROWS - 1),
            )
            if pos not in snake_body:
                return pos

    def draw(self, screen):
        x, y = self.position
        # Usa config.CELL_SIZE
        pygame.draw.rect(
            screen,
            RED,
            (
                x * config.CELL_SIZE,
                y * config.CELL_SIZE,
                config.CELL_SIZE,
                config.CELL_SIZE,
            ),
        )


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
        pygame.display.set_caption("Snake con Agente")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 20)

        self.snake = AStarAgent()  # o HamiltonianAgent / AStarAgent

        self.food = Food(self.snake.body)
        self.score = 0
        self.running = True
        self.game_over = False
    
    def show_message(self, text):
        # Mostrar mensaje en el centro de la pantalla
        msg = self.font.render(text, True, (255, 0, 0))  # rojo
        rect = msg.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2))
        self.screen.blit(msg, rect)
        pygame.display.flip()
        pygame.time.wait(2000)  # esperar 2 segundos



    def update(self):
        if not self.game_over:
            perceptions = {
                "head": self.snake.body[0],
                "food": self.food.position,
                "snake": self.snake.body,
            }
            action = self.snake.compute(perceptions)

            if action is None:
                print("Juego detenido: el agente no encontró una acción válida.")
                self.game_over = True
                self.show_message("Juego terminado")
                return


            self.snake.set_direction(action)
            self.snake.move()

            if self.snake.body[0] == self.food.position:
                self.score += 1
                self.food = Food(self.snake.body)
            else:
                self.snake.shrink()

            if self.snake.check_collision():
                print("Game Over! Score:", self.score)
                self.game_over = True  # 👈 solo marcar

    def draw(self):
        self.screen.fill(BLACK)
        # Llama al método draw() de la serpiente
        self.snake.draw(self.screen, GREEN)
        self.food.draw(self.screen)

        text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(text, (10, 10))

        pygame.display.flip()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            self.update()
            self.draw()
            self.clock.tick(10)


if __name__ == "__main__":
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()

    agents = [BFSAgent, AStarAgent]
