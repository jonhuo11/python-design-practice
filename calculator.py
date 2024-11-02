from __future__ import annotations
from typing import List


class Calculator:
    def __init__(self):
        self.__answer: int = 0

    def __evaluate(self, tokens: List[str]) -> int:
        
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
                for j in range(i + 1, len(tokens)):
                    if tokens[j] == "(":
                        counter += 1
                    elif tokens[j] == ")":
                        counter -= 1
                    
                    if counter == 0:
                        i = j + 1
                        break
                evaluated_parenthesis = str(self.__evaluate(tokens[i:j]))
                expr.append(evaluated_parenthesis)
            else:
                expr.append(tokens[i])
                i += 1

        # evaluate mult/div operations, assuming theres no parenthesis
        # 1 * 1 * 1
        # 1
        i = 0
        expr_no_multdiv = []
        while i < len(expr):
            if expr[i] == "*" or expr[i] == "/":
                left = expr_no_multdiv[-1]
                right = expr[i + 1]
                result = 1
                if expr[i] == "*":
                    result = int(left) * int(right)
                else:
                    result = int(left) // int(right)
                expr_no_multdiv[-1] = result
                i += 2
            else:
                expr_no_multdiv.append(expr[i])
                i += 1

        i = 0
        expr_evaluated = []
        while i < len(expr_no_multdiv):
            if expr_no_multdiv[i] == "+" or expr_no_multdiv[i] == "-":
                left = expr_evaluated[-1]
                right = expr[i + 1]
                result = 1
                if expr_no_multdiv[i] == "+":
                    result = int(left) + int(right)
                else:
                    result = int(left) - int(right)
                expr_evaluated[-1] = result
                i += 2
            else:
                expr_evaluated.append(expr_no_multdiv[i])
                i += 1
        

        return expr_evaluated[0]
    

    def __parse(self, expression: str) -> List[str]:
        pass


    def calculate(self, expression: str) -> int:
        
        self.__answer = self.__evaluate(self.__parse(expression))
        return self.__answer
