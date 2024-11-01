from __future__ import annotations
from typing import Dict, List, Tuple, Set

class TrieNode:
    def __init__(self):
        self.__to: Dict[str, TrieNode] = {}
        self.__path_sentence_ids: Set[int] = set()
        self.__end_for_id: int | None = None

    def add_sentence(self, sentence: str, sentence_id: int) -> None:
        cur_node: TrieNode = self
        nodes_on_path: List[TrieNode] = []
        for char in sentence:
            nodes_on_path.append(cur_node)
            if char not in cur_node.__to:
                cur_node.__to[char] = TrieNode()
            cur_node = cur_node.__to[char]
        nodes_on_path.append(cur_node)

        if cur_node.__end_for_id is not None:  # its already occupied by the same sentence but diff id
            return
        
        cur_node.__end_for_id = sentence_id
        # retroactively add the path sentence ids for each node on the path
        for node in nodes_on_path:
            node.__path_sentence_ids.add(sentence_id)


    def possible_completions(self, sentence: str) -> List[int]:
        # returns a list of possible completions for the sentence ending at sentence
        cur_node = self
        for char in sentence:
            if char not in cur_node.__to:
                # no completions
                return []
            cur_node = cur_node.__to[char]
        
        return list(cur_node.__path_sentence_ids)
    
    def to(self, char: str) -> TrieNode | None:
        if char in self.__to:
            return self.__to[char]
        return None
    
    def possible_completions_at(self) -> List[int]:
        return list(self.__path_sentence_ids)
            


class Autocomplete:
    def __init__(self, sentences: List[str], hotnesses: List[int]):
        self.__sentence_map: Dict[int, str] = {} # (sentence_id : sentence)
        self.__hotness_map: Dict[int, int] = {} # (sentence_id : hotness)
        self.__query: str = ""
        self.__root: TrieNode = TrieNode()
        self.__node_ptr: TrieNode | None = self.__root

        for i in range(len(sentences)):
            hotness = 0
            if i < len(hotnesses):
                hotness = hotnesses[i]
            
            self.__sentence_map[i] = sentences[i]
            self.__hotness_map[i] = hotness

            self.__root.add_sentence(sentences[i], i)

    def reset(self) -> None:
        self.__query = ""
        self.__node_ptr = self.__root

    def input_(self, char: str) -> List[str]:
        self.__query += char
        if self.__node_ptr is None:
            return []
        
        # go to the next node
        self.__node_ptr = self.__node_ptr.to(char)
        if self.__node_ptr is None:
            return []
        else:
            possibilities = self.__node_ptr.possible_completions_at()
            # sort by hotness
            ranked = [(self.__hotness_map[p], p) for p in possibilities]
            ranked.sort(key=lambda p: p[0])
            return [self.__sentence_map[r[1]] for r in ranked]
        
    @property
    def query(self) -> str:
        return self.__query
        
if __name__ == "__main__":
    sentences = [
        "miami",
        "minecraft",
        "minnesota",
        "minnesota burgers",
        "burgers",
        "miami metro"
    ]
    ac = Autocomplete(sentences, [i for i in range(len(sentences))])
    while True:
        sentence = input()
        completions = []
        for char in sentence:
            completions = ac.input_(char)
        for c in completions:
            print(c)
        ac.reset()
        print()