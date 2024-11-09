from __future__ import annotations
from typing import List, Dict, Tuple, Set
from enum import Enum
import random

class Minesweeper:

    class GameStates(Enum):
        VICTORY=1
        DEFEAT=2
        NORMAL=3

    # board
    # spawn mines
    # keep track of which areas are opened and closed
    # on click handle exposing area
    # win/lose/score state

    __mined = -1
    __unknown = -2

    def __init__(self, rows: int, cols: int, mines: int):
        # create board
        # spawn mines
        self.__rows = rows
        self.__cols = cols
        self.__mines = mines
        self.__exposed_tiles = 0
        self.__board: List[List[int]] = [[Minesweeper.__unknown] * self.__cols for _ in range(self.__rows)]
        self.__game_state: Minesweeper.GameStates = Minesweeper.GameStates.NORMAL
        self.__flags: Set[Tuple[int,int]] = set()

        # randomly place mines
        remaining_positions = []
        for row_i in range(self.__rows):
            for col_i in range(self.__cols):
                remaining_positions.append((col_i, row_i))
        
        for _ in range(mines):
            random_pos = remaining_positions.pop(random.randint(0, len(remaining_positions) - 1))
            self.__board[random_pos[1]][random_pos[0]] = Minesweeper.__mined


    def expose(self, click_point: Tuple[int,int]) -> Minesweeper.GameStates:
        # return False if we didnt click on a mine, return True if we clicked on a mine and the game ends
        
        # check if the click point is on a mine
        click_x, click_y = click_point
        if self.__board[click_y][click_x] == Minesweeper.__mined:
            self.__game_state = Minesweeper.GameStates.DEFEAT
            return Minesweeper.GameStates.DEFEAT

        # bfs around the click point, visiting coords that do not touch a mine
        visited: Set[Tuple[int,int]] = set()
        q = [click_point]
        while q:
            cur = q.pop(0)
            cur_x, cur_y = cur
            if cur in visited or self.__board[cur_y][cur_x] != Minesweeper.__unknown:
                continue
            visited.add(cur)
            self.__exposed_tiles += 1
            
            # visit all neighbors
            mined_neighbors = 0
            neighbors = []
            for y in range(cur_y - 1, cur_y + 2):
                for x in range(cur_x - 1, cur_x + 2):
                    # check out of bounds or self
                    if y < 0 or y >= self.__rows or x < 0 or x >= self.__cols or (y == cur_y and x == cur_x):
                        continue
                    # check touching mine
                    neighbor_tile = self.__board[y][x]
                    if neighbor_tile == Minesweeper.__mined:
                        mined_neighbors += 1
                    neighbors.append((x, y))
            
            self.__board[cur_y][cur_x] = mined_neighbors
            if mined_neighbors == 0:
                q += neighbors

        # check condition
        if self.__exposed_tiles == (self.__cols * self.__rows) - self.__mines:
            self.__game_state = Minesweeper.GameStates.VICTORY
            return self.__game_state
        
        return Minesweeper.GameStates.NORMAL


    def place_flag(self, flag_point: Tuple[int,int]) -> None:
        # lets the user mark a spot with a flag
        self.__flags.add(flag_point)

    def __str__(self) -> str:
        o = ""
        for row in self.__board:
            for item in row:
                if item == Minesweeper.__mined or item == Minesweeper.__unknown:
                    o += "?"
                else:
                    o += str(item) if item != 0 else " "
            o += "\n"
        return o


if __name__ == "__main__":
    ms = Minesweeper(10,10,10)
    while True:
        print(ms)
        xstr, ystr = input().split()
        result = ms.expose((int(xstr), int(ystr)))
        if result == Minesweeper.GameStates.DEFEAT:
            print("game over!")
            break
        elif result == Minesweeper.GameStates.VICTORY:
            print("win!")
            break
