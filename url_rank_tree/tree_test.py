import pytest
from tree_node import TreeNodeRoot, TreeNode, Serializable
import json
    
def test_serialize_tree():
    root = TreeNodeRoot(1)
    root.appendChild(TreeNode(2))
    root.appendChild(TreeNode(3))


    root.children[0].appendChild(TreeNode(4))
    root.children[0].appendChild(TreeNode(5))
    root.children[-1].appendChild(TreeNode(6))
    root.children[-1].appendChild(TreeNode(7))

    # root.children[0].children[0].appendChild(TreeNode(8))
    # root.children[0].children[0].appendChild(TreeNode(9))
    # root.children[0].children[0].appendChild(TreeNode(9.1))
    # root.children[0].children[0].appendChild(TreeNode(9.2))
    # root.children[0].children[-1].appendChild(TreeNode(10))
    # root.children[0].children[-1].appendChild(TreeNode(11))
    # root.children[-1].children[0].appendChild(TreeNode(12))
    # root.children[-1].children[0].appendChild(TreeNode(13))
    # root.children[-1].children[-1].appendChild(TreeNode(14))
    # root.children[-1].children[-1].appendChild(TreeNode(15))
    
    rootDict = root.toDict()
    assert rootDict == {
        'name': 1, 
        'data': {'regexNodesInTreeDescendency': 0, 'isRegexNode': False, 'pathFrequency': 1}, 
        'children': [
            {
                'name': 2, 
                'data': None, 
                'children': [
                    {'name': 4, 'data': None, 'children': []}, 
                    {'name': 5, 'data': None, 'children': []}
                ]
            }, 
            {
                'name': 3, 
                'data': None, 
                'children': [
                    {'name': 6, 'data': None, 'children': []}, 
                    {'name': 7, 'data': None, 'children': []}
                ]
            }
        ]
    }
    
    rootJson = root.toJson()
    # assert rootJson == '{"name": 1, "data": {"regexNodesInTreeDescendency": 0, "isRegexNode": false, "pathFrequency": 1}, "children": [{"name": 2, "data": null, "children": [{"name": 4, "data": null, "children": []}, {"name": 5, "data": null, "children": []}]}, {"name": 3, "data": null, "children": [{"name": 6, "data": null, "children": []}, {"name": 7, "data": null, "children": []}]}]}'
    # assert json.loads(rootJson) == rootDict
    assert str(TreeNodeRoot.fromJson(rootJson)) == str(root)
    pass