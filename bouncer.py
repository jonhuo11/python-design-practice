import curses
import time
import math

class Ball:
    def __init__(self, screen_width: int, screen_height: int):
        self.__pos = [0,0]
        self.__spd = [0,0]
        self.__force = [0,0]
        self.__screen_width = screen_width
        self.__screen_height = screen_height
    
    def __move(self) -> None:

        self.__spd[0] += self.__force[0]
        self.__spd[1] += self.__force[1]

        self.__pos[0] += self.__spd[0]
        self.__pos[0] %= self.__screen_width

        next_y = self.__pos[1] + self.__spd[1]
        if next_y >= self.__screen_height:
            self.__pos[1] = self.__screen_height - (next_y % self.__screen_height)
            self.__spd[1] *= -0.9
        else:
            self.__pos[1] = next_y

        self.__force[0], self.__force[1] = 0, 0


    def add_force(self, force) -> None:
        self.__force[0] += force[0]
        self.__force[1] += force[1]

    def clear(self, stdscr: curses.window) -> None:
        if self.__pos[1] >= 0 and self.__pos[1] < self.__screen_height:
            stdscr.addch(math.floor(self.__pos[1]), self.__pos[0], " ")

    def draw(self, stdscr: curses.window) -> None:
        self.clear(stdscr)
        self.add_force([0,1])
        self.__move()

        if self.__pos[1] >= 0 and self.__pos[1] < self.__screen_height:
            stdscr.addch(math.floor(self.__pos[1]), self.__pos[0], "O")
    

class BouncingBar:
    def __init__(self, width: int, bounce_width: int, ypos: int):
        self.__ypos = ypos
        self.__l = 0
        self.__r = width
        self.__bounce_width = bounce_width
        self.__direction = 1

    def __move(self) -> None:
        if self.__r >= self.__bounce_width - 1:
            self.__direction = 0
        elif self.__l <= 0:
            self.__direction = 1

        if self.__direction == 1:
            self.__l += 1
            self.__r += 1
        else:
            self.__l -= 1
            self.__r -= 1

    def clear(self, stdscr: curses.window) -> None:
        for i in range(self.__l, self.__r + 1):
            stdscr.addch(self.__ypos, i, " ")

    def draw(self, stdscr: curses.window) -> None:
        self.clear(stdscr)
        self.__move()
        for i in range(self.__l, self.__r + 1):
            stdscr.addch(self.__ypos, i, "<" if self.__direction == 0 else ">")


def main(stdscr: curses.window):
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(100)

    fps = 300
    fdur = 1.0/fps

    height, width = stdscr.getmaxyx()
    bar = BouncingBar(width // 3, width, height // 2)
    ball = Ball(width, height)
    ball.add_force([2,0])

    try:
        while stdscr.getch() != ord("q"):
            time.sleep(fdur)
            ball.draw(stdscr)
            bar.draw(stdscr)
            stdscr.refresh()
    except KeyboardInterrupt:
        return
    
curses.wrapper(main)