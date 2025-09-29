import time

import pyautogui

from base.direc import Direc


class Actuator:
    """
    Actuador externo: envía teclas al ambiente con pyautogui.
    Envía la tecla solo si cambia la acción.
    """

    def __init__(self, key_delay: float = 0.01):
        print("(actuator.py) <__init__> Inicializando actuator...")
        self.key_delay = key_delay
        self.keymap = {
            # Las claves son los OBJETOS de la enumeración Direc
            Direc.UP: "up",
            Direc.DOWN: "down",
            Direc.LEFT: "left",
            Direc.RIGHT: "right",
        }
        print(f"(actuator.py) <__init__> Mapeo de teclas configurado: {self.keymap}")
        print(f"(actuator.py) <__init__> Delay entre teclas: {self.key_delay}s")
        print("(actuator.py) <__init__> Actuator inicializado correctamente")

    def send(self, direc: Direc):
        """Envía la dirección indicada al ambiente (tecla)."""
        print(f"(actuator.py) <send> Recibida dirección: {direc.name if direc else 'None'}")
        
        if direc is None:
            print("(actuator.py) <send> Dirección es None, no se envía tecla")
            return

        # Obtiene la cadena de la tecla (ej: "up") usando el objeto Direc (ej: Direc.UP)
        key = self.keymap.get(direc)
        print(f"(actuator.py) <send> Tecla mapeada: '{key}'")

        if not key:
            print(f"(actuator.py) <send> Error: Dirección no válida '{direc.name}'")
            raise ValueError(f"Dirección no válida '{direc.name}'.")
            
        # Aquí se presiona la tecla de flecha común (ej: 'up', 'down')
        print(f"(actuator.py) <send> Enviando tecla '{key}' al juego...")
        pyautogui.press(key)
        print(f"(actuator.py) <send> Tecla '{key}' enviada correctamente")

        # Pequeña pausa
        if self.key_delay:
            print(f"(actuator.py) <send> Pausando {self.key_delay}s...")
            time.sleep(self.key_delay)


if __name__ == "__main__":
    import time

    actuator = Actuator()

    # Patrón de movimiento en cuadrado
    moves = [Direc.RIGHT, Direc.DOWN, Direc.LEFT, Direc.UP]

    pyautogui.hotkey("alt", "tab")
    time.sleep(0.3)

    counter = 0
    while counter < 15:
        for move in moves:
            print(f"Enviando: {move}")
            actuator.send(move)
            time.sleep(0.25)
        counter += 1


