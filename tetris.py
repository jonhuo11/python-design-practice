from __future__ import annotations

from typing import List, Dict, Tuple


class Piece:
    def __init__(self, x:int, y:int, shape: List[List[int]]):
        self.__x: int = x
        self.__y: int = y
        self.__shape: List[List[int]] = shape

    @property
    def x(self) -> int:
        return self.__x
    
    @property
    def y(self) -> int:
        return self.__y
    
    @property
    def shape(self) -> List[List[int]]:
        return [[col for col in row] for row in self.__shape]
    
    @property
    def xlen(self) -> int:
        return len(self.__shape[0])
    
    @property
    def ylen(self) -> int:
        return len(self.__shape)

    def rotate(self, left=False) -> None:
        self.__shape = list(zip(*self.__shape))
        if not left:
            for row in self.__shape:
                row.reverse()
        else:
            for col in range(len(self.__shape[0])):
                for row in range(len(self.__shape)//2):
                    self.__shape[row][col], self.__shape[-(row + 1)][col] = self.__shape[-(row + 1)][col], self.__shape[row][col]
    
    def move(self, dir: str) -> None:
        if dir == "l":
            self.__x -= 1
        elif dir == "r":
            self.__x += 1
        elif dir == "u":
            self.__y -= 1
        else:
            self.__y += 1


class TetrisGame:

    __tetris_pieces = [
        [
            [0,1,0],
            [0,1,0],
            [0,1,1]
        ],
        [
            [1,0],
            [1,1],
            [0,1]
        ]
    ]

    def __init__(self, width: int, height: int):
        self.__score: int = 0
        self.__width = width
        self.__height = height
        self.__grid: List[List[int]] = [[0] * width for _ in range(height)]
        self.__active_piece: None | Piece = None

    def __can_move(self, direction: str) -> bool:
        if self.__active_piece is None:
            return False
        # return true if moving the shape in some direction will cause it to stop
        # false otherwise
        move_loc = [self.__active_piece.x, self.__active_piece.y]
        if direction == "l":
            move_loc[0] -= 1
        elif direction == "r":
            move_loc[0] += 1
        elif direction == "u":
            move_loc[1] -= 1
        else:
            move_loc[1] += 1

        # loop through all of the new piece locations
        # check if it intersects with something placed on the grid
        shape = self.__active_piece.shape
        xlen = self.__active_piece.xlen
        ylen = self.__active_piece.ylen
        for row_i in range(ylen):
            for col_i in range(xlen):
                if shape[row_i][col_i] == 1:
                    grid_spot = (self.__active_piece.x + row_i, self.__active_piece.y + col_i)
                    if self.__grid[grid_spot[1]][grid_spot[0]] == 1:
                        # intersection
                        return False
        return True


    def __place_active_piece(self) -> None:
        # writes the active piece to the grid
        shape = self.__active_piece.shape
        for row_i in range(self.__active_piece.ylen):
            for col_i in range(self.__active_piece.xlen):
                if shape[row_i][col_i] == 1:
                    
                    self.__grid[]

    def __spawn_piece(self) -> None:
        # pick a random piece and spawn in
        pass

    def __can_clear_row(self) -> None:
        pass

    
    def tick() -> None:
        # try to move the piece down (gravity)
        # if we cant, stop it by writing it to the grid location, and spawn a new piece
        # at this point also check for loss (the top of the piece == 0)
        pass
