from __future__ import annotations
from typing import Dict, List, Tuple

import heapq

class StockExchange:
    class _User:
        pass

    class _StockOrder:
        def __init__(self, price: int, amount: int):
            self.price = price
            self.amount = amount

        def __lt__(self, other: StockExchange._StockOrder) -> bool:
            return self.price < other.price
        
    class _Record:
        def __init__(self, ticket: str, sold_for: int, amount: int):
            self.__ticket = ticket
            self.__sold_for = sold_for
            self.__amount = amount

        def __str__(self) -> str:
            return f"Sold {self.__amount} shares of {self.__ticket} at {self.__sold_for} per share (total {self.__sold_for * self.__amount})"

    def __init__(self):
        self.__ticket_buy: Dict[str, List[StockExchange._StockOrder]] = {}
        self.__ticket_sell: Dict[str, List[StockExchange._StockOrder]] = {}
        self.__records: List[StockExchange._Record] = []

    def __str__(self) -> str:
        o = ""
        for record in self.__records:
            o += str(record) + "\n"
        return o

    def __match(self, ticket: str) -> bool:
        if ticket not in self.__ticket_buy or ticket not in self.__ticket_sell:
            return False
        if len(self.__ticket_buy[ticket]) == 0 or len(self.__ticket_sell[ticket]) == 0:
            return False
        
        # check if max buy price is greater than minimum sell price
        best_buy = self.__ticket_buy[ticket][0]
        best_sell = self.__ticket_sell[ticket][0]
        if -best_buy.price >= best_sell.price:
            # match
            amount_sold = min(best_buy.amount, best_sell.amount)
            best_buy.amount -= amount_sold
            best_sell.amount -= amount_sold

            # remove either if zero
            if best_buy.amount <= 0:
                heapq.heappop(self.__ticket_buy[ticket])
            if best_sell.amount <= 0:
                heapq.heappop(self.__ticket_sell[ticket])

            # sale happens at lowest selling price
            self.__records.append(StockExchange._Record(ticket, best_sell.price, amount_sold))
            return True
        return False
            

    def buy(self, ticket: str, buy_price: int, amount: int) -> None:
        if ticket not in self.__ticket_buy:
            self.__ticket_buy[ticket] = []

        order = StockExchange._StockOrder(-buy_price, amount)
        heapq.heappush(self.__ticket_buy[ticket], order)

        while self.__match(ticket): pass

    def sell(self, ticket: str, sell_price: int, amount: int) -> None:
        if ticket not in self.__ticket_sell:
            self.__ticket_sell[ticket] = []

        order = StockExchange._StockOrder(sell_price, amount)
        heapq.heappush(self.__ticket_sell[ticket], order)

        while self.__match(ticket): pass

if __name__ == "__main__":
    se = StockExchange()
    se.buy("MT", 100, 2)
    se.buy("MT", 200, 1)
    se.sell("MT", 201, 10)
    se.sell("MT", 10, 1)
    se.sell("MT", 99, 1)
    se.sell("MT", 99, 1)
    se.buy("MT", 2000, 11)

    print(se)