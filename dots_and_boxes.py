from __future__ import annotations
from os import system

from typing import List, Dict, Tuple

class DotsAndLines:
    class __Box:
        dir_to_vec = {
            "l": (-1, 0),
            "r": (1, 0),
            "u": (0, -1),
            "d": (0, 1)
        }
        opposite_dir = {
            "l": "r",
            "r": "l",
            "u": "d",
            "d": "u"
        }

        def __init__(self):
            self.l: bool = False
            self.r: bool = False
            self.u: bool = False
            self.d: bool = False

        @property
        def filled(self) -> bool:
            return self.l and self.r and self.u and self.d
        
        
        def fill(self, dir_: str) -> None:
            if dir_ not in list("lrud"):
                return
            
            if dir_ == "l":
                self.l = True
            elif dir_ == "r":
                self.r = True
            elif dir_ == "u":
                self.u = True
            elif dir_ == "d":
                self.d = True
            else:
                return
    
    def __init__(self, height: int, width: int, box_render_size: int = 3):
        self.__height: int = height
        self.__width: int = width
        self.__box_grid: List[List[DotsAndLines.__Box | None]] = []
        self.__render_grid: List[List[int]] = []
        self.__box_render_size: int = box_render_size

        # initialize grid of boxes
        for row_i in range(self.__height):
            self.__box_grid.append([None] * self.__width)
            for col_i in range(self.__width):
                self.__box_grid[row_i][col_i] = DotsAndLines.__Box()
    

        # (n - 1) bars between n boxes, add 2 bars on outsides = (n + 1) bar pixels
        # total grid size is (box_size * n) + (n + 1)
        render_width = (self.__box_render_size * self.__width) + (self.__width + 1)
        render_height = (self.__box_render_size * self.__height) + (self.__height + 1)
        self.__render_grid = [[0] * render_width for _ in range(render_height)]

        # draw dots initially on render grid
        for row_i in range(0, render_height, self.__box_render_size + 1):
            for col_i in range(0, render_width, self.__box_render_size + 1):
                self.__render_grid[row_i][col_i] = 1

    def __valid_coords(self, coords: Tuple[int,int]) -> bool:
        if coords[0] < 0 or coords[0] >= self.__width:
            return False
        if coords[1] < 0 or coords[1] >= self.__height:
            return False
        return True
    
    def __coords_in_dir(self, origin: Tuple[int, int], dir_: str) -> Tuple[int, int]:
        # gets the box in the direction
        # origin in (x,y)
        if dir_ not in list("lrud"):
            return None
        dir2vec = DotsAndLines.__Box.dir_to_vec[dir_]
        neighbor_coords = (origin[0] + dir2vec[0], origin[1] + dir2vec[1])
        return neighbor_coords

    def __neighbor_in_dir(self, origin: Tuple[int, int], dir_: str) -> DotsAndLines.__Box | None:
        cd = self.__coords_in_dir(origin, dir_)
        if not self.__valid_coords(cd):
            return None
        
        return self.__box_grid[cd[1]][cd[0]]
    
    def __render_box(self, box_coord: Tuple[int, int]) -> None:
        if not self.__valid_coords(box_coord):
            return
        # find top left coord
        top_left = (box_coord[0] * (self.__box_render_size + 1), box_coord[1] * (self.__box_render_size + 1))

        # top right, bottom left
        top_right = (top_left[0] + self.__box_render_size + 1, top_left[1])
        bot_left = (top_left[0], top_left[1] + self.__box_render_size + 1)
        box: DotsAndLines.__Box = self.__box_grid[box_coord[1]][box_coord[0]]

        # render sides
        if box.l:
            for y in range(top_left[1], top_left[1] + self.__box_render_size + 2):
                self.__render_grid[y][top_left[0]] = 1
        if box.r:
            for y in range(top_right[1], top_right[1] + self.__box_render_size + 2):
                self.__render_grid[y][top_right[0]] = 1
        if box.u:
            for x in range(top_left[0], top_right[0] + 1):
                self.__render_grid[top_left[1]][x] = 1
        if box.d:
            for x in range(bot_left[0], bot_left[0] + self.__box_render_size + 1):
                self.__render_grid[bot_left[1]][x] = 1


    def __str__(self) -> str:
        s = ""
        for row in self.__render_grid:
            for char in row:
                s += "•" if char == 1 else " "
            s += "\n"
        return s
    
    def play_move(self, box_coord: Tuple[int, int], line_side: str) -> bool:
        if line_side not in list("lrud"):
            return False
        if not self.__valid_coords(box_coord):
            return False
        
        # return true if this closes a box

        # play a line in both boxes, check if either is closed
        opp_side = DotsAndLines.__Box.opposite_dir[line_side]
        neighbor_coords = self.__coords_in_dir(box_coord, line_side)
        neighbor = self.__neighbor_in_dir(box_coord, line_side)
        box: DotsAndLines.__Box = self.__box_grid[box_coord[1]][box_coord[0]]
        box.fill(line_side)
        self.__render_box(box_coord)
        if neighbor is not None:
            neighbor.fill(opp_side)
            self.__render_box(neighbor_coords)
            return box.filled or neighbor.filled
        return box.filled
        
        
if __name__ == "__main__":
    game = DotsAndLines(4,5,2)
    print(game)
    try:
        while True:
            inp = input("Box coord in form <x,y>: ").split(",")
            dir_ = input("Dir (l/r/u/d): ")
            system("clear")
            x = int(inp[0])
            y = int(inp[1])
            result = game.play_move((x,y), dir_)
            print(game)
            print(result)
    except KeyboardInterrupt:
        pass
