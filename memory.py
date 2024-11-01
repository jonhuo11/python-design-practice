from __future__ import annotations

class Block:
    def __init__(self, start: int, end: int, next: Block | None = None):
        self.start = start
        self.end = end # not inclusive
        self.next: Block | None = next
        self.id: int | None = None

    @property
    def is_alloc(self) -> bool:
        return self.id is not None

    @property
    def size(self) -> int:
        return self.end - self.start 


class Memory:
    def __init__(self, max_size: int):
        self.__base: Block = Block(0, max_size)

    def __str__(self) -> str:
        o = ""
        cur_block = self.__base
        while cur_block is not None:
            o += f"({cur_block.id if cur_block.id is not None else "_"}[{cur_block.start},{cur_block.end}]) -> " 
            cur_block = cur_block.next
        return o

    def alloc(self, id_: int, size: int) -> int:
        # returns index of block allocated or -1 if cant find

        # loop through blocks and find the first free block that is big enough
        cur_block: Block | None = self.__base
        while cur_block is not None:
            if cur_block.size >= size and not cur_block.is_alloc:
                break
            cur_block = cur_block.next


        # edge case: if no blocks found, return -1
        if cur_block is None:
            return -1

        # guaranteed the block is big enough and suitable
        # split that block into two blocks
        # the current block becomes the alloc size
        # the new block gets the remaining size
        # the new block's next is the old blocks next
        new_block = Block(
            next=cur_block.next,
            start=(cur_block.start + size),
            end=cur_block.end
        )
        cur_block.next = new_block
        cur_block.end = new_block.start
        # set the current block as allocated, and set the id
        cur_block.id = id_

        return cur_block.start
    

    def free(self, id_: int) -> int:
        # frees all blocks with id, and returns total space freed
        total_freed = 0
        cur_block = self.__base
        while cur_block is not None:
            if (cur_block.id == id_) or not cur_block.is_alloc:
                # start freeing contiguous blocks
                end_block = cur_block
                if end_block.id == id_:
                    total_freed += end_block.size
                while end_block.next is not None and (end_block.next.id == id_ or ( not end_block.next.is_alloc )):
                    if end_block.next.id == id_:
                        total_freed += end_block.next.size
                    end_block = end_block.next
                
                # set current blocks end to the end of the end block
                # and remove all blocks in between by setting pointer to skip

                cur_block.next = end_block.next
                cur_block.end = end_block.end
                cur_block.id = None
            
            cur_block = cur_block.next

        # run it again 
        return total_freed
    

if __name__ == "__main__":
    memory = Memory(100)

    memory.alloc(1,1)
    memory.alloc(2,1)
    memory.alloc(3,1)
    print(memory.free(2))