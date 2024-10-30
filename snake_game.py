from typing import List, Tuple, Deque, Set
from collections import deque

class SnakeGame:

    def __init__(self, width: int, height: int, food: List[List[int]]):
        self.__grid_size: Tuple[int, int] = (width, height)
        self.__food: List[List[int]] = food # (r, c)
        self.__food_i: int = 0
        self.__score: int = 0
        self.__snake_set: Set[Tuple[int,int]] = set()
        self.__snake: Deque[Tuple[int,int]] = deque()

        self.__snake.append((0,0))
        self.__snake_set.add((0,0))


    def move(self, direction: str) -> int:
        move_vec = [0,0]
        if direction == "R":
            move_vec = [1,0]
        elif direction == "L":
            move_vec = [-1, 0]
        elif direction == "U":
            move_vec = [0,-1]
        else: # D
            move_vec = [0,1]

        self.__snake.append((self.__snake[-1][0] + move_vec[0], self.__snake[-1][1] + move_vec[1]))
        old_tail = self.__snake.popleft()
        self.__snake_set.remove(old_tail)
        head = self.__snake[-1]

        # if head collides with an occupied cell or the wall, die
        if head[0] < 0 or head[0] >= self.__grid_size[0] or head[1] < 0 or head[1] >= self.__grid_size[1]:
            return -1

        if head in self.__snake_set:
            return -1
        self.__snake_set.add(head)

        # check for food
        if self.__food_i < len(self.__food):
            cur_food = self.__food[self.__food_i]
            if head[0] == cur_food[1] and head[1] == cur_food[0]:
                self.__score += 1
                self.__food_i += 1
                self.__snake.appendleft(old_tail)
                self.__snake_set.add(old_tail)

        return self.__score


# Your SnakeGame object will be instantiated and called as such:
# obj = SnakeGame(width, height, food)
# param_1 = obj.move(direction)