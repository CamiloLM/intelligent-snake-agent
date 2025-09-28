import time

import pyautogui

from base.direc import Direc  # ¡Asegúrate de que esta línea esté presente!


class Actuator:
    """
    Actuador externo: envía teclas al ambiente con pyautogui.
    Envía la tecla solo si cambia la acción (para evitar spam).
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
            print(
                f"ERROR: Dirección no válida '{direc}'. Debe ser un miembro de Direc (Direc.UP, etc.)."
            )
            return

        # Aquí se presiona la tecla de flecha común (ej: 'up', 'down')
        pyautogui.press(key)

        # Pequeña pausa
        if self.key_delay:
            time.sleep(self.key_delay)


if __name__ == "__main__":
    import time

    actuator = Actuator()

    # CAMBIO CRÍTICO: Debes usar los objetos Direc.UP, Direc.RIGHT, etc., NO las cadenas.
    moves = [Direc.UP, Direc.RIGHT, Direc.DOWN, Direc.LEFT]

    # Tiempo para asegurar que el foco se mueva al juego
    print("Cambiando el foco a la ventana del juego en 3 segundos...")
    pyautogui.hotkey("alt", "tab")
    time.sleep(0.6)

    # Bucle para probar el patrón de cuadrado
    print("Iniciando patrón de cuadrado (UP, RIGHT, DOWN, LEFT)...")

    counter = 0
    while counter < 5:  # Limitar a 5 ciclos para evitar bucle infinito
        for move in moves:
            print(f"Enviando: {move}")
            actuator.send(move)
            time.sleep(0.25)  # Espera 1 segundo para ver el movimiento
        counter += 1

    print("Patrón de cuadrado finalizado.")
