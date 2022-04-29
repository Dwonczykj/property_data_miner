import pytest

from tree_node import draw_new_tree, save_pydot_to_png, view_graph, TreeNode

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

def test_can_draw_tree():
    tree = _build_complex_tree()
    graph = draw_new_tree(tree)
    dotString = graph.to_string()
    
    assert dotString == 'graph G {\nrankdir=UD;\n"c50ba588-6164-4f4d-83e6-50ce839d8e01" -- "599f28a1-5a8b-49d1-ada4-293b376be495";\n"599f28a1-5a8b-49d1-ada4-293b376be495" -- "594d08cf-0a50-44c5-a81e-035f1b3628e6";\n"599f28a1-5a8b-49d1-ada4-293b376be495" -- "34b16164-e80d-40e4-b335-7b51958950d4";\n"c50ba588-6164-4f4d-83e6-50ce839d8e01" -- "73ced6d6-fdde-4870-8b16-96fb5b3e40cc";\n"73ced6d6-fdde-4870-8b16-96fb5b3e40cc" -- "2a4ef4de-fa56-411e-893c-39cd41927c4a";\n"73ced6d6-fdde-4870-8b16-96fb5b3e40cc" -- "a8c5bae2-4dab-470d-814b-61760d31c304";\n}\n'
    pass