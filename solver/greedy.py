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
        print(f"🔍 GreedySolver - Serpiente virtual: {s_copy.head()}")
        
        # Obtener dirección actual para validar movimientos
        current_direc = self.snake.direc
        print(f"🔍 GreedySolver - Dirección actual: {current_direc.name}")
        
        # Paso 1 - Buscar camino válido hacia la comida
        self._path_solver.snake = self.snake
        path_to_food = self._path_solver.shortest_path_to_food()
        
        print(f"🔍 GreedySolver - Camino hacia comida: {path_to_food}")

        if path_to_food:
            # Validar que el primer movimiento sea válido
            first_move = path_to_food[0]
            print(f"🔍 GreedySolver - Primer movimiento hacia comida: {first_move.name}")
            if self._is_valid_move(current_direc, first_move):
                # Verificar que el movimiento no lleve fuera del mapa
                next_pos = self.snake.head().adj(first_move)
                if self.map.is_safe(next_pos):
                    # Paso 2
                    s_copy.move_path(path_to_food)
                    if m_copy.is_full():
                        print(f"🔍 GreedySolver - paso2")
                        return first_move

                    # Paso 3
                    self._path_solver.snake = s_copy
                    path_to_tail = self._path_solver.longest_path_to_tail()
                    print(f"🔍 GreedySolver - Camino hacia cola: {path_to_tail}")
                    if len(path_to_tail) > 1:
                        print(f"🔍 GreedySolver - paso3")
                        return first_move
                else:
                    print(f"🔍 GreedySolver - Movimiento hacia comida lleva fuera del mapa: {first_move.name}")
            else:
                print(f"🔍 GreedySolver - Movimiento hacia comida inválido: {current_direc.name} -> {first_move.name}")
        else:
            print(f"🔍 GreedySolver - No se encontró camino hacia la comida")

        # Paso 4
        self._path_solver.snake = self.snake
        path_to_tail = self._path_solver.longest_path_to_tail()
        if len(path_to_tail) > 1:
            first_move = path_to_tail[0]
            if self._is_valid_move(current_direc, first_move):
                print(f"🔍 GreedySolver - paso4")
                return first_move

        # Paso 5 - Buscar movimiento válido que aleje de la comida
        head = self.snake.head()
        print(f"🔍 GreedySolver - cabeza: {head}")
        print(f"🔍 GreedySolver - pos comida: {self.map.food}")
        
        # Buscar movimiento válido que aleje de la comida
        direc, max_dist = self.snake.direc, -1
        for adj in head.all_adj():
            if self.map.is_safe(adj):
                new_direc = head.direc_to(adj)
                if self._is_valid_move(current_direc, new_direc):
                    dist = Pos.manhattan_dist(adj, self.map.food)
                    if dist > max_dist:
                        max_dist = dist
                        direc = new_direc
        
        print(f"🔍 GreedySolver - paso5")
        return direc
    
    def _is_valid_move(self, current_direc, new_direc):
        """
        Valida que el movimiento sea válido (no se puede cambiar de vertical a vertical
        o de horizontal a horizontal directamente).
        """
        from base.direc import Direc
        
        # Si es la misma dirección, es válido
        if current_direc == new_direc:
            print(f"✅ Movimiento válido: {current_direc.name} -> {new_direc.name} (misma dirección)")
            return True
            
        # Definir direcciones verticales y horizontales
        vertical_direcs = {Direc.UP, Direc.DOWN}
        horizontal_direcs = {Direc.LEFT, Direc.RIGHT}
        
        # No se puede cambiar de vertical a vertical o de horizontal a horizontal
        if (current_direc in vertical_direcs and new_direc in vertical_direcs):
            print(f"❌ Movimiento inválido: {current_direc.name} -> {new_direc.name} (vertical a vertical)")
            return False
        if (current_direc in horizontal_direcs and new_direc in horizontal_direcs):
            print(f"❌ Movimiento inválido: {current_direc.name} -> {new_direc.name} (horizontal a horizontal)")
            return False
            
        print(f"✅ Movimiento válido: {current_direc.name} -> {new_direc.name}")
        return True