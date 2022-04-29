import pytest

from tree_node import TreeNode, TreeRootNodeBase

# def test_tree_can_refresh_jagged_array():
#     thirdChild = TreeNode(f'Leaf{3}')
#     firstChild = TreeNode(f'Leaf{1}', children=[thirdChild])
#     secondChild = TreeNode(f'Leaf{2}')
#     tree = TreeNode(name='TestTree', children=[firstChild, secondChild])
#     tree._refreshNodeJaggedArr()
#     assert tree._nodeJaggedArr == [
#         [tree],
#         [firstChild, secondChild],
#         [thirdChild],
#     ], 'Node Jagged Array has refreshed with the wrong shape'
#     thirdChild._refreshNodeJaggedArr()
#     assert thirdChild._nodeJaggedArr == [
#         [tree],
#         [firstChild, secondChild],
#         [thirdChild],
#     ], 'Node Jagged Array does not correctly refresh from child nodes.'


def test_can_traverse_preorder():
    tree = _build_complex_tree()
    allNodesPreOrder = tree.traversePreorder(map=lambda n: n.name)
    traversalType = 'Preorder'
    assert len(allNodesPreOrder) == 7, f'Some nodes were missed when traversing the tree in {traversalType}'
    assert allNodesPreOrder == [
        "RootTreeNode", 
        "TreeNode_Layer_1_child1", 
        "TreeNode_Layer_2_child1", "TreeNode_Layer_2_child2", 
        "TreeNode_Layer_1_child2", 
        "TreeNode_Layer_2_child3", "TreeNode_Layer_2_child4"
        ], f'Nodes are in wrong order after {traversalType} traversal'
    temp = tree.traversePreorder()
    allNodesPreOrder2 = [n.name for n in temp]
    assert allNodesPreOrder2 == allNodesPreOrder, f'The default Callable passed to TreeTraversable.traverse{traversalType}() failed'
    
    pass

def test_can_traverse_postorder():
    tree = _build_complex_tree()
    allNodesPostOrder = tree.traversePostorder(map=lambda n: n.name)
    traversalType = 'Postorder'
    assert len(allNodesPostOrder) == 7, f'Some nodes were missed when traversing the tree in {traversalType}'
    assert allNodesPostOrder == ["TreeNode_Layer_2_child1", "TreeNode_Layer_2_child2", "TreeNode_Layer_1_child1", "TreeNode_Layer_2_child3", "TreeNode_Layer_2_child4", "TreeNode_Layer_1_child2", "RootTreeNode"], f'Nodes are in wrong order after {traversalType} traversal'
    temp = tree.traversePostorder()
    allNodesPostOrder2 = [n.name for n in temp]
    assert allNodesPostOrder2 == allNodesPostOrder, f'The default Callable passed to TreeTraversable.traverse{traversalType}() failed'
    
    pass

def test_can_traverse_inorder():
    tree = _build_complex_tree()
    allNodesInOrder = tree.traverseInorder(map=lambda n: n.name)
    traversalType = 'Inorder'
    assert len(allNodesInOrder) == 7, f'Some nodes were missed when traversing the tree in {traversalType}'
    assert allNodesInOrder == ["TreeNode_Layer_2_child1", "TreeNode_Layer_1_child1", "TreeNode_Layer_2_child2", "RootTreeNode", "TreeNode_Layer_2_child3", "TreeNode_Layer_1_child2", "TreeNode_Layer_2_child4"], f'Nodes are in wrong order after {traversalType} traversal'
    temp = tree.traverseInorder()
    allNodesInOrder2 = [n.name for n in temp]
    assert allNodesInOrder2 == allNodesInOrder, f'The default Callable passed to TreeTraversable.traverse{traversalType}() failed'
    
    pass

def test_can_add_child_to_tree():
    tree = TreeNode(name='TestTree')
    tree.appendChild(TreeNode('FirstLeaf'))
    assert len(tree.children) == 1, 'TestTree appendChild failed to add one child'
    assert isinstance(tree.children[0], TreeNode), 'TestTree appendChild doesnt add child of type TreeNode'
    assert tree.children[0].name == 'FirstLeaf', 'TestTree appendChild, child incorrectly named'
    pass

def _generate_child_node(level:int, childNo: int):
    return TreeNode(name=f'TreeNode_Layer_{level}_child{childNo}')

def _build_complex_tree():
    tree = TreeNode(name='RootTreeNode')
    layer1 = [_generate_child_node(1, i+1) for i in range(2)]
    for i,n in enumerate(layer1):
        tree.appendChild(n)
        numChildren = 2
        layer2n = [_generate_child_node(2,(i*numChildren)+j+1) for j in range(numChildren)]
        for j,nn in enumerate (layer2n):
            n.appendChild(nn)
    return tree

def test_can_get_tree_leaves():
    tree = _build_complex_tree()
    leaves = tree.getLeaves()
    for n in leaves:
        # assert(f'TreeNode_Layer_2_child' in n.name, 'Tree.getLeaves returns nodes that arent leaves')
        assert not(n.children), 'getLeaves() returns nodes with children'
    assert len(leaves)==4, 'getLeaves() return incorrect number of leaves in the tree'
    pass

def test_tree_can_count_its_layers():
    tree = _build_complex_tree()
    assert tree.numberOfLayers == 3, 'Tree cannot correctly count its layers, should be 3.'
    pass


def test_can_initialise_tree():
    tree = TreeNode(name='TestTree')
    assert tree.name == 'TestTree', 'Tree node initialisation failed.'
    pass
    
def test_can_create_deep_copy():
    tree = _build_complex_tree()
    copyTree = tree.copyDeep()
    def _checkNodesEqual(node1:TreeRootNodeBase, node2:TreeRootNodeBase):
        assert node1.name == node2.name
        assert node1.data == node2.data
        assert len(node1.children) == len(node2.children)
        for i, childTuple in enumerate(zip(node1.children, node2.children)):
            _checkNodesEqual(childTuple[0], childTuple[1])
    
    _checkNodesEqual(tree, copyTree)
    pass
        
    
def test_deep_copy_is_new_instance():
    tree:TreeRootNodeBase = _build_complex_tree()
    copyTree:TreeRootNodeBase = tree.copyDeep()
    assert tree != copyTree
    def _checkNodesAreCopies(node1:TreeRootNodeBase, node2:TreeRootNodeBase):
        assert node1 != node2
        for i, childTuple in enumerate(zip(node1.children, node2.children)):
            _checkNodesAreCopies(childTuple[0], childTuple[1])
    
    _checkNodesAreCopies(tree, copyTree)
    pass
    