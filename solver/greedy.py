from base.pos import Pos
from solver.base import BaseSolver
from solver.path import PathSolver


class GreedySolver(BaseSolver):
    """
    Algoritmo voraz, busca el camino más corto para la comida si es seguro.
    Si el camino no es seguro, la serpiente camina hasta que encuentre un camino seguro.

    La estrategia es:
    1. Calcula el camino más corto P1 desde la cabeza S1 hasta la comida. Si lo encuentra, va al paso 2.
    Si no, va al paso 4.

    2. Se crea una serpiente virtual S2 que simula el movimiento de S1 siguiendo P1.

    3. Calcula el camino más largo P2 desde la cabeza de S2 hasta su cola. Si P2 existe la
    serpiente esta segura y se mueve en la dirección del primer paso de P1. Si no existe P2, va al paso 4.

    4. Calcula el camino más largo P3 desde la cabeza S1 hasta su cola. Si P3 existe, la serpiente camina
    en la dirección del primer paso de P3. Si no existe P3, va al paso 5.

    5. La serpiente entra en modo supervivencia, elige la dirección segura que la aleje más de la comida.
    """
    def __init__(self, snake):
        super().__init__(snake)
        self._path_solver = PathSolver(snake)

    def next_direc(self):
        # Crea la serpiente virtual
        s_copy, m_copy = self.snake.copy()

        # Paso 1
        self._path_solver.snake = self.snake
        path_to_food = self._path_solver.shortest_path_to_food()

        if path_to_food:
            # Paso 2
            s_copy.move_path(path_to_food)
            if m_copy.is_full():
                return path_to_food[0]

            # Paso 3
            self._path_solver.snake = s_copy
            path_to_tail = self._path_solver.longest_path_to_tail()
            if len(path_to_tail) > 1:
                return path_to_food[0]

        # Paso 4
        self._path_solver.snake = self.snake
        path_to_tail = self._path_solver.longest_path_to_tail()
        if len(path_to_tail) > 1:
            return path_to_tail[0]

        # Paso 5
        head = self.snake.head()
        direc, max_dist = self.snake.direc, -1
        for adj in head.all_adj():
            if self.map.is_safe(adj):
                dist = Pos.manhattan_dist(adj, self.map.food)
                if dist > max_dist:
                    max_dist = dist
                    direc = head.direc_to(adj)
        return direc