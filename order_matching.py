from typing import List, Tuple, Dict, TypeAlias
from enum import Enum
import heapq

Order: TypeAlias = Tuple[float, int, int] # (price, time, id)
OrderBook: TypeAlias = Dict[str, List[Order]]


class StockExchange:
    class OrderType(Enum):
        BUY = 1
        SELL = 2
    def __init__(self):
        self.__id_counter = 1
        self.__sell_book: OrderBook = {}
        self.__buy_book: OrderBook = {}
        self.__order_amounts: Dict[int, int] = {} # id : amount left

    def add_order(self, type_: OrderType, ticket: str, price: float, amount: int, time: int) -> None:
        # add order to the appropriate book
        book = self.__sell_book if type_ == StockExchange.OrderType.SELL else self.__buy_book
        if book == self.__buy_book:
            price *= -1  # to make maxheap

        if ticket not in book:
            book[ticket] = []

        heapq.heappush(
            book[ticket],
            (price, time, self.__id_counter)
        )

        # record amount in the order amounts
        if self.__id_counter not in self.__order_amounts:
            self.__order_amounts[self.__id_counter] = {}
        self.__order_amounts[self.__id_counter] = amount

        self.__id_counter += 1

        # check if any orders can be matched
        self.try_match_order(ticket)

    def try_match_order(self, ticket: str) -> None:
        if ticket not in self.__buy_book or ticket not in self.__sell_book:
            return
        if len(self.__buy_book[ticket]) == 0 or len(self.__sell_book[ticket]) == 0:
            return
        
        # at least 1 order for this ticket in buy and sell heaps
        # if the max buy order satisfies the min sell order (buy >= sell)
        # then subtract appropriate amounts and output

        max_buy = self.__buy_book[ticket][0]
        min_sell = self.__sell_book[ticket][0]
        if -max_buy[0] >= min_sell[0]:
            # subtract the min of sell and buy from both
            sell_id = min_sell[2]
            buy_id = max_buy[2]
            amount_sold = min(self.__order_amounts[sell_id], self.__order_amounts[buy_id])
            self.__order_amounts[sell_id] -= amount_sold
            self.__order_amounts[buy_id] -= amount_sold

            # print the order matched
            print(f"[{max(max_buy[1], min_sell[1])}] Sold {amount_sold} shares of {ticket} at {-max_buy[0]} (sell id {sell_id}, buy id {buy_id})")

            # remove empty from heaps and orders
            if self.__order_amounts[sell_id] <= 0:
                del self.__order_amounts[sell_id]
                heapq.heappop(self.__sell_book[ticket])
            if self.__order_amounts[buy_id] <= 0:
                del self.__order_amounts[buy_id]
                heapq.heappop(self.__buy_book[ticket])
            
            self.try_match_order(ticket)
            

if __name__ == "__main__":
    exchange = StockExchange()
    exchange.add_order(StockExchange.OrderType.BUY, "GOOG", 10.0, 20, 5)
    exchange.add_order(StockExchange.OrderType.BUY, "GOOG", 20.0, 1, 10)
    exchange.add_order(StockExchange.OrderType.BUY, "GOOG", 30.0, 2, 20)
    exchange.add_order(StockExchange.OrderType.SELL, "GOOG", 100, 1, 21)
    exchange.add_order(StockExchange.OrderType.SELL, "GOOG", 5, 21, 22)
    
    