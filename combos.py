from __future__ import annotations
from typing import Dict, Tuple, List

class TrieNode:
    def __init__(self):
        self.to: Dict[str, TrieNode] = {} 
        self.label: str | None = None
    
    @property
    def end(self) -> bool:
        return self.label is not None

class ComboRegister:

    def __init__(self):
        self.__trie_root: TrieNode = TrieNode()
        self.__node: TrieNode | None = self.__trie_root

    def register_combo(self, combo_name: str, combo: str) -> None:
        cur_node: TrieNode = self.__trie_root
        for key in combo:
            if key not in cur_node.to:
                cur_node.to[key] = TrieNode()
            cur_node = cur_node.to[key]
        cur_node.label = combo_name
    
    def new_sequence(self) -> None:
        self.__node = self.__trie_root

    def key_press(self, key: str) -> str | None:
        # returns the combo name if a combo is detected, otherwise dont return anything
        if self.__node is None:
            return None

        if key in self.__node.to:
            self.__node = self.__node.to[key]
            if self.__node.end:
                return self.__node.label
        else:
            self.__node = None
        return None
    

if __name__ == "__main__":
    register = ComboRegister()
    combos = [
        ("mega punch", "udlr"),
        ("super slam", "uuddllrr"),
        ("laser beam", "uudl"),
        ("mega laser beam", "uudluudl"),
        ("ultra laser beam", "uudluurr"),
        ("uppercut", "lrud"),
        ("super uppercut", "lrudddu")
    ]
    for combo in combos:
        register.register_combo(combo[0], combo[1])
    while True:
        key = input("Press a key: ")
        combo_completed = register.key_press(key[0])
        if combo_completed is not None:
            print(combo_completed)
        
