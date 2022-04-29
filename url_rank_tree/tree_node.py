from __future__ import annotations
import inspect
from operator import add
from os import path, setpgid
import io
import os
import re
from typing import Any, Callable, Generic, Iterable, Optional, TypeVar
import jsonpickle
import requests
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from collections.abc import Sequence
from uint import Uint, Int
from enum import Enum, IntEnum
import debugpy as debug
import warnings
from pprint import pprint
import abc
import json
import pydot
import uuid

 
os.environ["PATH"] += os.pathsep + "/usr/local/Cellar/graphviz/2.50.0/bin"

# graph = pydot.Dot(graph_type="graph", rankdir="UD")

# root = "Pydot"
# edge = pydot.Edge(root, "How to install it")
# graph.add_edge(edge)

# graph.write_png("Hello.png")

# graph = pydot.Dot('my_graph', graph_type='graph', bgcolor='yellow')

# # Add nodes
# my_node = pydot.Node('a', label='Foo')
# graph.add_node(my_node)
# # Or, without using an intermediate variable:
# graph.add_node(pydot.Node('b', shape='circle'))

# # Add edges
# my_edge = pydot.Edge('a', 'b', color='blue')
# graph.add_edge(my_edge)
# # Or, without using an intermediate variable:
# graph.add_edge(pydot.Edge('b', 'c', color='blue'))

# graph.add_edge(pydot.Edge('b', 'd', style='dotted'))

# graph.set_bgcolor('lightyellow')
# graph.get_node('b')[0].set_shape('box')

# graph.write_png("Hello.png")


def draw_new_tree(tree: TreeRootNodeBase) -> pydot.Dot:
    return _draw_tree_nodes_on_graph(tree, pydot.Dot(graph_type="graph", rankdir="UD"))

def _draw_tree_nodes_on_graph(tree: TreeRootNodeBase, graph: pydot.Dot=pydot.Dot(graph_type="graph", rankdir="UD")) -> pydot.Dot:
    graph.set_node_defaults(shape='box', style="filled", color="black", fillcolor="white", fontname='helvetica')
    graph.set_edge_defaults(fontname='helvetica')
    
    root_node = pydot.Node(str(uuid.uuid4()), label=tree.name)
    guid = root_node.get_name()
    graph.add_node(root_node)
    
    _add_to_dot_node(root_node, tree, graph)
    
    return graph
     
def _add_to_dot_node(node: pydot.Node, treeNode: TreeRootNodeBase, graph: pydot.Dot):
    for cNode in treeNode.children:
        child_node = pydot.Node(str(uuid.uuid4()), label=cNode.name)
        edge = pydot.Edge(node.get_name(), child_node)
        child_guid = edge.get_destination()
        child_label = child_node.get_attributes()['label']
        graph.add_edge(edge)
        graph.add_node(child_node)
        if cNode.children:
            _add_to_dot_node(child_node, cNode, graph)
    
def save_pydot_to_png(graph:pydot.Dot, fileName:str):
    graph.write_png(os.path.splitext(os.path.basename(fileName))[0] + '.png')
    
def view_graph(graph:pydot.Dot):
    from IPython.display import Image, display
    plt = Image(graph.create_png())
    display(plt)


# @abc.ABC
class ITreeNode(abc.ABC):
    def __init__(self, name:str) -> None:
        self._data: Serializable = None
        self.name:str = name
        self._id = str(uuid.uuid4())
        
    def _getData(self):
        return self._data
    
    
    def _setData(self, data:Serializable):
        self._data = data
        
    data:Serializable = property(_getData,_setData)
    
    @abc.abstractclassmethod
    def toDict(self) -> dict:
        pass
    
    def _getId(self):
        return self._id
    
    id:str = property(_getId)
    
    
    COUNT:list[int]

    @abc.abstractmethod
    def print2DUtil(root, space:int) -> str:
        pass

    def print2D(root) :
        pass
    
    def _dummyPipe(v:T) -> T:
        return v

    def traverseInorder(self, map:Callable[[ITreeNode],T]=_dummyPipe):
        pass

    def traversePostorder(self, map:Callable[[ITreeNode],T]=_dummyPipe):
        pass

    def traversePreorder(self, map:Callable[[ITreeNode],T]=_dummyPipe):
        pass
    
    def __repr__(self):
        return TreePrintable.print2D(self)

    def __str__(self) -> str:
        return str([node.name for node in self.traverseInorder()])

    def __hash__(self) -> int:
        return hash(str(self))
    
    @abc.abstractmethod
    def appendChild(self, node):
        pass

    @abc.abstractmethod
    def getDepth(self) -> Uint:
        pass

    @abc.abstractmethod
    def numberOfLayers() -> Uint:
        pass

    @abc.abstractmethod
    def getLeaves(self) -> list[ITreeNode]:
        pass

    @abc.abstractmethod
    def getChildren(self) -> list[ITreeNode]:
        pass

    @property
    @abc.abstractmethod
    def children() -> list[ITreeNode]:
        pass

    @abc.abstractmethod
    def rightChildren() -> list[ITreeNode]:
        pass

    @abc.abstractmethod
    def leftChildren() -> list[ITreeNode]:
        pass


class ITreeChildNode(ITreeNode):
    @abc.abstractmethod
    def acceptParent(self, parentNode:ITreeNode) -> bool:
        pass

class TreePrintable(ITreeNode):

    def ancestorAtLevel(self, level:Uint) -> ITreeNode:
        '''Root is level 1'''
        level = max(1,level)
        ancestry = self.ancestry()
        
        if level > len(ancestry):
            return self
        return ancestry[level-1]

    def ancestorGenerationsBefore(self, generationsAgo:Uint) -> ITreeNode:
        generationsAgo = max(0,generationsAgo)
        ancestor = self
        for i in range(0,generationsAgo):
            if hasattr(ancestor, 'parent'):
                ancestor = getattr(ancestor, 'parent')
            else:
                # hit root
                return ancestor
        return ancestor

    def ancestry(self):
        ancestor = self
        ancestry:list[TreePrintable] = []
        i = 0
        while i <= 99 and hasattr(ancestor, 'parent'):
            i += 1
            ancestry = [ancestor] + ancestry
            ancestor = getattr(ancestor, 'parent')
        return ancestry

    def rightChildren(self) -> list:
        # Get number of children to root
        n = 0
        if self.children:
            n = len(self.children)
        return self.children[int(n/2.0):]

    def leftChildren(self) -> list:
        # Get number of children to root
        n = 0
        if self.children:
            n = len(self.children)
        return self.children[:int(n/2.0)]
        


    def isRightOf(self,ancestor:ITreeNode):
        ancestry = self.ancestry()
        assert ancestor != self, 'ancestor cant be self'
        assert ancestor in ancestry, f'ancestor passed: {ancestor.name} must be in ancestry of self: {self.name}'
        childToAncestorInAncestry = next(anc for anc in ancestor.children if anc in ancestry)
        return childToAncestorInAncestry in self.rightChildren()

    def isLeftOf(self,ancestor:ITreeNode):
        return not self.isRightOf(ancestor)


    PRINT_SPACE_COUNT = [8] # == 2 tabs
    PRINT_HYPHEN_COUNT = int(PRINT_SPACE_COUNT[0]/2)
    
    def _print2DUtilArr(root, space:int) -> list:

        output = []

        # Base case
        if (root == None):
            return ''

        # Increase distance between levels
        space += TreePrintable.PRINT_SPACE_COUNT[0]

        #Calculate the length of the space
        longSpace = ''
        for i in range(TreePrintable.PRINT_SPACE_COUNT[0], space):
            # print(end = " ") # end parameter tells it to append to end of current line rather than create a new line
            longSpace += ' '
#           longSpace += '-'
        
        # remove last few spaces and replace with hyphens
        if len(longSpace) >= (TreePrintable.PRINT_HYPHEN_COUNT*2):
            longSpace = longSpace[:-1*TreePrintable.PRINT_HYPHEN_COUNT] + ('-'*TreePrintable.PRINT_HYPHEN_COUNT)

        def _drawSubTrees(fromRight:bool, root, childRoot, space:int, longSpace:str):
            _x = len(longSpace)+TreePrintable.PRINT_HYPHEN_COUNT
            subTreesArr = TreePrintable._print2DUtilArr(childRoot, space)
            nodeSubTrees = [subTreesArr.index(line) for line in subTreesArr if line[_x:_x+TreePrintable.PRINT_HYPHEN_COUNT] == ('-'*TreePrintable.PRINT_HYPHEN_COUNT)]
            _out = []
            if fromRight:
                # slice = subTreesArr[min(nodeSubTrees):]
                slice = range(min(nodeSubTrees),len(subTreesArr))
            else:
                # slice = subTreesArr[:max(nodeSubTrees)]
                slice = range(0,max(nodeSubTrees))
            for i,line in enumerate(subTreesArr):
                if i in slice:
                    if line[_x] == '-':
                        pass
                    elif line[_x] == ' ':
                        line = line[:_x] + '|' + line[_x+1:]
                _out.append(line)

            return _out

        # Process RIGHT CHILDREN first (To be printed in lines above root, as print flips tree to left):
        rightChildren = root.rightChildren()[::-1]
        for childRoot in rightChildren:
            output += _drawSubTrees(True, root, childRoot, space, longSpace)
            
        # Next Line: 
        # outputStr += '\n' # print()
        
        
        # # add line spacer edges '|' where parent nodes have further right siblings.
        # def _addSpacers(longSpace, ancestry):
        #     for i,char in enumerate(range(TreePrintable.PRINT_HYPHEN_COUNT, len(longSpace), TreePrintable.PRINT_SPACE_COUNT)):
        #         # First check for 
        #         _parentNodeAtLvl = ancestry[i] # root.ancestorAtLevel(1) is root node
        #         _parentsChildNodeAtLvl = ancestry[i+1] # Should be guaranteed this index by only enumerating the length of longSpace
                
        #         # Check if parentsChildNode is not the furthest right sibling:
        #         if not _parentsChildNodeAtLvl.isLeftMostSibling():
        #             longSpace[char] = '|'

        #         if -1 < _parentNodeAtLvl.children.index(_parentsChildNodeAtLvl) and _parentNodeAtLvl.children.index(_parentsChildNodeAtLvl) < len(_parentNodeAtLvl.children):
        #             # Not furthest right child, add '|'.
        #             longSpace[char] = '|'
        #     return longSpace
        
        # ancestry = root.ancestry()
        # longSpace = _addSpacers(longSpace, ancestry)
        
        # Print CURRENT NODE after space
        # add the tree node label
        output += [f'{longSpace}{root.name}' + ('-'*max(TreePrintable.PRINT_HYPHEN_COUNT-len(f'{root.name}'),0)) + ('|' if len(f'{root.name}') <= TreePrintable.PRINT_HYPHEN_COUNT else '')]
        
        # output += '\n'
        # longSpace = _addSpacers(longSpace, ancestry)
        
        # Add a line break that looks like longspace but with one '|' instead of 4 '-'s at the end:
        # output += re.sub(r'-{'+str(TreePrintable.PRINT_HYPHEN_COUNT)+r'}$', '|', longSpace, count=1)

        # Process left child
        leftChildren = root.leftChildren()[::-1]
        for childRoot in leftChildren:
            output += _drawSubTrees(False, root, childRoot, space, longSpace)

        return output

    # 
    def print2DUtil(root, space:int) -> str:
        '''Function to print binary tree in 2D. \n
        It does reverse inorder traversal'''
        return '\n'.join(TreePrintable._print2DUtilArr(root,space))

    # Wrapper over print2DUtil()
    def print2D(root) :
        
        # space=[0]
        # Pass initial space count as 0
        return TreePrintable.print2DUtil(root, 0)

class TreeTraversable(ITreeNode):
    def _dummyPipe(v:T) -> T:
        return v

    # A function to do inorder tree traversal
    def traverseInorder(self, map:Callable[[ITreeNode],Any]=_dummyPipe):

        output:list[TreeNode] = []

        if self:

            # Get number of children to root
            n = 0
            if self.children:
                n = len(self.children)

            # First recur on left child
            for childRoot in self.children[int((n+1)/2.0)-1::-1]:
                output += childRoot.traverseInorder(map=map)

            # then print the name of node
            output += [map(self)]

            # now recur on right child
            for childRoot in self.children[:int((n+1)/2.0)-1:-1]:
                output += childRoot.traverseInorder(map=map)
            
        
        return output


    # A function to do postorder tree traversal
    def traversePostorder(self, map:Callable[[ITreeNode],Any]=_dummyPipe):

        output:list[TreeNode] = []

        if self:

            # Get number of children to self
            n = 0
            if self.children:
                n = len(self.children)

            # First recur on left child
            for childRoot in self.children[int((n+1)/2.0)-1::-1]:
                output += childRoot.traversePostorder(map=map)

            # the recur on right child
            for childRoot in self.children[:int((n+1)/2.0)-1:-1]:
                output += childRoot.traversePostorder(map=map)

            # now print the data of node
            output += [map(self)]

        return output

    # A function to do preorder tree traversal
    def traversePreorder(self, map:Callable[[ITreeNode],T]=_dummyPipe):

        output:list[TreeNode] = []

        if self:

            # Get number of children to root
            n = 0
            if self.children:
                n = len(self.children)

            # First print the data of node
            output += [map(self)]

            # Then recur on left child
            for childRoot in self.children[int((n+1)/2.0)-1::-1]:
                output += childRoot.traversePreorder(map=map)

            # Finally recur on right child
            for childRoot in self.children[:int((n+1)/2.0)-1:-1]:
                output += childRoot.traversePreorder(map=map)

        return output
    
    def __repr__(self):
        return TreeNode.print2D(self)

    def __str__(self) -> str:
        return str(self.traverseInorder(map=lambda n: n.name))

    def __hash__(self) -> int:
        return hash(str(self))   
    
T = TypeVar("T")
TS = TypeVar("TS", str, Uint, int, float, None, list, dict, Sequence, Iterable, bool)

class Serializable(abc.ABC):

    @abc.abstractclassmethod
    def toDict(self) -> dict[str,TS]:
        pass
    
    @abc.abstractclassmethod
    def fromDict(dic:dict[str,TS], objType:T) -> T:
        pass
    
    # def fromJson(jsonString:str, objType:T) -> T:
    #     d = json.loads(jsonString)
    #     return Serializable.fromDict(d, objType=objType)
    
    # def toJson(self) -> str:
    #     return json.dumps(self.toDict())
    
    def fromJson(jsonString: str) -> V:
        return jsonpickle.decode(jsonString)
    
    def toJson(self) -> str:
        return jsonpickle.encode(self)
    
    
class TreeSerializable(ITreeNode, Serializable):

    def toDict(self) -> dict[str,TS]:
        return {
            'name': self.name,
            'id': str(self.id),
            # '__type__': type(self),
            'data': self.data.toDict() if isinstance(self.data,Serializable) else self.data,
            'children': [c.toDict() for c in self.children]
        }
        
        
    def fromDict(dic:dict[str,TS], objType:V) -> V:
        instance = type(objType)(dic['name'])
        instance.data = dic['data']
        for child in instance.children:
            instance.appendChild(TreeSerializable.fromDict(child))
        return instance
        
    # def fromJson(jsonString:str, objType:V) -> V:
    #     d = json.loads(jsonString)
    #     return Serializable.fromDict(d, objType=objType)
    
    

V = TypeVar("V")


    
class TreeRootNode(ITreeChildNode):



    def __init__(self, name:str) -> None:
        super().__init__(name)
        self.name = name
        
        self._children = []

    # def getParent(self):
    #     return self._parent
    # # def setParent(self,parent):
    # #     self._parent = parent
    # parent = property(getParent)

    def getChildren(self) -> list[TreeRootNode]:
        return self._children
    
    children:list[TreeRootNode] = property(getChildren)

    def appendChild(self, node:ITreeChildNode, atPosition:Optional[int]=None):
        assert isinstance(node, ITreeChildNode), 'can only add TreeNode children'
        assert hasattr(node,'parent') == False or node.parent is None or node.parent == self, f'TreeNode: ({node.name}) can only have one parent. Already has parent with name: {node.parent.name}, so cant set self as parent with name: {self.name}'
        
        if node not in self._children:
            if atPosition is not None:
                self._children = self._children[:atPosition] + [node] + self._children[atPosition:]
            else:
                self._children.append(node)
            node.acceptParent(self)
        else:
            debug.breakpoint()
            print('warning')
        
        return self
    
    # def appendChildren(self, addChilds:list):
    #     for c in addChilds:
    #         self.appendChild(c)

    def acceptParent(self, parentNode:ITreeChildNode) -> bool:
        if self in parentNode.children:
            self._parent  = parentNode
            return True
        return False


T = TypeVar('T',bound=TreeRootNode)

class TreeRootNodeBase(TreeRootNode, TreePrintable, TreeTraversable, TreeSerializable):
    "Generic tree node."
    def __init__(self, name='root', data=None, children:list[ITreeChildNode]=None):
        super().__init__(name)
        if data is None:
            self.data = self.name
        else:
            self.data = data
        
        if children is not None:
            for child in children:
                self.appendChild(child)
    
    def __repr__(self):
        return TreeNode.print2D(self)

    def __str__(self) -> str:
        return str([node.name for node in self.traversePreorder()])

    def __hash__(self) -> int:
        return hash(str(self))
    
    def toDict(self) -> dict[str, TS]:
        return super().toDict()
    
    def _getChildren(self):
        return super().getChildren()
    
    children:list[TreeRootNodeBase] = property()
    
    def drawGraph(self, outFileName:str=None):
        graph = draw_new_tree(self)
        if outFileName is not None:
            save_pydot_to_png(graph, outFileName)
    
    def copyDeep(self:T) -> T:
        kwargs = {}
        for constructor_arg_name in list(inspect.signature(type(self).__init__).parameters)[1:]:
            if hasattr(self, constructor_arg_name):
                kwargs[constructor_arg_name] = getattr(self, constructor_arg_name)
        
        instance = type(self)(**kwargs)
        instance.data = self.data
        
        for child in self.children:
            instance.appendChild(child.copyDeep())
        
        return instance
    
    def getNumberLayers(self):
        return self.getDepth()

    def getDepth(self) -> int:
        if self.children:
            return max((c.getDepth() for c in self.children))+1
        else:
            return 1

    numberOfLayers:int = property(getNumberLayers)

    def getLeaves(self):
        _leaves = []
        if not self.children:
            return [self]
        return [x for c in self.children for x in c.getLeaves()]

class TreeChildNode(TreeRootNodeBase):
    def __init__(self, name:str) -> None:
        super().__init__()
        self.name = name
        self._parent = None
        self._children = []

    def getParent(self):
        return self._parent
    # def setParent(self,parent):
    #     self._parent = parent
    parent:TreeChildNode = property(getParent)

    def getSiblingsOfPathType(self):
        return [n for n in self.parent.children if not n.data['isRegexNode']]

    def getNumSiblingsOfPathType(self):
        return len(self.getSiblingsOfPathType())

# class TreeNodeBase(TreeChildNode):
#     pass

class TreeNodeRoot(TreeRootNodeBase):
    def __init__(self, name='root'):
        super().__init__(name=name)
        self.data = {
            'regexNodesInTreeDescendency': 0,
            'isRegexNode':False,
            'pathFrequency': 1
        }

class TreeNode(TreeChildNode):
    def __init__(self, name='root', data=None):
        super().__init__(name=name)
        self.data = data
        if data is None:
            data = {}
        # assert parent is None or isinstance(parent, TreeNode), 'parent must be a TreeNode'
        # self._parent = parent
        # if parent is not None:
        #     parent.addChild(self)

    
   