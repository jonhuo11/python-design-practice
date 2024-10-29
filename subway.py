from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass
class TripData:
    total_time: int = 0  # total amount of time spent across all trips
    total_trips: int = 0  # total number of this exact trip made

    @property
    def average(self):
        return self.total_time / self.total_trips

class UndergroundSystem:

    def __init__(self):
        # customer ids mapped to check in times + station
        # when the customer checks out, we calculate the total trip time and record it in the trip data

        self.__check_ins: Dict[int, Tuple[int, str]] = {} # (time, station in)
        self.__trip_data: Dict[Tuple[str, str], TripData] = {} # (station A, station B): TripData


    def checkIn(self, id: int, stationName: str, t: int) -> None:
        self.__check_ins[id] = (t, stationName)

    def checkOut(self, id: int, stationName: str, t: int) -> None:
        check_in_data = self.__check_ins[id]
        trip_time = t - check_in_data[0]
        source = check_in_data[1]
        trip = (source, stationName)
        if trip not in self.__trip_data:
            self.__trip_data[trip] = TripData()
        self.__trip_data[trip].total_time += trip_time
        self.__trip_data[trip].total_trips += 1

    def getAverageTime(self, startStation: str, endStation: str) -> float:
        trip = (startStation, endStation)
        return self.__trip_data[trip].average


# Your UndergroundSystem object will be instantiated and called as such:
# obj = UndergroundSystem()
# obj.checkIn(id,stationName,t)
# obj.checkOut(id,stationName,t)
# param_3 = obj.getAverageTime(startStation,endStation)