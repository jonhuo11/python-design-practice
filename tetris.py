from os import system
from typing import List, Tuple

def blit(content: str) -> None:
    system('clear')
    print(content, end='')

class Shape:
    def __init__(self, grid: List[List[int]]):
        # shapes are defined within an X by Y grid, rotated around the center coord on that grid
        self.width = grid[0]
        self.height = grid[1]
        self.__x = 0
        self.__y = 0
        self.__center_x = self.width // 2
        self.__center_y = self.height // 2
        self.__grid: List[List[int]] = grid

    def rotate(self) -> None:
        for coord in self.__grid:
            centered_coord = [coord[0] - self.__center_x, coord[1] - self.__center_y]
            centered_coord[0], centered_coord[1] = centered_coord[1], -centered_coord[0]
            coord[0] = centered_coord[0] + self.__center_x
            coord[1] = centered_coord[1] + self.__center_y

    def move(self, dir_: Tuple[int, int]) -> None:
        self.__x += dir_[0]
        self.__y += dir_[1]

    @property
    def in_world(self) -> List[List[int]]:
        pass


class Tetris:
    def __init__(self, rows: int, cols: int):
        self.__grid: List[List[int]] = [[0] * cols for _ in range(rows)]
        self.__active_shape: Shape | None = None

    def spawn_shape(self) -> None:
        if self.__active_shape is not None:
            return
        self.__active_shape = Shape([
            [0, 1, 0],
            [0, 1, 0],
            [1, 1, 0]
        ])
        self.__active_shape.move((2,0))

    def step(self):
        if self.__active_shape is not None:
            self.__active_shape.move((0,1))
            self.__active_shape.rotate()

    def __str__(self) -> str:
        if self.__active_shape is not None:
            for coord in self.__active_shape.structure:
                self.__grid[coord[1]][coord[0]] = 1

        output = ""
        for row in self.__grid:
            for data in row:
                output += str(data)
            output += "\n"

        if self.__active_shape is not None:
            for coord in self.__active_shape.structure:
                self.__grid[coord[1]][coord[0]] = 0

        return output

if __name__ == "__main__":
    tetris = Tetris(10,6)
    tetris.spawn_shape()
    while True:
        input()
        blit(str(tetris))

        tetris.step()