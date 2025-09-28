from random import randrange, choice
from collections import deque

from base.direc import Direc
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
        posicion del cuerpo o tipos de la serpiente, estos se asignarán de manera aleatoria.
        Por defecto, también se reinicia el estado del mapa. Puede modificar el parámetro reset_map para evitarlo."""

        # Si no se proporcionan los valores iniciales, se asignan aleatoriamente
        randInit = False  # Indica si la función se inicio sin valores
        rand_init = False
        if self._init_direc is None:  # Randomly initialize
            rand_init = True
            head_row = randrange(2, self._map.num_rows - 2)
            head_col = randrange(2, self._map.num_cols - 2)
            head = Pos(head_row, head_col)

            self._init_direc = choice(
                [Direc.LEFT, Direc.UP, Direc.RIGHT, Direc.DOWN]
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
        if rand_init:
            self._init_direc = self._init_bodies = self._init_types = None


    def copy(self):
        m_copy = self._map.copy()
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
    def dead(self, val):
        self._dead = val

    @property
    def direc(self):
        return self._direc

    @property
    def direc_next(self):
        return self._direc_next

    @direc_next.setter
    def direc_next(self, val):
        self._direc_next = val

    @property
    def bodies(self):
        return self._bodies

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

    def move_path(self, path):
        for p in path:
            self.move(p)

    def move(self, new_direc=None):
        if new_direc is not None:
            self._direc_next = new_direc

        if (
            self._dead
            or self._direc_next == Direc.NONE
            or self._map.is_full()
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

        self._map.point(new_head).type = new_head_type
        self._direc = self._direc_next

    def _rm_tail(self):
        self._map.point(self.tail()).type = PointType.EMPTY
        self._bodies.pop()

    def _new_types(self):
        """Decide que tipo de celda debe tener cabeza y el resto cuerpo cuando la serpiente se mueve."""
        old_head_type, new_head_type = None, None
        
        # Posiciones de la cabeza despues del movimiento
        if self._direc_next == Direc.LEFT:
            new_head_type = PointType.HEAD_L
        elif self._direc_next == Direc.UP:
            new_head_type = PointType.HEAD_U
        elif self._direc_next == Direc.RIGHT:
            new_head_type = PointType.HEAD_R
        elif self._direc_next == Direc.DOWN:
            new_head_type = PointType.HEAD_D
        
        # Poscion del cuerpo que era cabeza antes del movimiento
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