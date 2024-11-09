from __future__ import annotations
from typing import List


class Calculator:
    def __init__(self):
        self.__answer: int = 0

    @classmethod
    def __operate(cls, operator, op1, op2) -> int:
        if operator == "+":
            return op1 + op2
        elif operator == "-":
            return op1 - op2
        elif operator == "*":
            return op1 * op2
        elif operator == "/":
            return op1//op2
        else:
            raise Exception()
    
    
    @classmethod
    def __evaluate_operations_on_stack(cls, stack: List[str|int], operators: List[str]) -> List[str|int]:
        i = 0
        expr_evaluated = []
        while i < len(stack):
            if stack[i] in operators:
                operator = stack[i]
                left = expr_evaluated[-1]
                right = stack[i + 1]
                expr_evaluated[-1] = Calculator.__operate(operator, left, right)
                i += 2
            else:
                expr_evaluated.append(stack[i])
                i += 1
        return expr_evaluated

    @classmethod
    def __evaluate(cls, tokens: List[str|int]) -> int:
        
        # + - * / ( ) num
        # - num
        # num op num
        # ( ... )

        # (1 + 1 - (2 * (2 - 1) + 1) + 2)
        # (1 + 1) * (2 + 2)
        expr = []
        # find and eval parenthesis
        i = 0
        while i < len(tokens):
            if tokens[i] == "(":
                counter = 1
                end_i = i
                for j in range(i + 1, len(tokens)):
                    if tokens[j] == "(":
                        counter += 1
                    elif tokens[j] == ")":
                        counter -= 1
                    
                    end_i = j
                    if counter == 0:
                        break
                evaluated_parenthesis = Calculator.__evaluate(tokens[i+1:end_i])
                expr.append(evaluated_parenthesis)
                i = end_i + 1
            else:
                expr.append(tokens[i])
                i += 1

        mult_div_evaluated = Calculator.__evaluate_operations_on_stack(expr, ["*", "/"])
        add_sub_evaluated = Calculator.__evaluate_operations_on_stack(mult_div_evaluated, ["+", "-"])
        return int(add_sub_evaluated[0])
    
    @classmethod
    def __parse(cls, expression: str) -> List[str|int]:
        # parse without checking validity
        tokens: List[str|int] = []
        cur_token: str = ""
        for ch in expression:
            if ch in "0123456789":
                cur_token += ch
            elif ch in "+-*/":
                if len(cur_token):
                    tokens.append(int(cur_token))
                    cur_token = ""
                tokens.append(ch)
            elif ch in "()":
                if len(cur_token):
                    tokens.append(int(cur_token))
                    cur_token = ""
                tokens.append(ch)     
        if len(cur_token):
            tokens.append(int(cur_token))
        return tokens



    def calculate(self, expression: str) -> int:
        
        self.__answer = Calculator.__evaluate(Calculator.__parse(expression))
        return self.__answer


if __name__ == "__main__":

    calc = Calculator()
    while True:
        print(calc.calculate(input("Enter expression: ")))

