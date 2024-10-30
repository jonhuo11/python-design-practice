from typing import Dict, List
from bisect import bisect_right

class HitCounter:

    def __init__(self):
        self.__counter: Dict[int, int] = {}

    def hit(self, timestamp: int) -> None:
        if timestamp not in self.__counter:
            self.__counter[timestamp] = 0
        self.__counter[timestamp] += 1

    def getHits(self, timestamp: int) -> int:
        # get list of keys
        # binary search for where (timestamp - 300) should occur
        # iterate forward on keys until key > timestamp
        keys = list(self.__counter.keys())
        key_i = bisect_right(keys, timestamp - 300)
        total_hits = 0
        while key_i < len(keys) and keys[key_i] != timestamp:
            total_hits += self.__counter[keys[key_i]]
            key_i += 1
        if timestamp in self.__counter:
            total_hits += self.__counter[timestamp]
        return total_hits



# Your HitCounter object will be instantiated and called as such:
# obj = HitCounter()
# obj.hit(timestamp)
# param_2 = obj.getHits(timestamp)