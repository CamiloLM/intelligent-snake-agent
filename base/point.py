from enum import Enum, unique


@unique
class PointType(Enum):
    """Tipos de puntos en el juego."""

    EMPTY = 0
    WALL = 1
    FOOD = 2
    HEAD_L = 100
    HEAD_U = 101
    HEAD_R = 102
    HEAD_D = 103
    BODY_LU = 104
    BODY_UR = 105
    BODY_RD = 106
    BODY_DL = 107
    BODY_HOR = 108
    BODY_VER = 109


class Point:
    """Punto en el juego. Se almacena solamente el tipo de punto ya que la posicion la clase pos"""

    def __init__(self):
        self._type = PointType.EMPTY

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, val):
        self._type = val