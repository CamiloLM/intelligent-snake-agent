import time

import pyautogui

from base.direc import Direc


class Actuator:
    """
    Actuador externo: envía teclas al ambiente con pyautogui.
    Envía la tecla solo si cambia la acción.
    """

    def __init__(self, key_delay: float = 0.01):
        self.key_delay = key_delay
        self.keymap = {
            # Las claves son los OBJETOS de la enumeración Direc
            Direc.UP: "up",
            Direc.DOWN: "down",
            Direc.LEFT: "left",
            Direc.RIGHT: "right",
        }

    def send(self, direc: Direc):
        """Envía la dirección indicada al ambiente (tecla)."""
        if direc is None:
            return

        # Obtiene la cadena de la tecla (ej: "up") usando el objeto Direc (ej: Direc.UP)
        key = self.keymap.get(direc)

        if not key:
            raise ValueError(f"Dirección no válida '{direc.name}'.")
            

        # Aquí se presiona la tecla de flecha común (ej: 'up', 'down')
        pyautogui.press(key)

        # Pequeña pausa
        if self.key_delay:
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


