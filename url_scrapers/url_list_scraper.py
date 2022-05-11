import logging
import re

import requests
from bs4 import BeautifulSoup
from lxml import etree
from py_utils import exception_to_string, int_to_pos_int, nullPipe
# from rank_pair_tree import RankPairTree
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Safari
from selenium.webdriver.common.by import By
from selenium_interops import (get_tag_ancestors_lxml,
                               get_tag_ancestors_selenium)

from url_scraper_base import UrlLinkScraperSeleniumBase, UrlProps


class UrlListScraper(UrlLinkScraperSeleniumBase):

    def __init__(self) -> None:
        super().__init__()
        self._page_number: int = 0
        self.maxDomainHitsCookieCheck = 5

    @property
    def link_xpath_selector(self):
        return '//div[@class="item-title"]'
