from bs4 import Tag


def nth_of_type(elem:Tag):
    count, curr = 0, 0
    _elem = elem.find_parent()
    if not _elem:
        return None
    for i, e in enumerate(_elem.find_all(recursive=False), 1):
        if e.name == _elem.name:
            count += 1
        if e == _elem:
            curr = i
    return '' if count == 1 else ':nth-child({})'.format(curr)

def _getElemSelector(elem:Tag):
    selector = elem.name
    # otherAttrs = set(elem.attrs.keys()).difference('class')
    if elem['class']:
        selector += '.' + '.'.join(elem['class'])

    for otherAtr in elem.attrs.keys():
        if isinstance(elem[otherAtr], list) and otherAtr == 'class':
            pass
        else:
            selector += f'[{otherAtr}="{elem[otherAtr]}"]'
    
    if str(elem.string) and not elem.children:
        selector += f':contains("{elem.text}")'
    
    return selector# + nth_of_type(elem)

def getCssPath(elem:Tag, maxTreeSize:int = 100):
    if elem.attrs.get('id'):
        return '#' + elem.attrs['id']

    rv = [_getElemSelector(elem)]
    _i = 0
    while _i < maxTreeSize:
        _i += 1
        _elem = elem.find_parent()
        if not _elem or _elem.name == '[document]':
            return '>'.join(rv[::-1])
        elif _i >= maxTreeSize:
            return ' ... ' + ' > '.join(rv[::-1])
        elif _elem.attrs.get('id'):
            return '#' + _elem.attrs['id'] + ' > '.join(rv[::-1])
        elem = _elem
        rv.append(_getElemSelector(elem))
