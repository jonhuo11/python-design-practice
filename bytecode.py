
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
    # maximum of 2**4 - 1 instructions
    __instruction_set: Tuple[str] = (
        "store",
        "load",
        "push",
        "pop",
        "add",
        "sub",
        "vs",
        "jump",
        "write",
        "where",
    )

    __max_op_size = 2**4-1
    __end_program_opcode = __max_op_size << 12

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
        instruction_pointer = 0
        for _, line in enumerate(program):
            split_line = line.strip().split()
            command = Runtime.__instruction_set.index(split_line[0])
            op1 = int(split_line[1]) if len(split_line) >= 2 else 0
            op2 = int(split_line[2]) if len(split_line) >= 3 else 0
            op3 = int(split_line[3]) if len(split_line) >= 4 else 0
            if op1 > Runtime.__max_op_size or op2 > Runtime.__max_op_size or op3 > Runtime.__max_op_size:
                raise Exception("op exceeeds max op size", Runtime.__max_op_size)
            for op in (op1, op2, op3):
                command <<= 4
                command |= op
            self.__stack.set(instruction_pointer, command)
            instruction_pointer += 1
        self.__stack.set(instruction_pointer, Runtime.__end_program_opcode) # special command to indicate end
        self.__stack_counter = instruction_pointer + 1
    
    def step(self) -> None:
        bytecode = self.__stack.get(self.__program_counter)
        if bytecode == Runtime.__end_program_opcode: 
            return
        mask = 0xF
        opcode = (bytecode >> 12) & mask
        op1 = (bytecode >> 8) & mask
        op2 = (bytecode >> 4) & mask
        op3 = (bytecode) & mask
        opname = Runtime.__instruction_set[opcode]

        # format should be <cmd> <reg1> <reg2> <dest>
        # <cmd> <val> <dest>

        # TODO: prevent stack overflow and prevent popping into instruction space
        if opname == "write": # write val register
            self.__registers.set(op2, op1)
        elif opname == "push": # push reg1 
            self.__stack.set(self.__stack_counter, self.__registers.get(op1))
            self.__stack_counter += 1
        elif opname == "pop": # pop reg1
            self.__stack_counter -= 1
            self.__registers.set(op1, self.__stack.get(self.__stack_counter))
        elif opname == "store": # store reg1 destreg
            self.__stack.set(op2, self.__registers.get(op1))
        elif opname == "load": # load memoryloc destreg
            self.__registers.set(op2, self.__stack.get(self.__registers.get(op1)))
        elif opname == "add": # add reg1 reg2 dest
            sum_ = self.__registers.get(op1) + self.__registers.get(op2)
            self.__registers.set(op3, sum_)
        elif opname == "where": # where dest
            # writes the stack pointer to the destination
            self.__registers.set(op1, self.__stack_counter)
        elif opname == "jump": # jump by
            self.__program_counter += self.__registers.get(op1)
            return
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

    program = """write 8 0
push 0
write 5 2
write 2 3
add 2 3 4
where 1
pop 1
"""
    rt = Runtime(16, program.splitlines())
    try:
        while True:
            input()
            rt.step()
            print(rt)
    except KeyboardInterrupt:
        print("done")