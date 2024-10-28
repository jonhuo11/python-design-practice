from typing import List

class Line:
    def __init__(self, n: int):
        self.n: int = n
        self.belongs: int | None = None
        self.can_win: bool = True

    def place(self, player: int) -> None:
        if self.belongs is None:
            self.belongs = player
        else:
            if self.belongs != player:
                self.can_win = False
        self.n -= 1
    
    def win(self) -> bool:
        return self.can_win and self.n == 0


class TicTacToe:

    def __init__(self, n: int):

        # list of rows and columns
        # each line has state, either won or in progress
        # if >1 players place things on a row/column then that row/column is blocked from winning
        self.n: int = n
        self.rows: List[Line] = []
        self.cols: List[Line] = []
        self.fwd_diag: Line = Line(n)
        self.bwd_diag: Line = Line(n)

        # fill in rows and cols
        for i in range(n):
            self.rows.append(Line(n))
            self.cols.append(Line(n))

    def is_on_bwd_diag(self, x: int, y: int) -> bool:
        return x + y == self.n - 1

    def is_on_fwd_diag(self, x: int, y: int) -> bool:
        return x == y

    def move(self, row: int, col: int, player: int) -> int:
        # place tile in corresponding row or column
        # first person to place in a row/col claims it
        # 2nd person will set can_win to False
        # if a tile has n = 0 and can_win, then we win
        self.rows[row].place(player)
        self.cols[col].place(player)
        if self.is_on_fwd_diag(col, row):
            self.fwd_diag.place(player)
        if self.is_on_bwd_diag(col, row):
            self.bwd_diag.place(player)

        if self.rows[row].win() or self.cols[col].win() or self.fwd_diag.win() or self.bwd_diag.win():
            return player
        return 0


# # # #
# # # #
# # # #
# # # #


# (3,0) (2,1) (1,2) (0,3)


# Your TicTacToe object will be instantiated and called as such:
# obj = TicTacToe(n)
# param_1 = obj.move(row,col,player)