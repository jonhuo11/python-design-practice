
from typing import List, Tuple, Dict



class CodeTree:

    class __CodeNode:
        def __init__(self, line: int):
            self.line: int = line
            self.lines: List[str | CodeTree.__CodeNode] = []

        def expanded(self) -> str:
            return "\n".join(self.lines)
        
        def collapsed(self) -> str:
            return self.lines[0] + "\n" + self.lines[-1]
    

    def __init__(self, code: str):
        self.__lines = code.splitlines()
        self.__brace_map = CodeTree.__get_brace_map(self.__lines)
        self.__expanded_map: Dict[int, bool] = {} # line num : expanded?

        # build expander and closer
        # walk the brace map, each time we find a opening line, we create a new node and enter it
        # closing line we close the node and pop to the previous level
        self.__root = CodeTree.__CodeNode(0)
        stack: List[CodeTree.__CodeNode] = [self.__root]
        for line_number, line in enumerate(self.__lines):
            if stack[-1].line in self.__brace_map and self.__brace_map[stack[-1].line] == line_number: # in a closing brace for the current one
                # add the line to the code node
                stack[-1].lines.append(line)
                # pop the current node from the stack
                stack.pop()
            elif line_number not in self.__brace_map: # just a regular line
                stack[-1].lines.append(line)
            else:
                # this is an opening brace line, push a new node
                new_node = CodeTree.__CodeNode(line_number)
                new_node.lines.append(line)
                stack[-1].lines.append(new_node)
                stack.append(new_node)
                self.__expanded_map[line_number] = True



    def toggle(self, line_number: int) -> None:
        # if the line is not a code node, do nothing
        # if it is, mark it as closed
        if line_number not in self.__expanded_map:
            return
        self.__expanded_map[line_number] = not self.__expanded_map[line_number]
        

    def display(self) -> str:
        out = ""
        def dfs(node: CodeTree.__CodeNode):
            nonlocal out
            for line in node.lines:
                if isinstance(line, CodeTree.__CodeNode):
                    if self.__expanded_map[line.line]:
                        dfs(line)
                    else:
                        out += line.collapsed() + "\n"
                else:
                    out += line + "\n"
        dfs(self.__root)
        return out
            

    @classmethod
    def __validator(cls, lines: List[str]) -> bool:
        counter = 0
        #print(lines)
        for line in lines:
            for char in line:
                if char == "{":
                    counter += 1
                elif char == "}":
                    counter -= 1
                
                if counter < 0:
                    return False
        return counter == 0


    @classmethod
    def __get_brace_map(cls, lines: List[str]) -> Dict[int, int]:
        if not cls.__validator(lines):
            raise Exception("Mismatch braces")
        brace_map: Dict[int, int] = {}
        open_stack: List[int] = [] # (line)
        for line_number, line in enumerate(lines):
            line = line.strip()
            start = line[0]
            end = line[-1]
            if end == "{" and start == "}":
                raise Exception("Not supported to have open and closed braces on the same line")
            if end == "{":
                open_stack.append(line_number)
            if start == "}":
                # pop the stored line number and record in the brace map
                start_line_number = open_stack.pop()
                brace_map[start_line_number] = line_number
        return brace_map




if __name__ == "__main__":
    test_case = """if (something) {
    if (something) {
        print("hi")
        while (true) {
            print("do anything")
        }
        print("bye")
    } 
    print("hi")
    if (something) {
    } 
    else {
        print("final hi")
    }
}
"""
    ct = CodeTree(test_case)
    print(ct.display())
    print()
    ct.toggle(0)
    print(ct.display())
    ct.toggle(0)
    ct.toggle(3)
    print(ct.display())
    ct.toggle(0)
    print(ct.display())
    ct.toggle(0)
    print(ct.display())