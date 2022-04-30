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
from url_browse import CanUseRawHTMLRequests, UrlProps, UrlScraperSeleniumBase

from url_discovery import seleniumTryClickWebEl
from file_appender import IFileAppender, DummyFileAppender, TxtFileAppender, JsonFileAppender
from url_parser import ParsedUrlParser, URL_RE_PATTERN
from rank_pair_tree import RankPairTree


class UrlSpiderScraper(UrlScraperSeleniumBase):
    '''Perform all url scraping with additional url parsing and adding to a rank tree to manage the state of urls already processed'''
    maxSpiderExplodeAllowed: Literal[3] = 3
    defaultSpiderExplodeDepth: Literal[3] = 3

    def __init__(self, maxSubUrls: int = -1) -> None:
        super().__init__()
        self.maxSubUrls = maxSubUrls

    def run_url_discovery(self, domain: str, subDomainReq: str, saveOut: str | None = None):
        urlPioneer = self.open_file_storage_stream(saveOut=saveOut)
        urlPioneer = self.run_spider_search_algorithm(
            urlPioneer=urlPioneer, domain=domain, subDomainReq=subDomainReq, explodeTimes=UrlSpiderScraper.defaultSpiderExplodeDepth)

    def run_spider_search_algorithm(self, urlPioneer: set[str], domain: str, subDomainReq: str, explodeTimes: int = defaultSpiderExplodeDepth):
        driver = self.driver

        if UrlSpiderScraper.maxSpiderExplodeAllowed < explodeTimes:
            warnings.warn(
                f'Warning: Max allowed Spider Explode to depth of: {UrlSpiderScraper.maxSpiderExplodeAllowed}')

        _explodeTimes = max(
            1, min(UrlSpiderScraper.defaultSpiderExplodeDepth, explodeTimes))

        try:
            urlsToSearch = [domain]
            newurls: set[str] = set()

            _i = 0  # explosion depth index
            spinner = Spinner(message='Urls discovered')
            urlTree: RankPairTree = RankPairTree()
            urlDict: dict[str, UrlProps] = defaultdict(
                lambda: UrlProps([], []))

            while _i < _explodeTimes:
                _i += 1
                newurls = set()
                for url in urlsToSearch:
                    _useSeleniumForThisUrl = self.useSelenium
                    exampleUrl = urlTree.getExampleGeneralisationOf(
                        url, removeRegexNodes=True)
                    urlTree.embedUrl(url)
                    if urlDict[exampleUrl].canUseRawHTMLRequests != CanUseRawHTMLRequests.Unknown:
                        _useSeleniumForThisUrl = bool(
                            urlDict[exampleUrl].canUseRawHTMLRequests == CanUseRawHTMLRequests.No)
                        urlProps = self.urlDiscovery(
                            url, driver, useSelenium=_useSeleniumForThisUrl, requiredSubDomain=subDomainReq)
                    elif exampleUrl is not None:
                        _useSeleniumForThisUrl = False
                        expectedHtmlProps: UrlProps = urlDict[exampleUrl]
                        urlProps = self.urlDiscovery(
                            url, driver, useSelenium=_useSeleniumForThisUrl, requiredSubDomain=subDomainReq)
                        if len(expectedHtmlProps.anchorTagHrefs) > 0 and (len(urlProps.anchorTagHrefs) / len(expectedHtmlProps.anchorTagHrefs)) < 0.5:
                            urlDict[exampleUrl].canUseRawHTMLRequests = CanUseRawHTMLRequests.No
                            _useSeleniumForThisUrl = True
                            urlProps = self.urlDiscovery(
                                url, driver, useSelenium=_useSeleniumForThisUrl, requiredSubDomain=subDomainReq)
                            urlDict[url] = urlProps
                            urlDict[url].canUseRawHTMLRequests = CanUseRawHTMLRequests.No
                        else:
                            urlDict[url].canUseRawHTMLRequests = CanUseRawHTMLRequests.Yes
                            urlDict[exampleUrl].canUseRawHTMLRequests = CanUseRawHTMLRequests.Yes
                    else:
                        urlProps = self.urlDiscovery(
                            url, driver, useSelenium=_useSeleniumForThisUrl, requiredSubDomain=subDomainReq)
                    urlDict[url] = urlProps

                    newurls = newurls.union(
                        (urlProps.anchorTagHrefs + urlProps.embeddedScriptAndAnchorTagHrefs))

                    if isinstance(self._saveFileWrap, JsonFileAppender):
                        self._saveFileWrap.write(
                            {'urls': {url: list(newurls)}})
                    elif isinstance(self._saveFileWrap, TxtFileAppender):
                        self._saveFileWrap.write(
                            f'\n{url}\n-\t' + '\n-\t'.join(newurls))
                urlsToSearch = list(newurls - urlPioneer)

                if self.maxSubUrls > -1:
                    urlsToSearch = urlsToSearch[:self.maxSubUrls]
                urlPioneer = urlPioneer.union(urlsToSearch)

                spinner.message = f'{len(urlPioneer)} urls discovered by explosion #{_i}'

            return urlPioneer
        except Exception as e:
            logging.error(e)
            logging.error(exception_to_string(e))
            print(e)
            if self._fileToClose != False and self._saveFileWrap is not None:
                self._saveFileWrap.closeStream()

            return None

    def urlDiscovery(self, rootUrl: str, driver: Safari | None = None, useSelenium: bool = False, requiredSubDomain: str | None = None):
        maxDomainHitsCookieCheck = 5
        driverType = 'selenium' if useSelenium else 'bs4'
        logging.info(f'urlDiscovery[{driverType}]: {rootUrl}')

        if useSelenium and driver is not None:
            if any(rootUrl.startswith(u) for u in self._domainsHit.keys() if bool(u)):
                urlDomain = next((u
                                 for u in self._domainsHit.keys() if bool(u) and rootUrl.startswith(u)))
                self._domainsHit[urlDomain] += 1
            else:
                try:
                    urlDomainMatch = re.match(
                        ParsedUrlParser.URL_DOMAIN_MATCH, rootUrl)
                    if urlDomainMatch:
                        urlDomain = urlDomainMatch[0]
                        if urlDomain not in self._domainsHit.keys():
                            self._domainsHit[urlDomain] = 1
                        else:
                            self._domainsHit[urlDomain] += 1
                except:
                    urlDomain = None
            if urlDomain:
                if self._domainsHit[urlDomain] < maxDomainHitsCookieCheck:
                    _checkCookies = True
                else:
                    _checkCookies = False

            result = self._urlDiscoverySelenium(
                rootUrl=rootUrl, driver=driver, checkCookies=_checkCookies)

            if result.cookiesAgreed and urlDomain:
                # Stop checking for cookies:
                self._domainsHit[urlDomain] = maxDomainHitsCookieCheck

        else:
            result = self._urlDiscoveryHTMLOnly(rootUrl)

        def _removeEmptyUrls(result: list[str]):
            return [url for url in result if url is not None and ((requiredSubDomain is not None and requiredSubDomain in url) or requiredSubDomain is None)]

        return UrlProps(
            anchorTagHrefs=_removeEmptyUrls(result.anchorTagHrefs),
            embeddedScriptAndAnchorTagHrefs=_removeEmptyUrls(
                result.embeddedScriptAndAnchorTagHrefs)
        )

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

        anchorTagUrls: list[str] = []
        scriptTagUrlEmbeds: list[str] = []
        onClickAttributeUrlEmbeds: list[str] = []
        try:
            anchorTagUrls = [we.get_attribute(
                'href') for we in driver.find_elements(By.TAG_NAME, 'a')]
            scriptTagUrlEmbeds = [nullPipe(re.match(URL_RE_PATTERN, str(
                we.text)), lambda x: x.string if x is not None else '') for we in driver.find_elements(By.TAG_NAME, 'script')]
            onClickAttributeUrlEmbeds = [nullPipe(re.match(URL_RE_PATTERN, we.get_attribute(
                'onClick')), lambda x: x.string if x is not None else '') for we in driver.find_elements(By.CSS_SELECTOR, '[onClick]') if we.get_attribute('onClick')]
        except TimeoutException as timeoutExcp:
            if not anchorTagUrls:
                logging.warn(
                    f'Selenium failed to grab anchor tag urls for {rootUrl}.')
                anchorTagUrls = []
            if not scriptTagUrlEmbeds:
                logging.warn(
                    f'Selenium failed to grab script Tag Url Embeds for {rootUrl}.')
                scriptTagUrlEmbeds = []
            if not onClickAttributeUrlEmbeds:
                logging.warn(
                    f'Selenium failed to grab onClick Attribute Url Embeds for {rootUrl}.')
                onClickAttributeUrlEmbeds = []
        except Exception as e:
            logging.error(exception_to_string(e))
        # Button urls should be included in the onClick handler above.
        # buttonTagUrls = [we for we in driver.find_elements(By.TAG_NAME, 'button')]

        # urlPioneer = anchorTagUrls + scriptTagUrlEmbeds + onClickAttributeUrlEmbeds
        # return urlPioneer
        urlProps = UrlProps(anchorTagUrls, scriptTagUrlEmbeds +
                            onClickAttributeUrlEmbeds, cookiesAgreed=cookiesAgreed)
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

        anchorTagUrls = [we.get('href') for we in soup.find_all('a')]
        scriptTagUrlEmbeds = [nullPipe(re.match(URL_RE_PATTERN, str(nullPipe(
            we.string, lambda y: y, returnIfnull=None))), lambda x: x.string if x is not None else '') for we in soup.find_all('script')]
        onClickAttributeUrlEmbeds = [nullPipe(re.match(URL_RE_PATTERN, we.get(
            'onClick')), lambda x: x.string if x is not None else '') for we in soup.find_all(onClick=True) if we.get('onClick')]
        # Button urls should be included in the onClick handler above.
        # buttonTagUrls = [we for we in driver.find_elements(By.TAG_NAME, 'button')]

        # urlPioneer = anchorTagUrls + scriptTagUrlEmbeds + onClickAttributeUrlEmbeds
        urlProps = UrlProps(
            anchorTagUrls, scriptTagUrlEmbeds + onClickAttributeUrlEmbeds)
        return urlProps
