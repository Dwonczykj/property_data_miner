from typing import TypeVar
from lxml.etree import _Element

T = TypeVar('T')


def xpath_element_if_exists(dom: _Element, selector: str, match_number: int = 0) -> _Element | None:
    selection = dom.xpath(selector)
    if not selection:
        return None
    elif len(selection) < abs(match_number):
        return None
    return selection[match_number]

def xpath_attr_if_exists(dom: _Element, selector: str, match_number: int = 0, attr: str = 'text', defaultRes: T = None) -> T | None:
    selected = xpath_element_if_exists(dom, selector, match_number)
    if selected is None:
        return defaultRes
    return getattr(selected,attr,defaultRes) if attr == 'text' else selected.get(attr,defaultRes)