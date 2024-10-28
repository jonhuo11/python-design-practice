# Container class: linked list type class which has pointer to next most recently used
# Two pointers: one to mru (head of queue), another to lru (the end of queue)
# dict mapping key to container

from typing import Dict

class Container:
    def __init__(self, next: Container | None, prev: Container | None, key: int, value: int):
        self.next:Container|None = next
        self.prev:Container|None = prev
        self.key:int = key
        self.value:int = value

class LRUCache:

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.mru: Container = None
        self.lru: Container = None
        self.mapping: Dict[int, Container] = {} # map of keys to containers

    def make_mru(self, key:int) -> None:
        container = self.mapping[key]

        # if the element is already the mru, dont do anything
        if self.mru == container:
            return

        # reconnect the list around the moved element
        left = container.prev 
        right = container.next
        if left is not None:
            left.next = right
        if right is not None:
            right.prev = left

        # if our element is the last element, update the last element
        if self.lru == container:
            if container.prev is not None:
                container.prev.next = None
            self.lru = container.prev

        # move it to the front as the mru
        if self.mru is not None:
            self.mru.prev = container
        container.next = self.mru
        self.mru = container

    def get(self, key: int) -> int:
        if key not in self.mapping:
            return -1
        # make it the mru
        self.make_mru(key)
        return self.mapping[key].value

    def put(self, key: int, value: int) -> None:
        container:Container|None = None

        # check if key exists
        if key in self.mapping:
            self.mapping[key].value = value
            self.make_mru(key)
        # if not check if the capacity is exceeded or not
        else:
            if len(self.mapping) >= self.capacity:
                # need to remove lru
                if self.lru is not None:
                    del self.mapping[self.lru.key]
                    self.lru = self.lru.prev
                    if self.lru is not None:
                        self.lru.next = None

            # create the key/value and set it as mru
            container = Container(None, None, key, value)
            self.mapping[key] = container
            if self.mru is not None:
                self.mru.prev = container
                container.next = self.mru
            self.mru = container

            # if no items are in the queue, set it as the lru as well
            if len(self.mapping) == 1:
                self.lru = container



# Your LRUCache object will be instantiated and called as such:
# obj = LRUCache(capacity)
# param_1 = obj.get(key)
# obj.put(key,value)