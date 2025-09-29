class Scanner:
    def capture(self):
        """
        Captura el estado actual del juego: la posición de la serpiente y la comida.
        """
        # Aquí deberías implementar la lógica real para capturar el estado del juego.
        # Por ahora, retornamos datos ficticios para ilustrar.
        snake_body = [(8, 7), (8, 6), (8, 5)]
        food_position = (7, 13)
        return snake_body, food_position