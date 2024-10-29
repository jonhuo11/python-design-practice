from typing import List

EMPTY = "="

class ConnectFour:
    def __init__(self, rows: int, cols: int):
        self.board: List[List[int]] = [[EMPTY] * cols for _ in range(rows)]

    def is_victory(self, source_x: int, source_y: int) -> bool:
        pass

    def longest_line_from(self, source_x: int, source_y: int, max: int = 4) -> int:
        pass

    def place_chip(self, col: int) -> int:
        # return X or O depending on who wins
        pass