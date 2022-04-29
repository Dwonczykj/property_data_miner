
from _pytest.capture import _readline_workaround
from pytest import CaptureFixture
import pytest
from pprint import pprint
from rank_pair_tree import RankPair, RankPairTreeNode, RankPairTree, RankPairTreeRank


def test_rankTree_builds_correct_layers():
    
    _testUrl = 'https://groceries.asda.com/product/natural-plain-organic/fage-total-fat-free-greek-recipe-natural-yogurt/24771357?sid=12534Q&style=green'
    rankTree = RankPairTree(_testUrl)
    pprint(rankTree)
    assert rankTree.depth == 9, f'RankTree should have 9 layers for url: {_testUrl}, not {rankTree.depth}'
    pass


def test_rankTree_builds_correct_layers(capfd:CaptureFixture[str]):
    
    _testUrl = 'https://acme.com/forum?sid=QZ932'
    rankTree = RankPairTree(_testUrl)
    pprint(rankTree)
    out, err = capfd.readouterr()
#     assert out == (
#         '''                    ----^[0-9A-Za-z]+$
#             ----^[A-Za-z]+$
#             |       ----QZ932
#     ----^[A-Za-z]+$
#     |       |       ----^[0-9A-Za-z]+$
#     |       ----sid-|
#     |               ----QZ932
# https://acme.com
#     |               ----^[0-9A-Za-z]+$
#     |       ----^[A-Za-z]+$
#     |       |       ----QZ932
#     ----forum
#             |       ----^[0-9A-Za-z]+$
#             ----sid-|
#                     ----QZ932''')
    print(rankTree.treeRank)
    # capfd.
    # out, err = capfd.readouterr()
    assert rankTree.depth == 4, f'RankTree should have 4 layers for url: {_testUrl}, not {rankTree.depth}'
    assert rankTree.data['pathFrequency'] == 1 and rankTree.data['regexNodesInTreeDescendency'] == 0 
    pass

def test_rankTree_builds_correct_layers_complex():
    
    _testUrl = 'https://groceries.asda.com/product/natural-plain-organic/fage-total-fat-free-greek-recipe-natural-yogurt/24771357?sid=12534Q&style=green'
    rankTree = RankPairTree(_testUrl)
    pprint(rankTree)
    print(rankTree.treeRank)
    pass

def test_rankTree_2_urls():
    
    _testUrl = 'https://acme.com/forum?sid=QZ932'
    rankTree = RankPairTree(_testUrl)
    assert rankTree._treeState.children[1].fullNameFromRoot.startswith('https://acme.com/')
    _testUrl2 = 'https://acme.com/forum?sid=QZ933'
    rankTree.embedUrl(_testUrl2)
    treeRank = rankTree.treeRank
    assert treeRank['isRegexNode'] == True, 'treeRank[\'isRegexNode\'] should be True'
    assert treeRank['pathFrequency'] == 2, 'treeRank[\'pathFrequency\'] should be 2'
    assert treeRank['regexNodesInTreeDescendency'] == 1, 'treeRank[\'regexNodesInTreeDescendency\'] should be 1'
    rankTree.sortTree()
    pprint(rankTree)
    pass

def test_rankTree_multi_urls():
    urls = [
        'https://groceries.asda.com/promotion/2-for-4/ls91619', 
        'https://groceries.asda.com/cat/vegan-plant-based/617635960', 
        'https://groceries.asda.com/product/910000879998', 
        'https://groceries.asda.com/product/1000005036703', 
        'https://groceries.asda.com/accessibility', 
        'https://groceries.asda.com/cat/fresh-food-bakery/103099', 
        'https://groceries.asda.com/product/1000275697716', 
        'https://groceries.asda.com/super_dept/food-cupboard/1215337189632', 
        'https://groceries.asda.com/product/1000329097857', 
        'https://groceries.asda.com/recipes/Crunchy-cheese-bites/384e188d-2aff-11e9-8802-7daf07a34f81'
        ]
    rankTree = RankPairTree(urls[0])
    for url in urls[1:]:
        rankTree.embedUrl(url)
        rankTree.sortTree()
    assert rankTree.__repr__() == ('                    ----^[0-9A-Za-z]+$\n                    ----103099\n            ----^[0-9A-Za-z\\-]+$\n            |       ----617635960\n            |       ----ls91619\n                    ----^[0-9A-Za-z\\-]+$\n            ----Crunchy-cheese-bites\n            |       ----384e188d-2aff-11e9-8802-7daf07a34f81\n            ----1000329097857\n            ----1000275697716\n                    ----^[0-9]+$\n            ----fresh-food-bakery\n            |       ----103099\n    ----^[A-Za-z]+$\n    |       ----1000005036703\n    |       ----910000879998\n    |       |       ----^[0-9]+$\n    |       ----vegan-plant-based\n    |               ----617635960\n    |       |       ----^[0-9A-Za-z]+$\n    |       ----2-for-4\n    |               ----ls91619\n                    ----^[0-9A-Za-z\\-]+$\n            ----^[0-9A-Za-z\\-]+$\n            |       ----384e188d-2aff-11e9-8802-7daf07a34f81\n    ----recipes\n    |       |       ----^[0-9A-Za-z\\-]+$\n    |       ----Crunchy-cheese-bites\n    |               ----384e188d-2aff-11e9-8802-7daf07a34f81\n    ----accessibility\nhttps://groceries.asda.com\n    |       ----^[0-9]+$\n    |       ----1000329097857\n    |       ----1000275697716\n    ----product\n            ----1000005036703\n            ----910000879998\n    |               ----^[0-9]+$\n    |               ----103099\n    |       ----^[0-9A-Za-z\\-]+$\n    |       |       ----617635960\n    |               ----^[0-9]+$\n    |       ----fresh-food-bakery\n    |       |       ----103099\n    ----cat-|\n            |       ----^[0-9]+$\n            ----vegan-plant-based\n                    ----617635960\n    |               ----^[0-9A-Za-z]+$\n    |       ----^[0-9A-Za-z\\-]+$\n    |       |       ----ls91619\n    ----promotion\n            |       ----^[0-9A-Za-z]+$\n            ----2-for-4\n                    ----ls91619')
    pass

def test_rankTree_get_example_generalisation():
    urls = [
        'https://groceries.asda.com/product/910000879998', 
        'https://groceries.asda.com/product/1000005036703',
        'https://groceries.asda.com/product/3120005036743',
    ]
    rankTree = RankPairTree(urls[0])
    url = urls[1]
    exampleUrlGeneralisations = rankTree.getAllExampleGeneralisationsOf(url,removeRegexNodes=True)
    assert exampleUrlGeneralisations[0] == 'https://groceries.asda.com/product/910000879998'
    # exampleUrlGeneralisations = rankTree.getAllExampleGeneralisationsOf(url,removeRegexNodes=False)
    # assert 'https://groceries.asda.com/<regex>^[A-Za-z]+$</regex>/1000005036703' in exampleUrlGeneralisations[0] 
    # assert exampleUrlGeneralisations[0] == 'https://groceries.asda.com/<regex>^[A-Za-z]+$</regex>/1000005036703'
    
    rankTree.embedUrl(url)
    rankTree.sortTree()
    url = urls[2]
    exampleUrlGeneralisations = rankTree.getAllExampleGeneralisationsOf(url,removeRegexNodes=True)
    assert exampleUrlGeneralisations[0] == 'https://groceries.asda.com/product/910000879998'
    # exampleUrlGeneralisations = rankTree.getAllExampleGeneralisationsOf(url,removeRegexNodes=False)
    # assert exampleUrlGeneralisations[0] == 'https://groceries.asda.com/product/910000879998'
    pass
    

def test_ranktree_get_example_generalisations_returns_none_for_first_url():
    rankTree = RankPairTree()
    exampleUrlGeneralisation = rankTree.getExampleGeneralisationOf('https://groceries.asda.com',removeRegexNodes=True)
    assert exampleUrlGeneralisation is None
    pass

def test_ranktree_check_example_generalisations_matches_for_2_duplicate_urls():
    rankTree = RankPairTree()
    urls = [
        'https://groceries.asda.com', 
        'https://groceries.asda.com', 
        # 'https://groceries.asda.com/promotion/2-for-7/ls91300'
    ]
    rankTree.embedUrl(urls[0])
    exampleUrlGeneralisation = rankTree.getExampleGeneralisationOf(urls[0],removeRegexNodes=True)
    assert exampleUrlGeneralisation == urls[0]
    pass
    
def test_ranktree_get_example_generalisations_doesnt_return_subpaths():
    urls = [
        'https://groceries.asda.com', 
        'https://groceries.asda.com/promotion/2-for-7/ls91300'
    ]
    rankTree = RankPairTree(urls[0])
    url = urls[1]
    exampleUrlGeneralisation = rankTree.getExampleGeneralisationOf(url,removeRegexNodes=True)
    assert exampleUrlGeneralisation is None
    exampleUrlGeneralisations = rankTree.getAllExampleGeneralisationsOf(url,removeRegexNodes=True)
    assert exampleUrlGeneralisations is None or exampleUrlGeneralisations == []
    pass
    
def test_ranktree_get_example_generalisations_should_not_match():
    urls = [
        'https://groceries.asda.com/promotion/2-for-7/ls91300', 
        'https://groceries.asda.com/product/1000338629556', 
        # 'https://groceries.asda.com/super_dept/veganuary/1215686171560', 
        # 'https://groceries.asda.com/cat/fresh-food-bakery/103099', 
        # 'https://groceries.asda.com/product/1000334423970', 
        # 'https://groceries.asda.com/product/18883', 
        # 'https://groceries.asda.com/product/1000330481079', 
        # 'https://groceries.asda.com/product/1000237774511', 
        # 'https://groceries.asda.com/event/gino_dacampo_view_all', 
        # 'https://money.asda.com/insurance/car-insurance/?utm_source=ghs&utm_medium=footer&utm_campaign=car-insurance'
    ]
    rankTree = RankPairTree(urls[0])
    url = urls[1]
    exampleUrlGeneralisations = rankTree.getAllExampleGeneralisationsOf(url,removeRegexNodes=True)
    assert exampleUrlGeneralisations is None or exampleUrlGeneralisations == []
    exampleUrlGeneralisation = rankTree.getExampleGeneralisationOf(url,removeRegexNodes=True)
    assert exampleUrlGeneralisation is None
    pass
    
def test_ranktree_is_serializable():
    urls = [
        'https://groceries.asda.com', 
        'https://groceries.asda.com/promotion',
        'https://groceries.asda.com/product', 
        # 'https://groceries.asda.com/promotion/2-for-7/ls91300',
        # 'https://groceries.asda.com/product/1000338629556', 
        # 'https://groceries.asda.com/super_dept/veganuary/1215686171560', 
        # 'https://groceries.asda.com/cat/fresh-food-bakery/103099', 
        # 'https://groceries.asda.com/product/1000334423970',
    ]
    rankTree = RankPairTree(urls[0])
    for url in urls[1:]:
        rankTree.embedUrl(url)
    rankTreeJson = rankTree.toJson()
    copyTreeFromJson = RankPairTree.fromJson(rankTreeJson)
    # assert rankTreeDict == {
    #     'initialised': True,
    #     '_treeState': {
    #         'name': ''
    #     }
    # }
    assert str(copyTreeFromJson) == str(rankTree)
    assert copyTreeFromJson.__repr__() == rankTree.__repr__()
    
    
    def _checkNodesEqual(node1:RankPairTreeNode, node2:RankPairTreeNode):
        assert type(node1) == type(node2)
        assert node1.name == node2.name
        assert node1.data == node2.data
        assert len(node1.children) == len(node2.children)
        for i, childTuple in enumerate(zip(node1.children, node2.children)):
            _checkNodesEqual(childTuple[0], childTuple[1])
    
    _checkNodesEqual(rankTree.treeState, copyTreeFromJson.treeState)
    
    pass


def test_ranktree_can_store_multiple_domains():
    urls = [
        'https://groceries.asda.com/promotion/2-for-7/ls91300', 
        'https://money.asda.com/insurance/car-insurance'
    ]
    rankTree = RankPairTree(urls[0])
    for url in urls[1:]:
        rankTree.embedUrl(url)
    
    assert rankTree.treeState.name == RankPairTree.TREE_ROOT_MULTI_DOMAIN_NAME
    
    assert rankTree.treeState.children[0].name == 'https://groceries.asda.com'
    assert rankTree.treeState.children[1].name == 'https://money.asda.com'
    assert len(rankTree.treeState.children) == 2
    
    assert rankTree.depth == 5
    
def test_ranktree_can_parse_query():
    urls = [
        'https://money.asda.com/insurance/car-insurance',
        # 'https://money.asda.com/insurance/car-insurance?utm_source=ghs&utm_medium=footer&utm_campaign=car-insurance',
        'https://money.asda.com/insurance/car-insurance/?utm_source=ghs&utm_medium=footer&utm_campaign=car-insurance',
    ]
    rankTree = RankPairTree(urls[0])
    for url in urls[1:]:
        rankTree.embedUrl(url)
    
    assert rankTree.depth == 9
    
def test_ranktree_can_be_ranked():
    urls = [
        'https://groceries.asda.com', 
        'https://groceries.asda.com', 
        'https://groceries.asda.com/promotion/2-for-7/ls91300', 
        'https://groceries.asda.com/promotion/3-for-1/87435', 
        'https://groceries.asda.com/promotion/buy-one-get-one-free/xt9875', 
        'https://groceries.asda.com/product/1000338629556', 
        'https://groceries.asda.com/super_dept/veganuary/1215686171560', 
        'https://groceries.asda.com/cat/fresh-food-bakery/103099', 
        'https://groceries.asda.com/product/1000334423970', 
        'https://groceries.asda.com/cat/fresh-food-bakery/107823', 
        'https://groceries.asda.com/cat/fresh-food-bakery/997463', 
        'https://groceries.asda.com/cat/lader/123765', 
        'https://groceries.asda.com/product/18883', 
        'https://groceries.asda.com/product/1000330481079', 
        'https://groceries.asda.com/product/1000237774511', 
        'https://groceries.asda.com/cat/lader/198354', 
        'https://groceries.asda.com/event/gino_dacampo_view_all',
    ]
    rankTree = RankPairTree(urls[0])
    for url in urls[1:]:
        rankTree.embedUrl(url)
    treeRank = rankTree.treeRank
    assert treeRank == RankPairTreeRank(**{
        'isRegexNode':True,
        'pathFrequency': 8, 
        'regexNodesInTreeDescendency': 3,
        'fullUrl': 'https://groceries.asda.com/<regex>^[A-Za-z]+$</regex>/<regex>^[0-9A-Za-z\\-]+$</regex>/<regex>^[0-9A-Za-z]+$</regex>'
    })
    
def test_ranktree_subnode_can_be_ranked():
    urls = [
        'https://groceries.asda.com', 
        'https://groceries.asda.com', 
        'https://groceries.asda.com/promotion/2-for-7/ls91300', 
        'https://groceries.asda.com/promotion/3-for-1/87435', 
        'https://groceries.asda.com/promotion/buy-one-get-one-free/xt9875', 
        'https://groceries.asda.com/product/1000338629556', 
        'https://groceries.asda.com/super_dept/veganuary/1215686171560', 
        'https://groceries.asda.com/cat/fresh-food-bakery/103099', 
        'https://groceries.asda.com/product/1000334423970', 
        'https://groceries.asda.com/cat/fresh-food-bakery/107823', 
        'https://groceries.asda.com/cat/fresh-food-bakery/997463', 
        'https://groceries.asda.com/cat/lader/123765', 
        'https://groceries.asda.com/product/18883', 
        'https://groceries.asda.com/product/1000330481079', 
        'https://groceries.asda.com/product/1000237774511', 
        'https://groceries.asda.com/cat/lader/198354', 
        'https://groceries.asda.com/event/gino_dacampo_view_all/?sid=uxvtr',
        'https://groceries.asda.com/event/gino_dacampo_view_all/?sid=1834f',
    ]
    rankTree = RankPairTree(urls[0])
    for url in urls[1:]:
        rankTree.embedUrl(url)
    
    
    productChild = next((c for c in rankTree.children if c.name == 'product'),None)
    assert productChild is not None
    treeRank = productChild.treeRank
    assert treeRank == RankPairTreeRank(**{
        'isRegexNode':True,
        'pathFrequency': 5, 
        'regexNodesInTreeDescendency': 1,
        'fullUrl': 'https://groceries.asda.com/product/<regex>^[0-9]+$</regex>'
    })
    eventChild = next((c for c in rankTree.children if c.name == 'event'),None)
    assert eventChild is not None
    treeRank = eventChild.treeRank
    assert treeRank == RankPairTreeRank(**{
        'isRegexNode': True,
        'pathFrequency': 2, 
        'regexNodesInTreeDescendency': 1,
        'fullUrl': 'https://groceries.asda.com/event/gino_dacampo_view_all/?sid=<regex>^[0-9A-Za-z]+$</regex>'  
    })
    
