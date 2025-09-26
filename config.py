# Variables de configuración global para el juego de la serpiente
WIDTH, HEIGHT = 600, 400

# Número de filas y columnas deseado
COLS = 17
ROWS = 15

# Recalcular el tamaño de la celda para que la cuadrícula se ajuste a la ventana
CELL_SIZE = WIDTH // COLS
if CELL_SIZE > HEIGHT // ROWS:
    CELL_SIZE = HEIGHT // ROWS

# Direcciones
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
