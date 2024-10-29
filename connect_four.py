from typing import List, Tuple
from enum import Enum

class TileType(Enum):
    EMPTY = "="
    PLAYER_1 = "X"
    PLAYER_2 = "O"


class ConnectFour:
    scan_dirs: List[Tuple[int, int]] = [
        (1,1),
        (1,0),
        (0,1),
        (1,-1)
    ]

    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        self.board: List[List[TileType]] = [[TileType.EMPTY] * cols for _ in range(rows)]

    def victory_for(self, source_x: int, source_y: int) -> TileType:
        if (self.longest_line_from(source_x, source_y) >= 4):
            return self.board[source_y][source_x]
        else:
            return TileType.EMPTY

    def scan_line_in_direction(self, dir_vec: Tuple[int, int], source: Tuple[int, int], target_type: TileType, dist: int) -> int:
        if self.board[source[1]][source[0]] != target_type:
            return 0
        
        fwd_count = 0
        fwd_pos = [source[0], source[1]]
        for _ in range(dist):
            fwd_pos[0] += dir_vec[0] # dont count the source as one
            fwd_pos[1] += dir_vec[1]
            if fwd_pos[0] < 0 or fwd_pos[0] >= self.cols or fwd_pos[1] < 0 or fwd_pos[1] >= self.rows:
                break
            if self.board[fwd_pos[1]][fwd_pos[0]] != target_type:
                break
            fwd_count += 1
        return fwd_count


    def longest_line_from(self, source_x: int, source_y: int, max_: int = 4) -> int:
        target_type = self.board[source_y][source_x]
        if target_type == TileType.EMPTY: # must be a player tile
            return 0
        longest_line = 0
        for dir in ConnectFour.scan_dirs:
            dist_fwd = self.scan_line_in_direction(dir, (source_x, source_y), target_type, max_)
            dist_bwd = self.scan_line_in_direction((-dir[0], -dir[1]), (source_x, source_y), target_type, max_)
            longest_line = max(longest_line, 1 + dist_fwd + dist_bwd)
        return longest_line

    def place_chip(self, col: int, type: TileType) -> TileType:
        # return X or O depending on who wins
        placement_y = -1
        for i, row in enumerate(self.board):
            if row[col] != TileType.EMPTY:
                if i == 0:
                    return TileType.EMPTY
                self.board[i - 1][col] = type
                placement_y = i - 1
                break
            elif i == self.rows - 1 and row[col] == TileType.EMPTY:
                self.board[i][col] = type
                placement_y = i
                break
        if placement_y == -1: return TileType.EMPTY
        return self.victory_for(col, placement_y)

    def __str__(self) -> str:
        out = ""
        for row in self.board:
            out_row = ""
            for col in row:
                if col == TileType.EMPTY: 
                    out_row += "="
                elif col == TileType.PLAYER_1: 
                    out_row += "X"
                elif col == TileType.PLAYER_2: 
                    out_row += "O"
            out += out_row + "\n"
        return out
    

if __name__ == "__main__":
    c4 = ConnectFour(5, 5)
    while True:
        input_split = input().split()
        col = int(input_split[0])
        type_ = TileType(input_split[1])

        winner = c4.place_chip(col, type_)
        print(str(c4))
        if winner != TileType.EMPTY:
            print("Winner", winner)