class BaseSolver:
    """Clase base para los solucionadores de la serpiente."""

    def __init__(self, snake):
        self._snake = snake
        self._map = snake.map

    @property
    def map(self):
        return self._map

    @property
    def snake(self):
        return self._snake

    @snake.setter
    def snake(self, val):
        self._snake = val
        self._map = val.map

    def next_direc(self):
        """Genera la próxima dirección para la serpiente."""
        return NotImplemented
