from typing import Dict, Deque, Tuple, Set
from collections import deque

class Converter:

    def __init__(self):
        self.mappings: Dict[str, Dict[str, float]] = {}

    def add_fact(self, unit_a: str, unit_b: str, ratio: float) -> None:
        if unit_a not in self.mappings:
            self.mappings[unit_a] = {}
        if unit_b not in self.mappings:
            self.mappings[unit_b] = {}
        self.mappings[unit_a][unit_b] = ratio
        self.mappings[unit_b][unit_a] = 1 / ratio

    def convert(self, amount_in_unit_a: str, unit_a: str, unit_b: str) -> float:
        # outputs the amount in unit_b
        # perform a bfs to find the shortest path from a to b
        # return multiplier * amount

        if unit_a not in self.mappings or unit_b not in self.mappings:
            raise Exception("Unit not found in converter")

        queue: Deque[Tuple[str, float]] = deque() # (current unit, conversion ratio currently)
        queue.append((unit_a, 1))
        visited: Set[str] = set()
        while queue:
            if queue[0][0] == unit_b:
                break
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)

            adjacent_map = self.mappings[current[0]]
            for adj_unit in adjacent_map:
                multiplier = adjacent_map[adj_unit]
                queue.append((adj_unit, current[1] * multiplier))

        final_ratio = queue[0][1]
        return amount_in_unit_a * final_ratio
    


if __name__ == "__main__":
    converter = Converter()
    converter.add_fact("m", "cm", 100)
    converter.add_fact("m", "km", 1/1000)
    converter.add_fact("m", "in", 39.37)
    converter.add_fact("m", "ft", 3.28)

    print(converter.convert(10.5, "in", "cm"))