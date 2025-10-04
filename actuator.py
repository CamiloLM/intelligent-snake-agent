from time import sleep

import pyautogui

from base.direc import Direc


class Actuator:
    """
    Actuador externo: envía teclas al ambiente con pyautogui.
    Envía la tecla solo si cambia la acción.
    """

    # 0.1235
    # 0.11
    def __init__(self, key_delay: float = 0.11):
        self.key_delay = key_delay
        self.keymap = {
            # Las claves son los OBJETOS de la enumeración Direc
            Direc.UP: "up",
            Direc.DOWN: "down",
            Direc.LEFT: "left",
            Direc.RIGHT: "right",
        }

    def send(self, direc: Direc):
        """Envía la dirección indicada al ambiente."""
        if direc is None:
            return

        sleep(self.key_delay)
        # Obtiene la cadena de la tecla (ej: "up") usando el objeto Direc (ej: Direc.UP)
        key = self.keymap.get(direc)

        if not key:
            raise ValueError(f"Dirección no válida '{direc.name}'.")

        # Aquí se presiona la tecla de flecha común (ej: 'up', 'down')
        pyautogui.press(key)
