def stoi(a: str) -> int:
    return ord(a) - ord('0')


def add(a: str, b: str) -> str:
    # pad the shorter strings with leading 0s
    # iterate from LTR, with a carry num
    # potentially add carry to front at the end
    longer = a
    shorter = a
    if len(b) != len(a):
        if len(b) < len(a):
            shorter = b
        else:
            longer = b
    else:
        shorter = b
    
    shorter = ("0" * (len(longer) - len(shorter))) + shorter

    output: str = ""
    n = len(shorter)
    carry: int = 0
    for i in range(n - 1, -1, -1):
        sum_ = stoi(shorter[i]) + stoi(longer[i]) + carry
        carry = sum_ // 10
        sum_ = sum_ % 10
        output = str(sum_) + output
    if carry != 0:
        output = str(carry) + output
    return output


def sub(a: str, b: str) -> str:
    # assume b is less than a
    # pad b with leading 0s
    # start from RTL
    # if top > bottom, subtract 1 from the next
    # edge case: next is 0
    # find the first digit that is non zero, sub 1 from that. Then everything in between needs to become a 9
    b = ("0" * (len(a) - len(b))) + b
    a_arr = list(a)
    b_arr = list(b)

    n = len(a_arr)
    o_arr = ["0"] * n
    for i in range(n - 1, -1, -1):
        if (stoi(a_arr[i]) >= stoi(b_arr[i])):
            o_arr[i] = str(stoi(a_arr[i]) - stoi(b_arr[i]))
        else: # rtl loop and check for first non zero
            found = False
            for j in range(i - 1, -1, -1):
                if a_arr[j] == "0": # set it to 9 and continue
                    a_arr[j] = "9"
                else:
                    a_arr[j] = str(stoi(a_arr[j]) - 1)
                    o_arr[i] = str((10 + stoi(a_arr[i])) - (stoi(b_arr[i])))
                    found = True
                    break
            if not found:
                # should never get here
                raise Exception("b is greater than a")
    for i in range(len(o_arr)):
        if o_arr[i] != "0":
            return "".join(o_arr[i:])
    return "".join(o_arr)
    
if __name__ == "__main__":
    while True:
        a = input("Enter number A: ")
        b = input("Enter number B: ")
        print(sub(a,b))