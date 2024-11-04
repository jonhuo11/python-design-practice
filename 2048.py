from __future__ import annotations
from typing import List
from enum import Enum
from random import choice

class Game2048:

    class GameState(Enum):
        NORMAL=0
        VICTORY=1
        DEFEAT=2

    # 4x4 board 
    # calculate position after swiping in a direction
    # spawn in new tiles
    # check if victory or defeat


    def __init__(self):
        self.__board: List[List[int]] = [
            [0,0,0,0],
            [0,0,0,0],
            [0,0,0,0],
            [0,0,0,0]
        ]
        self.__game_state: Game2048.GameState = Game2048.GameState.NORMAL
        self.__spawn_tile()

    @classmethod
    def __are_boards_equal(cls, board_a: List[List[int]], board_b: List[List[int]]) -> bool:
        for row in range(4):
            for col in range(4):
                if board_a[row][col] != board_b[row][col]:
                    return False
        return True
    

    def __swipe(self, direc: str, wb=True) -> bool:
        # True if the move succeeds
        # collect all items into a stack
        # try to condense the top two items of the stack
        if direc not in list('lrud'):
            return False 

        board = self.__board if wb else [[item for item in row] for row in self.__board]
        cached_board = [[item for item in row] for row in board]
        
        inner_range = range(3, -1, -1)
        if direc == "l" or direc == "u":
            inner_range = range(0,4)

        for row_i in range(4):
            stack: List[int] = []
            for col_i in inner_range:
                tile_spot = (row_i, col_i)
                if direc == "u" or direc == "d":
                    tile_spot = (col_i, row_i)
                tile = board[tile_spot[0]][tile_spot[1]]
                if tile != 0:
                    stack.append(tile)
                    if len(stack) > 1 and stack[-1] == stack[-2]:
                        stack[-2] *= 2
                        stack.pop()
                # clear the tile
                board[tile_spot[0]][tile_spot[1]] = 0
            # write the items on the stack back into the row/col
            write_i = 3 if direc == "r" or direc == "d" else 0
            for i in range(0, len(stack)):
                if direc == "l" or direc == "r":
                    board[row_i][write_i] = stack[i]
                else:
                    board[write_i][row_i] = stack[i]
                write_i += -1 if direc == "r" or direc == "d" else 1

        return not Game2048.__are_boards_equal(board, cached_board)


    def __spawn_tile(self) -> None:
        # find all empty spots on the board and spawn tiles in one of them
        choices = []
        for row_i in range(len(self.__board)):
            for col_i in range(len(self.__board)):
                if self.__board[row_i][col_i] == 0:
                    choices.append((col_i, row_i))
        random_spot = choice(choices)
        self.__board[random_spot[1]][random_spot[0]] = choice([2,4])

    def __state(self) -> Game2048.GameState:
        # check victory
        for row in self.__board:
            for item in row:
                if item == 2048:
                    return Game2048.GameState.VICTORY

        # check defeat
        for move in list('lrud'):
            if self.__swipe(move, False):
                return Game2048.GameState.NORMAL
        return Game2048.GameState.DEFEAT

    def play_move(self, direction: str) -> Game2048.GameState:
        if self.__game_state != Game2048.GameState.NORMAL:
            return self.__game_state
        
        move = self.__swipe(direction, True)
        if not move:
            return self.__game_state
        self.__spawn_tile()

        self.__game_state = self.__state()
        return self.__game_state
        
    def __str__(self) -> str:
        max_len = 0
        for row in self.__board:
            for tile in row:
                max_len = max(max_len, len(str(tile)))
        o = ""
        for row in self.__board:
            for tile in row:
                tile_as_str = str(tile)
                if tile_as_str == "0":
                    tile_as_str = "=" * max_len
                o += (" " * (1 + max_len - len(tile_as_str))) + (tile_as_str)
            o += "\n"
        return o


if __name__ == "__main__":
    game = Game2048()
    print(game)
    while True:
        direc = input("Enter lrud: ")
        result = game.play_move(direc)
        print(game)
        
        if result != Game2048.GameState.NORMAL:
            print("Game over!")
            break

