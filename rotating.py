from __future__ import annotations
from typing import Dict, Tuple, List
from abc import ABC, abstractmethod
import curses
import time

BLANK_CHARACTER = " "

class Drawable(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def clear(self, stdscr: curses.window) -> None:
        pass

    @abstractmethod
    def draw(self, stdscr: curses.window) -> None:
        pass

class RotatingShape(Drawable):
    def __init__(self, x:int, y:int, shape: List[List[int]]):
        self.__x: int = x
        self.__y: int = y
        self.__shape: List[List[int]] = [[c for c in shape[row]] for row in range(len(shape))]

    @property
    def x(self) -> int:
        return self.__x
    
    @property
    def y(self) -> int:
        return self.__y
    
    def rotate(self, left=False) -> None:
        self.__shape = [list(row) for row in list(zip(*self.__shape))]
        if not left:
            for row in self.__shape:
                row.reverse()
        else:
            for col in range(len(self.__shape[0])):
                for row in range(0, len(self.__shape)//2):
                    self.__shape[row][col], self.__shape[-(row+1)][col] = self.__shape[-(row+1)][col], self.__shape[row][col]

    def clear(self, stdscr: curses.window) -> None:
        for row in range(len(self.__shape)):
            for col in range(len(self.__shape)):
                stdscr.addch(self.__y + row, self.__x + col, BLANK_CHARACTER)

    def draw(self, stdscr: curses.window) -> None:
        for row in range(len(self.__shape)):
            for col in range(len(self.__shape)):
                if self.__shape[row][col] != 0:
                    stdscr.addch(self.__y + row, self.__x + col, "#")


def main(stdscr: curses.window):
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(100)

    height, width = stdscr.getmaxyx()

    try:
        shape = RotatingShape(width//2, height//2, [
            [0,1,0],
            [0,1,0],
            [1,1,0]
        ])

        while True:
            
            key = stdscr.getch()
            if key == curses.KEY_RIGHT:
                shape.rotate()
            elif key == curses.KEY_LEFT:
                shape.rotate(True)

            shape.clear(stdscr)
            shape.draw(stdscr)

            stdscr.refresh()
    except KeyboardInterrupt:
        return
    
curses.wrapper(main)