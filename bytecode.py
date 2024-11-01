
from __future__ import annotations
from typing import List, Tuple, Dict

class Memory:
    def __init__(self, size:int):
        self.__size = size
        self.__mem: List[int] = [0] * self.__size

    @property
    def size(self) -> int:
        return self.__size
    
    def set(self, loc: int, val: int) -> None:
        self.__mem[loc] = val

    def get(self, loc: int) -> int:
        return self.__mem[loc]
    

class Runtime:

    # instruction set to command mapping
    __instruction_set: Tuple[str] = (
        "store",
        "load",
        "push",
        "pop",
        "add",
        "sub",
        "vs",
        "jump",
        "write"
    )

    def __init__(self, memory_size_words: int, program: List[str]):
        self.__stack = Memory(memory_size_words)
        self.__registers = Memory(8)
        self.__stack_counter = 0
        self.__program_counter = 0

        # special registers
        self.__reg_test: int = 0  # result of comparison
        
        # load program into memory
        # at the end of program loading, write a special instruction to indicate end of execution
        
        # bytecode format
        # 4 bits are opcode
        # 4 bits are op1
        # 4 bits are op2
        # 4 bits are op3
        max_op_size = 2**4-1
        instruction_pointer = 0
        for line_num, line in enumerate(program):
            split_line = line.strip().split()
            command = Runtime.__instruction_set.index(split_line[0])
            op1 = int(split_line[1]) if len(split_line) >= 2 else 0
            op2 = int(split_line[2]) if len(split_line) >= 3 else 0
            op3 = int(split_line[3]) if len(split_line) >= 4 else 0
            if op1 > max_op_size or op2 > max_op_size or op3 > max_op_size:
                raise Exception("op exceeeds max op size", max_op_size)
            print("command", op1, op2, op3)
            for op in (op1, op2, op3):
                command <<= 4
                command |= op
            self.__stack.set(instruction_pointer, command)
            instruction_pointer += 1
        self.__stack.set(instruction_pointer, (max_op_size) << 12) # special command to indicate end
        self.__stack_counter = instruction_pointer + 1
    
    def step(self) -> None:
        # do stuff based on the opcode
        bytecode = self.__stack.get(self.__program_counter)
        opcode = (bytecode >> 12) & 0b1111
        op1 = (bytecode >> 8) & 0b1111
        op2 = (bytecode >> 4) & 0b1111
        op3 = (bytecode) & 0b1111
        opname = Runtime.__instruction_set[opcode]

        # format should be <cmd> <reg1> <reg2> <dest>
        # <cmd> <val> <dest>

        if opname == "write": # write val register
            self.__registers.set(op2, op1)
        elif opname == "push": # push reg1
            self.__stack.set(self.__stack_counter, self.__registers.get(op1))
            self.__stack_counter += 1
        else:
            raise Exception("Op not implemented", opcode)

        self.__program_counter += 1

    def __str__(self) -> str:
        o = ""
        o += "===REGISTERS===\n"
        for i in range(0, self.__registers.size):
            word = self.__registers.get(i)
            o += bin(word)[2:] + "\n"
        o += "===STACK===\n"
        for i in range(0, self.__stack.size):
            word = self.__stack.get(i)
            o += bin(word)[2:] + "\n"
        return o
        

if __name__ == "__main__":
    program = """push 0 1
write 5 2
"""
    rt = Runtime(16, program.splitlines())
    rt.step()
    rt.step()
    print(rt)