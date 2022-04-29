
# https://www.geeksforgeeks.org/print-binary-tree-2-dimensions/
# Python3 Program to print binary tree in 2D
COUNT = [10]

# Binary Tree Node
""" utility that allocates a newNode
with the given key """
class newNode:

    # Construct to create a newNode
    def __init__(self, key):
        self.data = key
        self._children:list[newNode] = []

    def getChildren(self) -> list:
        return self._children

    children = property(getChildren)

    def appendChild(self, child):
        self._children = self._children + [child]


# Function to print binary tree in 2D
# It does reverse inorder traversal
def print2DUtil(root, space:int):

    # Base case
    if (root == None):
        return

    # Increase distance between levels
    space += COUNT[0]

    # Get number of children to root
    n = 0
    if root.children:
        n = len(root.children)

    # print(f'Root {root.data} has {n} kids')
    # print(f'{n} kids -> {(n+1)/2.0} -> {(n+1)/2.0 - 1} -> {int((n+1)/2.0)}')
    # rightKids = ', '.join([str(k.data) for k in root.children[:int((n+1)/2.0):-1]])
    # print(f'Start traverseing right children from index: {int((n+1)/2.0)}: [{rightKids}]')
    
    # Process right children first
    for childRoot in root.children[:int((n+1)/2.0)-1:-1]:
        print2DUtil(childRoot, space)

    # Print current node after space
    # count
    print()
    for i in range(COUNT[0], space):
        print(end = " ")
    print(root.data)

    # Process left child
    for childRoot in root.children[int((n+1)/2.0)-1::-1]:
        print2DUtil(childRoot, space)

# Wrapper over print2DUtil()
def print2D(root) :
    
    # space=[0]
    # Pass initial space count as 0
    print2DUtil(root, 0)

# Driver Code
if __name__ == '__main__':

    root = newNode(1)
    root.appendChild(newNode(2))
    root.appendChild(newNode(3))


    root.children[0].appendChild(newNode(4))
    root.children[0].appendChild(newNode(5))
    root.children[-1].appendChild(newNode(6))
    root.children[-1].appendChild(newNode(7))

    root.children[0].children[0].appendChild(newNode(8))
    root.children[0].children[0].appendChild(newNode(9))
    root.children[0].children[0].appendChild(newNode(9.1))
    root.children[0].children[0].appendChild(newNode(9.2))
    root.children[0].children[-1].appendChild(newNode(10))
    root.children[0].children[-1].appendChild(newNode(11))
    root.children[-1].children[0].appendChild(newNode(12))
    root.children[-1].children[0].appendChild(newNode(13))
    root.children[-1].children[-1].appendChild(newNode(14))
    root.children[-1].children[-1].appendChild(newNode(15))
    
    print2D(root)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

# This code is contributed by
# Shubham Singh(SHUBHAMSINGH10)
# https://www.geeksforgeeks.org/tree-traversals-inorder-preorder-and-postorder/?ref=lbp


# Python program to for tree traversals

# A class that represents an individual node in a
# Binary Tree


class Node:
    def __init__(self, key):
        self.left = None
        self.right = None
        self._children = []
        self.data = key

    def getChildren(self) -> list:
        return self._children

    children = property(getChildren)

    def appendChild(self, child):
        self._children = self._children + [child]


# A function to do inorder tree traversal
def traverseInorder(root):

    output = []

    if root:

        # Get number of children to root
        n = 0
        if root.children:
            n = len(root.children)

        # First recur on left child
        for childRoot in root.children[int((n+1)/2.0)-1::-1]:
            output += traverseInorder(childRoot)

        # then print the data of node
        output += [root.data]

        # now recur on right child
        for childRoot in root.children[:int((n+1)/2.0)-1:-1]:
            output += traverseInorder(childRoot)
        
    
    return output


# A function to do postorder tree traversal
def traversePostorder(root):

    output = []

    if root:

        # Get number of children to root
        n = 0
        if root.children:
            n = len(root.children)

        # First recur on left child
        for childRoot in root.children[int((n+1)/2.0)-1::-1]:
            output += traversePostorder(childRoot)

        # the recur on right child
        for childRoot in root.children[:int((n+1)/2.0)-1:-1]:
            output += traversePostorder(childRoot)

        # now print the data of node
        output += [root.data]

    return output

# A function to do preorder tree traversal
def traversePreorder(root):

    output = []

    if root:

        # Get number of children to root
        n = 0
        if root.children:
            n = len(root.children)

        # First print the data of node
        output += [root.data]

        # Then recur on left child
        for childRoot in root.children[int((n+1)/2.0)-1::-1]:
            output += traversePreorder(childRoot)

        # Finally recur on right child
        for childRoot in root.children[:int((n+1)/2.0)-1:-1]:
            output += traversePreorder(childRoot)

    return output

# Driver code
if __name__ == '__main__':
    root = Node(1)
    root.appendChild(Node(2))
    root.appendChild(Node(3))


    root.children[0].appendChild(Node(4))
    root.children[0].appendChild(Node(5))
    # root.children[-1].appendChild(Node(6))
    # root.children[-1].appendChild(Node(7))
    print("Preorder traversal of binary tree is")
    print(traversePreorder(root))

    print("\nInorder traversal of binary tree is")
    print(traverseInorder(root))

    print("\nPostorder traversal of binary tree is")
    print(traversePostorder(root))
