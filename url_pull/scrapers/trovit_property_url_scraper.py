from collections import defaultdict
from enum import Enum
from types import NoneType
from typing import Iterable, Literal, TypeVar
import abc
import re
import logging
import warnings
from selenium.webdriver import Safari
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import requests
from bs4 import BeautifulSoup
from lxml import etree

from progress.spinner import Spinner
from progress.counter import Counter
from progress.bar import Bar
from py_utils import exception_to_string, nullPipe
from selenium_interops import get_tag_ancestors_lxml, get_tag_ancestors_selenium
from url_browse import UrlProps, UrlScraperBase

from url_discovery import seleniumTryClickWebEl
from file_appender import IFileAppender, DummyFileAppender, TxtFileAppender, JsonFileAppender
from url_parser import ParsedUrlParser, URL_RE_PATTERN
from rank_pair_tree import RankPairTree

class TrovitPropertyUrlScraper(UrlScraperBase):

    def __init__(self, useSelenium: bool) -> None:
        super().__init__(useSelenium)
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

    def _urlDiscoverySelenium(self, rootUrl: str, driver: Safari, checkCookies=False):
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
            property_page_divs = driver.find_elements_by_xpath(
                self.link_xpath_selector)

            for div in property_page_divs:
                ancestors = get_tag_ancestors_selenium(div)
                if any((d.tag_name == 'a' for d in ancestors)):
                    atag = next((d for d in ancestors if d.tag_name == 'a'))
                    property_page_links.append(atag.get_attribute('href'))

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
                ancestors = get_tag_ancestors_lxml(div)
                if any((d.tag == 'a' for d in ancestors)):
                    atag = next((d for d in ancestors if d.tag == 'a'))
                    property_page_links.append(atag.attributes('href'))

        except Exception as e:
            logging.error(exception_to_string(e))

        urlProps = UrlProps(property_page_links, [])
        return urlProps
