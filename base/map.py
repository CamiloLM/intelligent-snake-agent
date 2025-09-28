from random import randint

from base.point import Point, PointType
from base.pos import Pos


class Map:
    """Mapa 2D del juego que almacena el tipo de cada punto. Las posiciones se consultan con la clase Pos.
    La poscion en x corresponde a las filas y la posicion en y a las columnas.
    """

    def __init__(self, num_rows, num_cols):
        if not isinstance(num_rows, int) or not isinstance(num_cols, int):
            raise TypeError("'num_rows' y 'num_cols' deben ser enteros")
        if num_rows < 5 or num_cols < 5:
            raise ValueError("'num_rows' y 'num_cols' deben ser >= 5")

        self._num_rows = num_rows
        self._num_cols = num_cols
        self._capacity = (num_rows - 2) * (num_cols - 2)
        self._content = [[Point() for _ in range(num_cols)] for _ in range(num_rows)]
        self.reset()

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

    def point(self, pos: Pos) -> Point:
        """Devuelve un punto del mapa en la posición dada."""
        return self._content[pos.x][pos.y]

    def has_food(self):
        return self._food is not None

    def rm_food(self):
        """Elimina la comida del mapa."""
        if self.has_food():
            self.point(self._food).type = PointType.EMPTY
            self._food = None

    def create_food(self, pos):
        """Agrega comida en la posición dada."""
        if self.is_inside(pos) and self.is_empty(pos):
            self.point(pos).type = PointType.FOOD
            self._food = pos

    def reset(self):
        """Reinicia el mapa a su estado inicial."""
        self._food = None
        for i in range(self._num_rows):
            for j in range(self._num_cols):
                if (
                    i == 0
                    or i == self._num_rows - 1
                    or j == 0
                    or j == self.num_cols - 1
                ):
                    self._content[i][j].type = PointType.WALL
                else:
                    self._content[i][j].type = PointType.EMPTY

    def copy(self):
        """Crea una copia del mapa."""
        new_map = Map(self._rows, self._columns)
        for i in range(self._rows):
            for j in range(self._cols):
                new_map._content[i][j].type = self._content[i][j].type
        return new_map

    def is_inside(self, pos):
        """Verifica si una posición está dentro de los límites del mapa."""
        return (
            pos.x > 0
            and pos.x < self._num_rows - 1
            and pos.y > 0
            and pos.y < self._num_cols - 1
        )

    def is_empty(self, pos):
        """Verifica si una posición es vacía."""
        return self.is_inside(pos) and self.point(pos).type == PointType.EMPTY

    def is_safe(self, pos):
        """Verifica si una posición es segura para la serpiente."""
        return self.is_inside(pos) and (
            self.point(pos).type != PointType.WALL
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

    def create_rand_food(self):
        if self.has_food():
            return
        options = []
        for i in range(1, self._num_rows - 1):
            for j in range(1, self._num_cols - 1):
                t = self._content[i][j].type
                if t == PointType.EMPTY:
                    options.append(Pos(i, j))
        if options:
            return self.create_food(options[randint(0, len(options) - 1)])
        return None
