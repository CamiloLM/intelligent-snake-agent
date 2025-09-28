from collections import deque
from random import choice, randrange

from base.direc import Direc
from base.map import Map
from base.point import PointType
from base.pos import Pos


class Snake:
    def __init__(self, game_map, init_direc=None, init_bodies=None, init_types=None):
        """Inicializa el objeto Snake.
        Args:
            game_map (Map): El objeto Map donde se encuentra la serpiente.
            init_direc (str): La dirección inicial de la serpiente ('UP', 'DOWN', 'LEFT', 'RIGHT').
            init_bodies (list): Una lista de tuplas con las posiciones iniciales del cuerpo de la serpiente.
            init_types (list): Una lista de tipos que representan las posiciones del cuerpo de la serpiente.
        """
        self._map = game_map
        self._init_direc = init_direc
        self._init_bodies = init_bodies
        self._init_types = init_types
        self.reset(False)

    def reset(self, reset_map=True):
        """Reinicia la serpiente a su estado inicial en el juego. Si no se ha proporcionado la dirección inicial,
        posicion del cuerpo o tipos de la serpiente, estos se asignarán de manera aleatoria, con el tamaño de la
        serpiente de 2 segmentos.
        Por defecto, también se reinicia el estado del mapa. Puede modificar el parámetro reset_map para evitarlo."""

        # Si no se proporcionan los valores iniciales, se asignan aleatoriamente
        randInit = False  # Indica si la función se inicio sin valores
        if self._init_bodies is None or self._init_types is None:
            randInit = True
            head = Pos(
                [randrange(1, self._map.columns - 2), randrange(1, self._map.rows - 2)]
            )

            if self._init_direc is None:
                self._init_direc = choice(
                    [Direc.UP, Direc.DOWN, Direc.LEFT, Direc.RIGHT]
                )

            self._init_bodies = [head, head.adj(Direc.opposite(self._init_direc))]

            self._init_types = []
            if self._init_direc == Direc.LEFT:
                self._init_types.append(PointType.HEAD_L)
            elif self._init_direc == Direc.UP:
                self._init_types.append(PointType.HEAD_U)
            elif self._init_direc == Direc.RIGHT:
                self._init_types.append(PointType.HEAD_R)
            elif self._init_direc == Direc.DOWN:
                self._init_types.append(PointType.HEAD_D)
            if self._init_direc == Direc.LEFT or self._init_direc == Direc.RIGHT:
                self._init_types.append(PointType.BODY_HOR)
            elif self._init_direc == Direc.UP or self._init_direc == Direc.DOWN:
                self._init_types.append(PointType.BODY_VER)

        # Asignación de los valores iniciales
        self._dead = False
        self._direc = self._init_direc
        self._direc_next = Direc.NONE
        self._bodies = deque(self._init_bodies)
        if reset_map:
            self._map.reset()
        for i, pos in enumerate(self._init_bodies):
            self._map.point(pos).type = self._init_types[i]

        # Si la función se inició sin valores, se limpian los valores iniciales para la próxima vez
        if randInit:
            self._init_direc = None
            self._init_bodies = None
            self._init_types = None

    def copy(self):
        """Crea una copia de la serpiente y del mapa."""
        m_copy = self.game_map.copy()
        s_copy = Snake(m_copy, Direc.NONE, [], [])
        s_copy._dead = self._dead
        s_copy._direc = self._direc
        s_copy._direc_next = self._direc_next
        s_copy._bodies = deque(self._bodies)
        return s_copy, m_copy

    @property
    def map(self):
        return self._map

    @property
    def dead(self):
        return self._dead

    @dead.setter
    def dead(self, value):
        if not isinstance(value, bool):
            raise ValueError("El valor de dead debe ser un booleano")
        self._dead = value

    @property
    def direc(self):
        return self._direc

    @property
    def direc_next(self):
        return self._direc_next

    @direc_next.setter
    def direc_next(self, value):
        if not isinstance(value, Direc):
            raise ValueError("La dirección debe ser una instancia de Direc")
        self._direc_next = value

    @property
    def bodies(self):
        return list(self._bodies)

    def len(self):
        return len(self._bodies)

    def head(self):
        if not self._bodies:
            return None
        return self._bodies[0]

    def tail(self):
        if not self._bodies:
            return None
        return self._bodies[-1]

    def _new_types(self):
        """Decide que tipo de celda debe tener la cabeza y el cierpo de la serpiente al moverse."""
        old_head_type, new_head_type = None, None

        # new_head_type
        if self._direc_next == Direc.LEFT:
            new_head_type = PointType.HEAD_L
        elif self._direc_next == Direc.UP:
            new_head_type = PointType.HEAD_U
        elif self._direc_next == Direc.RIGHT:
            new_head_type = PointType.HEAD_R
        elif self._direc_next == Direc.DOWN:
            new_head_type = PointType.HEAD_D

        # old_head_type
        if (self._direc == Direc.LEFT and self._direc_next == Direc.LEFT) or (
            self._direc == Direc.RIGHT and self._direc_next == Direc.RIGHT
        ):
            old_head_type = PointType.BODY_HOR
        elif (self._direc == Direc.UP and self._direc_next == Direc.UP) or (
            self._direc == Direc.DOWN and self._direc_next == Direc.DOWN
        ):
            old_head_type = PointType.BODY_VER
        elif (self._direc == Direc.RIGHT and self._direc_next == Direc.UP) or (
            self._direc == Direc.DOWN and self._direc_next == Direc.LEFT
        ):
            old_head_type = PointType.BODY_LU
        elif (self._direc == Direc.LEFT and self._direc_next == Direc.UP) or (
            self._direc == Direc.DOWN and self._direc_next == Direc.RIGHT
        ):
            old_head_type = PointType.BODY_UR
        elif (self._direc == Direc.LEFT and self._direc_next == Direc.DOWN) or (
            self._direc == Direc.UP and self._direc_next == Direc.RIGHT
        ):
            old_head_type = PointType.BODY_RD
        elif (self._direc == Direc.RIGHT and self._direc_next == Direc.DOWN) or (
            self._direc == Direc.UP and self._direc_next == Direc.LEFT
        ):
            old_head_type = PointType.BODY_DL
        return old_head_type, new_head_type

    def _rm_tail(self):
        self._map.point(self.tail()).type = PointType.EMPTY
        self._bodies.pop()

    def move(self, new_direc=None):
        if new_direc is not None:
            self._direc_next = new_direc

        if (
            self._dead
            or self._direc_next == Direc.NONE
            or self._direc_next == Direc.opposite(self._direc)
        ):
            return

        old_head_type, new_head_type = self._new_types()
        self._map.point(self.head()).type = old_head_type
        new_head = self.head().adj(self._direc_next)
        self._bodies.appendleft(new_head)

        if not self._map.is_safe(new_head):
            self._dead = True
        if self._map.point(new_head).type == PointType.FOOD:
            self._map.rm_food()
        else:
            self._rm_tail()

    def move_path(self, path):
        for p in path:
            self.move(p)


if __name__ == "__main__":
    game_map = Map(15, 15)
    init_bodies = [Pos(7, 4), Pos(7, 3), Pos(7, 2), Pos(7, 1)]
    init_types = [PointType.HEAD_D]
    for i in range(1, len(init_bodies)):
        init_types.append(PointType.BODY_HOR)
    init_direc = Direc.RIGHT  # La dirección inicial no puede ser NONE

    snake = Snake(game_map, init_direc, init_bodies, init_types)
    snake.move(Direc.DOWN)

