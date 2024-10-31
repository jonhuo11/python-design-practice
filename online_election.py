from typing import List, Dict, Tuple
from bisect import bisect_right

class TopVotedCandidate:

    def __init__(self, persons: List[int], times: List[int]):
        
        # have a running dict mapping people to the number of votes they have
        # at each time we make a record of the leading candidate
        # put this record in an array of tuples (time, leading candidate)
        # to find the leading candidate at time t, binary search on the array

        self.__vote_record: Dict[int, int] = {} # (candidate, votes)
        self.__leading: List[Tuple[int, int]] = [] # (time, leading candidate)

        leading_candidate_id = None
        for i in range(len(persons)):
            if persons[i] not in self.__vote_record:
                self.__vote_record[persons[i]] = 0
            self.__vote_record[persons[i]] += 1
            if leading_candidate_id is None or self.__vote_record[persons[i]] >= self.__vote_record(leading_candidate_id):
                leading_candidate_id = persons[i]
                self.__leading.append((times[i], leading_candidate_id))


    def q(self, t: int) -> int:
        return self.__leading[bisect_right(self.__leading, (t, )) - 1][1]
        


# Your TopVotedCandidate object will be instantiated and called as such:
# obj = TopVotedCandidate(persons, times)
# param_1 = obj.q(t)