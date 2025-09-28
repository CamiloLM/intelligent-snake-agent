import random

from base.point import Point, PointType
from base.pos import Pos


class Map:
    """Mapa 2D del juego que almacena el tipo de cada punto. Las posiciones se consultan con la clase Pos.
    La poscion en x corresponde a las filas y la posicion en y a las columnas.
    """

    def __init__(self, num_rows, num_cols):
        """Initialize a Map object."""
        if not isinstance(num_rows, int) or not isinstance(num_cols, int):
            raise TypeError("'num_rows' and 'num_cols' must be integers")
        if num_rows < 5 or num_cols < 5:
            raise ValueError("'num_rows' and 'num_cols' must >= 5")

        self._num_rows = num_rows
        self._num_cols = num_cols
        self._capacity = (num_rows - 2) * (num_cols - 2)
        self._content = [[Point() for _ in range(num_cols)] for _ in range(num_rows)]
        self.reset()

    def reset(self):
        """Reinicia el mapa a su estado inicial."""
        self._food = None
        for i in range(self._num_rows):
            for j in range(self._num_cols):
                if (
                    i == 0
                    or i == self._num_rows - 1
                    or j == 0
                    or j == self._num_cols - 1
                ):
                    self._content[i][j].type = PointType.WALL
                else:
                    self._content[i][j].type = PointType.EMPTY

    def copy(self):
        """Crea una copia del mapa."""
        m_copy = Map(self._num_rows, self._num_cols)
        for i in range(self._num_rows):
            for j in range(self._num_cols):
                m_copy._content[i][j].type = self._content[i][j].type
        return m_copy

    @property
    def num_rows(self):
        return self._num_rows

    @property
    def num_cols(self):
        return self._num_cols

    @property
    def capacity(self):
        return self._capacity

    @property
    def food(self):
        return self._food

    def point(self, pos):
        """Devuelve un punto del mapa en la posición dada.
        Pos tiene que ser una instancia de la clase Pos."""
        return self._content[pos.x][pos.y]

    def is_inside(self, pos):
        """Verifica si una posición está dentro de los límites del mapa."""
        return (
            pos.x > 0
            and pos.x < self.num_rows - 1
            and pos.y > 0
            and pos.y < self.num_cols - 1
        )

    def is_empty(self, pos):
        """Verifica si una posición es vacía."""
        return self.is_inside(pos) and self.point(pos).type == PointType.EMPTY

    def is_safe(self, pos):
        """Verifica si una posición es segura para la serpiente."""
        return self.is_inside(pos) and (
            self.point(pos).type == PointType.EMPTY
            or self.point(pos).type == PointType.FOOD
        )

    def is_full(self):
        """Verifica si el mapa está lleno del cuerpo de la serpiente."""
        for i in range(1, self.num_rows - 1):
            for j in range(1, self.num_cols - 1):
                t = self._content[i][j].type
                if t.value < PointType.HEAD_L.value:
                    return False
        return True

    def has_food(self):
        return self._food is not None

    def rm_food(self):
        """Elimina la comida del mapa."""
        if self.has_food():
            self.point(self._food).type = PointType.EMPTY
            self._food = None

    def create_food(self, pos):
        """Agrega comida en la posición dada."""
        self.point(pos).type = PointType.FOOD
        self._food = pos
        return self._food

    def create_rand_food(self):
        empty_pos = []
        for i in range(1, self._num_rows - 1):
            for j in range(1, self._num_cols - 1):
                t = self._content[i][j].type
                if t == PointType.EMPTY:
                    empty_pos.append(Pos(i, j))
                elif t == PointType.FOOD:
                    return None  # Stop if food exists
        if empty_pos:
            return self.create_food(random.choice(empty_pos))
        return None