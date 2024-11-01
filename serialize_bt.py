# Definition for a binary tree node.
class TreeNode(object):
    def __init__(self, x):
        self.val = x
        self.left = None
        self.right = None

from typing import List, Dict

class Codec:

    def serialize(self, root):
        """Encodes a tree to a single string.
        
        :type root: TreeNode
        :rtype: str
        """
        serial: str = ""
        level_serial: str = ""
        level:List[TreeNode|None] = [root]
        level_total = 1
        level_traversed = 0
        level_nodes = 0
        while level:
            if level_traversed >= level_total:
                if level_nodes <= 0: # traversed the whole level but did not encounter any nodes => throwaway level serial and return
                    break
                else:
                    # reset the level
                    serial += level_serial
                    level_serial = ""
                    level_traversed = 0
                    level_nodes = 0
                    level_total *= 2

            node = level.pop(0)
            
            if node is None:
                level += [None, None]
                level_serial += "x,"
            else:
                level += [node.left, node.right]
                level_serial += f"{node.val},"
                level_nodes += 1
            level_traversed += 1
        return serial
    

    def deserialize(self, data):
        """Decodes your encoded data to tree.
        
        :type data: str
        :rtype: TreeNode
        """
        if len(data) == 0:
            return None
        split = data.split(",")[:-1]
        i_to_node: Dict[int, TreeNode | None] = {}
        for i, node_raw in enumerate(split):
            # grab children at 2i + 1, 2i + 2
            # create ith node (or grab it from the map) and set its children
            left_child_raw = split[2 * i + 1] if 2 * i + 1 < len(split) else "x"
            right_child_raw = split[2 * i + 2] if 2 * i + 2 < len(split) else "x"
            if i not in i_to_node:
                if node_raw == "x":
                    i_to_node[i] = None
                else:
                    i_to_node[i] = TreeNode(int(node_raw))
            node = i_to_node[i]
            if node is None:
                continue

            left_child = None if left_child_raw == "x" else TreeNode(int(left_child_raw))
            right_child = None if right_child_raw == "x" else TreeNode(int(right_child_raw))
            i_to_node[2 * i + 1] = left_child
            i_to_node[2 * i + 2] = right_child

            node.left = left_child
            node.right = right_child
        return i_to_node[0]


if __name__ == "__main__":
    root = TreeNode(1)
    left = TreeNode(2)
    right = TreeNode(3)
    right_right = TreeNode(4)
    left_right = TreeNode(5)
    root.left = left
    root.left.right = left_right
    root.right = right
    root.right.right = right_right

    codec = Codec()
    serialized = codec.serialize(root)
    print(serialized)
    deserialized = codec.deserialize(serialized)
    print(codec.serialize(deserialized))


# Your Codec object will be instantiated and called as such:
# ser = Codec()
# deser = Codec()
# ans = deser.deserialize(ser.serialize(root))