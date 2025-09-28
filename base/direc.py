from enum import Enum, unique


@unique
class Direc(Enum):
    """Enum con las direcciones posibles."""

    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3
    NONE = 4

    @staticmethod
    def opposite(direction):
        opposites = {
            Direc.UP: Direc.DOWN,
            Direc.DOWN: Direc.UP,
            Direc.LEFT: Direc.RIGHT,
            Direc.RIGHT: Direc.LEFT,
            Direc.NONE: Direc.NONE,
        }
        return opposites.get(direction, Direc.NONE)


if __name__ == "__main__":
    # Example usage
    print(Direc.UP)  # Output: Direc.UP
    print(Direc.opposite(Direc.LEFT))  # Output: Direc.RIGHT:w
