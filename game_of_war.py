from __future__ import annotations
from dataclasses import dataclass, field
from random import randint
from enum import Enum
from typing import List

class CardSuits(Enum):
    HEART = 0
    SPADE = 1
    CLUB = 2
    DIAMOND = 3


@dataclass(frozen=True, order=True)
class Card:
    value: int
    suit: CardSuits = field(compare=False)

def generate_deck() -> List[Card]:
    deck: List[Card] = []
    for suit in CardSuits:
        for i in range(len("23456789xjqka")):
            deck.append(Card(i, suit))
    return deck

class GameOfWar:
    def __init__(self):
        self.__p0_deck: List[Card] = []
        self.__p1_deck: List[Card] = []
        self.__game_over: bool = False

        # shuffle the cards and split them in two
        deck = generate_deck()
        for _ in range(100):
            random_swap_i = randint(0,51)
            deck[0], deck[random_swap_i] = deck[random_swap_i], deck[0]

        for i in range(len(deck)):
            if i % 2 == 0:
                self.__p0_deck.append(deck[i])
            else:
                self.__p1_deck.append(deck[i])


    def __battle(self) -> int:
        # repeatedly draw cards until someone wins
        battle_cards: List[Card] = []
        while len(self.__p0_deck) > 0 and len(self.__p1_deck) > 0:
            p0_top = self.__p0_deck.pop()
            p1_top = self.__p1_deck.pop()
            battle_cards.append(p0_top)
            battle_cards.append(p1_top)
            print(f"War! Player 0 plays {p0_top} and Player 1 plays {p1_top}.")

            if p0_top > p1_top:
                self.__p0_deck = battle_cards + self.__p0_deck
                return 0
            elif p1_top > p0_top:
                self.__p1_deck = battle_cards + self.__p1_deck
                return 1
            
            # if theres no victory, then draw 3 cards from each deck
            # if tie, return -1
            if len(self.__p0_deck) < 3 and len(self.__p1_deck) < 3:
                return -1
            elif len(self.__p0_deck) < 3:
                return 1
            elif len(self.__p1_deck) < 3:
                return 0
            
            print("Drawing 3 cards from each player's deck...")
            for _ in range(3):
                battle_cards.append(self.__p0_deck.pop())
                battle_cards.append(self.__p1_deck.pop())
        if len(self.__p0_deck) == 0 and len(self.__p1_deck) == 0:
            return -1
        elif len(self.__p0_deck) == 0:
            return 1
        else:
            return 0
        
    def play(self) -> None:
        print()
        if self.__game_over:
            print("The game has ended.")
            return
        
        print(f"Player 0 has {len(self.__p0_deck)} cards and Player 1 has {len(self.__p1_deck)} cards")
        print(f"Playing...")
        winner = self.__battle()
        if winner == -1: # tie
            print("Tie! Both players have less than 3 cards remaining")
            return
        
        print(f"Player {winner} wins the battle!")
        if len(self.__p0_deck) == 0:
            print(f"Player 1 wins the game!")
            self.__game_over = True
            return
        elif len(self.__p1_deck) == 0:
            print(f"Player 0 wins the game!")
            self.__game_over = True
            return


if __name__ == "__main__":
    gow = GameOfWar()
    while True:
        input()
        gow.play()