import abc
import logging
import re
import warnings
from collections import defaultdict
from enum import Enum
from types import NoneType
from typing import Iterable, Literal, TypeVar

import requests
from bs4 import BeautifulSoup
from file_appender import (DummyFileAppender, IFileAppender, JsonFileAppender,
                           TxtFileAppender)
from lxml import etree
from progress.bar import Bar
from progress.counter import Counter
from progress.spinner import Spinner
from py_utils import exception_to_string, int_to_pos_int, nullPipe
from rank_pair_tree import RankPairTree
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Safari
from selenium.webdriver.common.by import By
from selenium_interops import (get_tag_ancestors_lxml,
                               get_tag_ancestors_selenium)
from url_browse import UrlProps, UrlScraperSeleniumBase
from url_discovery import seleniumTryClickWebEl
from url_parser import URL_RE_PATTERN, ParsedUrlParser


class TrovitPropertyUrlScraper(UrlScraperSeleniumBase):

    def __init__(self) -> None:
        super().__init__()
        self._page_number: int = 0
        self.maxDomainHitsCookieCheck = 5

    @property
    def link_xpath_selector(self):
        return '//div[@class="item-title"]'

    def link_discovery_algo(self):
        pass

    def run_url_discovery(self, domain: str, subDomainReq: str, saveOut: str | None = None):
        urlPioneer = self.open_file_storage_stream(saveOut=saveOut)
        urlPioneer = set()
        self.run_url_discovery_engine(
            urlPioneer=urlPioneer, domain=domain, subDomainReq=subDomainReq)

    def next_page(self):
        assert self.driver is not None
        url = self.driver.current_url

        def replacer(match: re.Match):
            next_page_no = int(match[1]) + 1
            return f'page.{next_page_no}'
        next_url = re.sub(r'page\.([0-9]+)', replacer, url)
        self.driver.get(next_url)
        
    def get_page_number(self):
        assert self.driver is not None
        url = self.driver.current_url
        
        page_match = re.match(r'page\.([0-9]+)', url)
        
        return int(page_match[1]) if page_match and page_match[1] else None
        
    def adjust_page_number(self, page_number:int, set_if_none:bool=False):
        assert self.driver is not None
        url = self.driver.current_url
        
        page_number = int_to_pos_int(page_number,zero_allowed=False)

        def replacer(match: re.Match):
            return f'page.{page_number}'
        
        page_match = re.match(r'page\.([0-9]+)', url)
        if page_match:
            next_url = re.sub(r'page\.([0-9]+)', replacer, url)
            self.driver.get(next_url)
        elif set_if_none:
            spacer = '' if url.endswith('/') else '/'
            next_url = f'{url}{spacer}page.{page_number}/'
            self.driver.get(next_url)
        return page_number
    
    def list_page_urls(self,NPages:int,append_if_not_results_page:bool=False):
        assert self.driver is not None
        url = self.driver.current_url
        
        NPages = int_to_pos_int(NPages,zero_allowed=False)
        page_nos = [i+1 for i in range(NPages)]
        
        def replacer_lam(page_number: int):
            return lambda match: f'page.{page_number}'
        
        page_match = re.match(r'page\.([0-9]+)', url)
        if page_match:
            next_urls = [re.sub(r'page\.([0-9]+)', replacer_lam(i), url) for i in page_nos]
        elif append_if_not_results_page:
            spacer = '' if url.endswith('/') else '/'
            next_urls = [f'{url}{spacer}page.{i}/' for i in page_nos]
        else:
            next_urls = []
        return next_urls
        
        

    def _urlDiscoverySelenium(self, rootUrl: str, driver: Safari, checkCookies:bool=False):
        try:
            driver.get(rootUrl)
        except Exception as e:
            logging.error(
                f'Selenium Fell over trying to get: {rootUrl} with a {type(e).__name__} exception.')
            logging.error(e)

        try:
            self._closeExtraSeleniumWebWindows()
        except Exception as e:
            logging.error(
                f'Selenium Fell over trying to close extra selenium windows in: {rootUrl} with a {type(e).__name__} exception.')

        cookiesAgreed = False
        if checkCookies:
            try:
                cookiesAgreed = self.find_and_agree_cookies()
            except Exception as e:
                logging.error(
                    f'Selenium Fell over trying to find and agree cookies in: {rootUrl} with a {type(e).__name__} exception.')

        property_page_links: list[str] = []

        try:
            property_page_divs = driver.find_elements(by=By.XPATH,value=
                self.link_xpath_selector)

            for div in property_page_divs:
                ancestors = get_tag_ancestors_selenium(div, lambda we: (we.tag_name, we.get_attribute('href')))
                if any((d[0] == 'A' for d in ancestors)):
                    atag_href = next((d[1] for d in ancestors if d[0] == 'A'))
                    property_page_links.append(atag_href)

        except TimeoutException as timeoutExcp:
            if not property_page_links:
                logging.warn(
                    f'Selenium failed to grab anchor tag urls for {rootUrl}.')
        except Exception as e:
            logging.error(exception_to_string(e))

        urlProps = UrlProps(property_page_links, [],
                            cookiesAgreed=cookiesAgreed)
        return urlProps

    def _urlDiscoveryHTMLOnly(self, rootUrl: str):

        # http://www.xhaus.com/headers -> View your headers in browser
        headers = {
            "User-agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36 Edg/96.0.1054.43'}
        if rootUrl.startswith('file:///'):
            with open(re.sub(r'^file:\/\/\/', '/', rootUrl), 'r') as f:
                pageContents = f.read()
        else:
            pageContents = requests.get(rootUrl, headers=headers).content
        # print(page.content)
        soup = BeautifulSoup(pageContents, 'html.parser')
        dom = etree.HTML(str(soup), parser=None)
        property_page_links: list[str] = []
        try:
            property_page_divs = dom.xpath(self.link_xpath_selector)

            for div in property_page_divs:
                ancestors = get_tag_ancestors_lxml(div, lambda tag: (tag.tag, tag.attrib.get('href')))
                if any((d[0] == 'a' for d in ancestors)):
                    atag_href = next((d[1] for d in ancestors if d[0] == 'a'))
                    property_page_links.append(atag_href)

        except Exception as e:
            logging.error(exception_to_string(e))

        urlProps = UrlProps(property_page_links, [])
        return urlProps
