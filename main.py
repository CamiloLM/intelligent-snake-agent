import time
from base import Direc, Map, Pos, PointType, Snake
from solver import GreedySolver
from actuator import Actuator   
from game_scanner import Scanner
import pyautogui    

class Agent:    
    """Agente Inteligente que juega Snake de Google automáticamente."""
    def __init__(self):
        """ 
        scanner: instancia de Scanner para leer el estado del juego.
        actuator: instancia de Actuator para enviar teclas.
        map: mapa interno del juego (como en game.py)
        snake: serpiente int    erna (como en game.py)
        solver: GreedySolver para calcular direcciones óptimas
        """
        print("🤖 Inicializando agente inteligente...")
        self.scanner = Scanner()
        self.actuator = Actuator()
        
        # Crear mapa y serpiente internos (como en game.py)
        self.map = Map(15 + 2, 17 + 2)  # 15x17 + bordes
        
        # Inicializar serpiente como en game.py
        init_bodies = [Pos(7, 4), Pos(7, 3), Pos(7, 2), Pos(7, 1)]
        init_types = [PointType.HEAD_D] + [PointType.BODY_HOR] * (len(init_bodies) - 1)
        init_direc = Direc.RIGHT
        
        self.snake = Snake(self.map, init_direc, init_bodies, init_types)
            
        # Crear comida inicial  
        self.map.create_food(Pos(7, 13))
        
        # Crear solver
        self.solver = GreedySolver(self.snake)
        
        # Variables para seguimiento de ruta
        self.current_path = None
        self.path_index = 0
        self.last_food_position = None
        
        print("✅ Agente inicializado correctamente")
    
    def run(self):
        """Bucle principal usando GreedySolver como en game.py"""   
        print("🚀 Iniciando agente inteligente de Snake...")
        try:
            while True:
                # 1. Leer estado desde pantalla
                head_position, food_position = self.scanner.capture()
                
                # 2. Sincronizar estado interno con el juego real
                self._sync_internal_state(head_position, food_position)
                
                # 3. Calcular dirección usando estrategia de ruta única
                direc = self._get_next_direction()

                # Debug: mostrar información del solver
                print(f"🧠 Solver - Cabeza: {self.snake.head()}, Comida: {self.map.food if self.map.has_food() else 'None'}")
                print(f"🧠 Solver - Dirección calculada: {direc.name if direc else 'None'}")
                
                # 4. Enviar tecla al juego
                if direc is not None and direc != Direc.NONE:
                    print(f"🎯 Decisión: {direc.name}")
                    self.actuator.send(direc)
                else:
                    print("⚠️  No se envía tecla (dirección inválida)")
                
                # 5. Pausa para no sobrecargar el sistema
                time.sleep(0.005)  # Tiempo mínimo para decisiones ultra-rápidas
                    
        except KeyboardInterrupt:
            print("🛑 Interrupción detectada, deteniendo agente...")
        finally:
            # Limpiar recursos d    el scanner
            if hasattr(self.scanner, 'cleanup'):
                self.scanner.cleanup()
            print("✅ Agente detenido correctamente")



    def _sync_internal_state(self, head_position, food_position):
        """
        Sincroniza el estado interno de la serpiente con el estado real del juego.
        
        Args:
            head_position: [x, y] posición de la cabeza detectada
            food_position: [x, y] posición de la comida detectada
        """
        # Debug: mostrar posiciones detectadas
        print(f"🔍 Detectado - Cabeza: {head_position}, Comida: {food_position}")
        
        # Convertir coordenadas del scanner a coordenadas del mapa interno
        # El scanner usa [x, y] pero el mapa interno usa Pos(row, col)
        if head_position and len(head_position) == 2:
            head_x, head_y = head_position
            # CORRECCIÓN: El scanner devuelve [x, y] donde:
            # - x es la columna (0-16)
            # - y es la fila (0-14) desde arriba hacia abajo
            # El mapa interno usa (row, col) donde:
            # - row es la fila desde abajo hacia arriba (1-15)
            # - col es la columna (1-17)
            
            # Convertir Y: scanner (0-14, arriba-abajo) -> mapa (1-15, abajo-arriba)
            # IMPORTANTE: El solver espera coordenadas donde Y=0 está arriba
            # CORRECCIÓN: Ajustar Y para compensar desfase
            internal_row = head_y + 2  # Ajuste: 0->2, 1->3, ..., 14->16
            internal_col = head_x + 1   # X: 0->1, 1->2, ..., 16->17
            
            internal_head = Pos(internal_row, internal_col)
            print(f"📍 Cabeza interna: {internal_head} (scanner: [{head_x}, {head_y}])")
            
            # Actualizar la serpiente completa en el mapa interno
            # Limpiar toda la serpiente anterior
            for body_pos in self.snake.bodies:
                self.map.point(body_pos).type = PointType.EMPTY
            
            # Crear nueva serpiente con la cabeza detectada
            # Asumir que la serpiente tiene 4 segmentos (cabeza + 3 cuerpo)
            new_bodies = [internal_head]
            for i in range(1, 4):  # 3 segmentos adicionales
                # Calcular posición del cuerpo basándose en la dirección anterior
                if i == 1:
                    # Segundo segmento (cuerpo) - asumir dirección hacia atrás
                    body_pos = Pos(internal_head.x, internal_head.y - 1)
                else:
                    # Segmentos adicionales
                    body_pos = Pos(internal_head.x, internal_head.y - i)
                new_bodies.append(body_pos)
            
            # Crear nueva serpiente con los cuerpos calculados
            # Determinar la dirección basándose en el movimiento anterior
            if hasattr(self, 'last_head_position') and self.last_head_position:
                last_x, last_y = self.last_head_position
                print(f"🔍 Debug - Posición anterior: [{last_x}, {last_y}], actual: [{head_x}, {head_y}]")
                
                # Calcular diferencia de movimiento
                dx = head_x - last_x
                dy = head_y - last_y
                
                print(f"🔍 Debug - Diferencia: dx={dx}, dy={dy}")
                
                # Determinar dirección basándose en el movimiento más significativo
                # PRIORIDAD: Si hay movimiento horizontal, usar horizontal
                # Si no hay movimiento horizontal, usar vertical
                if dx != 0:
                    # Movimiento horizontal detectado
                    if dx > 0:
                        current_direc = Direc.RIGHT
                        head_type = PointType.HEAD_R
                    else:
                        current_direc = Direc.LEFT
                        head_type = PointType.HEAD_L
                elif dy != 0:
                    # Solo movimiento vertical
                    if dy > 0:
                        current_direc = Direc.DOWN
                        head_type = PointType.HEAD_D
                    else:
                        current_direc = Direc.UP
                        head_type = PointType.HEAD_U
                else:
                    # No hay movimiento, mantener dirección anterior
                    current_direc = getattr(self, 'last_direc', Direc.RIGHT)
                    head_type = PointType.HEAD_R
            else:
                current_direc = Direc.RIGHT  # Default para la primera iteración
                head_type = PointType.HEAD_R
            
            # Guardar dirección para la siguiente iteración
            self.last_direc = current_direc
            print(f"🔍 Debug - Dirección calculada: {current_direc.name}")
            
            new_types = [head_type] + [PointType.BODY_HOR] * (len(new_bodies) - 1)
            self.snake = Snake(self.map, current_direc, new_bodies, new_types)
            
            # Marcar las posiciones en el mapa
            self.map.point(internal_head).type = PointType.HEAD_R
            for i, body_pos in enumerate(new_bodies[1:], 1):
                self.map.point(body_pos).type = PointType.BODY_HOR
            
            # CRÍTICO: Actualizar el solver con la nueva serpiente
            self.solver = GreedySolver(self.snake)
            
            # Guardar posición actual para el siguiente cálculo de dirección
            self.last_head_position = head_position
        
        # Actualizar posición de la comida
        if food_position and food_position != [-1, -1] and len(food_position) == 2:
            food_x, food_y = food_position
            # CORRECCIÓN: Aplicar la misma conversión que para la cabeza
            internal_row = food_y + 2  # Ajuste: 0->2, 1->3, ..., 14->16
            internal_col = food_x + 1   # X: 0->1, 1->2, ..., 16->17
            internal_food = Pos(internal_row, internal_col)
            print(f"🍎 Comida interna: {internal_food} (scanner: [{food_x}, {food_y}])")
            
            # Remover comida anterior y crear nueva
            if self.map.has_food():
                old_food = self.map.food
                self.map.point(old_food).type = PointType.EMPTY
            self.map.create_food(internal_food)
        else:
            print("⚠️  No se detectó comida o posición inválida")
    
    def _get_next_direction(self):
        """
        Calcula la siguiente dirección usando estrategia de ruta única.
        Solo recalcula la ruta cuando aparece comida nueva.
        """
        # Verificar si la comida cambió
        current_food = self.map.food if self.map.has_food() else None
        food_changed = (current_food != self.last_food_position)
        
        if food_changed:
            print(f"🍎 Comida cambió! Recalculando ruta...")
            print(f"🍎 Comida anterior: {self.last_food_position}")
            print(f"🍎 Comida nueva: {current_food}")
            
            # Recalcular ruta completa
            self.current_path = self.solver._path_solver.shortest_path_to_food()
            self.path_index = 0
            self.last_food_position = current_food
            
            if self.current_path:
                print(f"🛤️  Nueva ruta calculada: {list(self.current_path)}")
            else:
                print(f"❌ No se encontró ruta hacia la comida")
        
        # Verificar si está cerca del borde y apuntando hacia él
        if self._is_near_border_and_pointing_towards_it():
            print(f"⚠️  Cerca del borde y apuntando hacia él, recalculando ruta preventiva...")
            self.current_path = self.solver._path_solver.shortest_path_to_food()
            self.path_index = 0
            
            if self.current_path:
                print(f"🛤️  Ruta preventiva calculada: {list(self.current_path)}")
            else:
                print(f"❌ No se pudo calcular ruta preventiva")
        
        # Si tenemos una ruta válida, seguir el siguiente paso
        if self.current_path and self.path_index < len(self.current_path):
            next_direction = self.current_path[self.path_index]
            self.path_index += 1
            
            # Validar que el movimiento sea válido
            current_direc = self.snake.direc
            if self._is_valid_move(current_direc, next_direction):
                print(f"🛤️  Siguiendo ruta: paso {self.path_index}/{len(self.current_path)} -> {next_direction.name}")
                return next_direction
            else:
                print(f"❌ Movimiento inválido en ruta: {current_direc.name} -> {next_direction.name}")
                # Recalcular ruta si el movimiento es inválido
                print(f"🔄 Recalculando ruta desde posición actual...")
                print(f"🔄 Posición actual: {self.snake.head()}")
                print(f"🔄 Comida: {self.map.food}")
                self.current_path = self.solver._path_solver.shortest_path_to_food()
                self.path_index = 0
                
                if self.current_path:
                    print(f"🛤️  Nueva ruta calculada: {list(self.current_path)}")
                    # Intentar el primer movimiento de la nueva ruta
                    if self.path_index < len(self.current_path):
                        next_direction = self.current_path[self.path_index]
                        self.path_index += 1
                        
                        if self._is_valid_move(current_direc, next_direction):
                            print(f"🛤️  Siguiendo nueva ruta: paso {self.path_index}/{len(self.current_path)} -> {next_direction.name}")
                            return next_direction
                        else:
                            print(f"❌ Nuevo movimiento también inválido: {current_direc.name} -> {next_direction.name}")
                else:
                    print(f"❌ No se pudo calcular nueva ruta")
        
        # Si no hay ruta válida, usar dirección segura
        print(f"🔄 No hay ruta válida, usando dirección segura")
        return self._get_safe_direction()
    
    def _is_valid_move(self, current_direc, new_direc):
        """
        Valida que el movimiento sea válido (no se puede cambiar de vertical a vertical
        o de horizontal a horizontal directamente).
        """
        from base.direc import Direc
        
        # Si es la misma dirección, es válido
        if current_direc == new_direc:
            return True
            
        # Definir direcciones verticales y horizontales
        vertical_direcs = {Direc.UP, Direc.DOWN}
        horizontal_direcs = {Direc.LEFT, Direc.RIGHT}
        
        # No se puede cambiar de vertical a vertical o de horizontal a horizontal
        if (current_direc in vertical_direcs and new_direc in vertical_direcs):
            return False
        if (current_direc in horizontal_direcs and new_direc in horizontal_direcs):
            return False
            
        return True
    
    def _get_safe_direction(self):
        """
        Obtiene una dirección segura considerando la dirección actual y la posición de la comida.
        Evita movimientos inválidos y prioriza movimientos hacia la comida.
        """
        current_direc = self.snake.direc
        head_pos = self.snake.head()
        food_pos = self.map.food
        
        print(f"🎯 Buscando dirección segura desde {current_direc.name}")
        print(f"🎯 Cabeza: {head_pos}, Comida: {food_pos}")
        
        # Calcular dirección hacia la comida
        dx = food_pos.x - head_pos.x
        dy = food_pos.y - head_pos.y
        
        print(f"🎯 Diferencia hacia comida: dx={dx}, dy={dy}")
        
        # Si la comida está en línea recta en la dirección actual, continuar
        if self._is_food_in_current_direction(dx, dy, current_direc):
            print(f"🎯 Comida en línea recta, continuando: {current_direc.name}")
            return current_direc
        
        # Buscar dirección válida hacia la comida
        preferred_directions = self._get_preferred_directions(dx, dy, current_direc)
        
        for direc in preferred_directions:
            next_pos = head_pos.adj(direc)
            if self.map.is_safe(next_pos) and self._is_valid_move(current_direc, direc):
                print(f"🎯 Dirección segura encontrada: {direc.name}")
                return direc
        
        # Si no hay dirección válida hacia la comida, buscar cualquier dirección segura
        for direc in [Direc.UP, Direc.DOWN, Direc.LEFT, Direc.RIGHT]:
            next_pos = head_pos.adj(direc)
            if self.map.is_safe(next_pos) and self._is_valid_move(current_direc, direc):
                print(f"🎯 Dirección de emergencia: {direc.name}")
                return direc
        
        # Último recurso: mantener dirección actual si es segura
        next_pos = head_pos.adj(current_direc)
        if self.map.is_safe(next_pos):
            print(f"🎯 Manteniendo dirección actual: {current_direc.name}")
            return current_direc
        
        # Si todo falla, usar el solver original
        print(f"🎯 Usando solver original como último recurso")
        return self.solver.next_direc()
    
    def _is_food_in_current_direction(self, dx, dy, current_direc):
        """
        Verifica si la comida está en línea recta en la dirección actual.
        """
        if current_direc == Direc.RIGHT and dx > 0 and dy == 0:
            return True
        elif current_direc == Direc.LEFT and dx < 0 and dy == 0:
            return True
        elif current_direc == Direc.DOWN and dy > 0 and dx == 0:
            return True
        elif current_direc == Direc.UP and dy < 0 and dx == 0:
            return True
        return False
    
    def _get_preferred_directions(self, dx, dy, current_direc):
        """
        Obtiene las direcciones preferidas basándose en la posición de la comida
        y la dirección actual, evitando movimientos inválidos.
        """
        from base.direc import Direc
        
        # Si estamos moviéndonos horizontalmente, priorizar movimiento vertical
        if current_direc in [Direc.LEFT, Direc.RIGHT]:
            if dy > 0:
                return [Direc.DOWN, Direc.LEFT, Direc.RIGHT, Direc.UP]
            elif dy < 0:
                return [Direc.UP, Direc.LEFT, Direc.RIGHT, Direc.DOWN]
            else:
                return [Direc.UP, Direc.DOWN, Direc.LEFT, Direc.RIGHT]
        
        # Si estamos moviéndonos verticalmente, priorizar movimiento horizontal
        elif current_direc in [Direc.UP, Direc.DOWN]:
            if dx > 0:
                return [Direc.RIGHT, Direc.UP, Direc.DOWN, Direc.LEFT]
            elif dx < 0:
                return [Direc.LEFT, Direc.UP, Direc.DOWN, Direc.RIGHT]
            else:
                return [Direc.LEFT, Direc.RIGHT, Direc.UP, Direc.DOWN]
        
        # Fallback
        return [Direc.UP, Direc.DOWN, Direc.LEFT, Direc.RIGHT]
    
    def _is_near_border_and_pointing_towards_it(self):
        """
        Verifica si la serpiente está a 3 posiciones o menos de algún borde
        y está apuntando hacia ese borde.
        """
        head_pos = self.snake.head()
        current_direc = self.snake.direc
        
        # Obtener dimensiones del mapa (asumiendo que el mapa es 15x17)
        map_rows = 15
        map_cols = 17
            
        print(f"🔍 Verificando proximidad al borde: {head_pos}, dirección: {current_direc.name}")
        
        # Verificar bordes y dirección
        near_border = False
        
        # Borde superior (row = 1)
        if head_pos.x <= 3 and current_direc == Direc.UP:
            print(f"⚠️  Cerca del borde superior: row={head_pos.x} <= 3, apuntando UP")
            near_border = True
        
            # Borde inferior (row = 15)
        elif head_pos.x >= map_rows - 2 and current_direc == Direc.DOWN:
            print(f"⚠️  Cerca del borde inferior: row={head_pos.x} >= {map_rows - 2}, apuntando DOWN")
            near_border = True
            
        # Borde izquierdo (col = 1)
        elif head_pos.y <= 3 and current_direc == Direc.LEFT:
            print(f"⚠️  Cerca del borde izquierdo: col={head_pos.y} <= 3, apuntando LEFT")
            near_border = True
        
        # Borde derecho (col = 17)
        elif head_pos.y >= map_cols - 2 and current_direc == Direc.RIGHT:
            print(f"⚠️  Cerca del borde derecho: col={head_pos.y} >= {map_cols - 2}, apuntando RIGHT")
            near_border = True
        
        if near_border:
            print(f"⚠️  DETECTADO: Cerca del borde y apuntando hacia él!")
        
        return near_border

if __name__ == "__main__":
    # Crear agente
    agent = Agent()
    
    print("Iniciando agente inteligente de Snake...")
    print("Asegúrate de que el juego Snake esté abierto y visible")
    print("Presiona Ctrl+C para detener")
    
    # Cambiar a la ventana del juego
    pyautogui.hotkey("alt", "tab")
    time.sleep(0.5)
    
    agent.run()