
import abc
import logging
import re
from collections import defaultdict
from pprint import pformat

import requests
from bs4 import BeautifulSoup
from file_appender import (JsonFileAppender,
                           TxtFileAppender)
from lxml import etree
# from progress.bar import Bar
# from progress.counter import Counter
from progress.spinner import Spinner
from py_utils import exception_to_string
from rank_pair_tree import RankPairTree
from selenium.webdriver import Safari
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium_interops import get_tag_ancestors_lxml, get_tag_ancestors_selenium, is_results_page, seleniumTryClickWebEl
from selenium.common.exceptions import TimeoutException
from url_scraper_requests_base import _BaseScraper, UrlLinkScraperRequestsBase
from url_props import UrlProps, CanUseRawHTMLRequests

class UrlLinkScraperSeleniumBase(UrlLinkScraperRequestsBase):
    '''Class to scrape urls using an algorithm that specifies how the engine will discover more urls to scrape
        
        The class uses browser emulation _when necessary_ to render pages.'''

    def __init__(self) -> None:
        super().__init__()
        self.useSelenium = True
        self.driver = Safari()
        self.driver.implicitly_wait(10)
        self._BASE_WINDOW_HANDLE_LAZY = self.driver.current_window_handle
        self._closeExtraSeleniumWebWindows()

    def _closeExtraSeleniumWebWindows(self):
        if len(self.driver.window_handles) > 1 and self._BASE_WINDOW_HANDLE_LAZY in self.driver.window_handles:
            for i, w in enumerate(self.driver.window_handles):
                if w != self._BASE_WINDOW_HANDLE_LAZY:
                    self.driver.switch_to.window(w)
                    self.driver.close()
            self.driver.switch_to.window(self._BASE_WINDOW_HANDLE_LAZY)
        assert self._BASE_WINDOW_HANDLE_LAZY in self.driver.window_handles, 'BASE_WINDOW_HANDLE_LAZY not in driver.window_handles'
        assert len(
            self.driver.window_handles) == 1, f'{type(self.driver)} should only have 1 window open.'

    def find_and_agree_cookies(self):
        cookiesAgreed = False

        def _f(btnText): return f"//*[text()='{btnText}']"
        agreebtns:list[WebElement] = self.driver.find_elements(by=By.XPATH, value=_f('I agree'))
        agreebtns += self.driver.find_elements(by=By.XPATH, value=_f('I Accept'))
        btn_ids = None
        if agreebtns:
            btn_ids = [agreebtn.get_attribute('id') for agreebtn in agreebtns if agreebtn.get_attribute('id')]
        if not btn_ids:
            agreebtns += self.driver.find_elements(
                by=By.XPATH, value=_f('Allow All'))
            if agreebtns:
                btn_ids = [agreebtn.get_attribute(
                    'id') for agreebtn in agreebtns if agreebtn.get_attribute('id')]
            else:
                btn_ids = []

        if btn_ids:
            for btn_id in btn_ids:
                btn = self.driver.find_element(by=By.ID, value=btn_id)
                if btn.is_displayed():
                    def check_clicked(wElem:WebElement): return not wElem.is_displayed()
                    if not seleniumTryClickWebEl(btn, check_clicked):
                        # driver.execute_script(f'$(\'#{btn_id}\').click()')
                        self.driver.execute_script(
                            f'document.getElementById(\'{btn_id}\').click()')
            cookiesAgreed = True
        elif agreebtns:
            for btn in agreebtns:
                btn.click()

        return cookiesAgreed

    def cookieCheckNeeded(self, urlDomain: str):

        if self._domainsHit[urlDomain] < self.maxDomainHitsCookieCheck:
            _checkCookies = True
        else:
            _checkCookies = False
        return _checkCookies
    
    def loadPageHtmlWithRequests(self, rootUrl: str):
        '''
        Returns a tuple of Safari and DomObject result of parsing that soup
        '''
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
        dom: etree._Element = etree.HTML(str(soup), parser=None)
        return soup, dom

    def loadPageHtmlWithSelenium(self, rootUrl: str, checkCookies: bool = False):
        '''
        Returns a tuple of WebDriver and bool to reflect if cookies are agreed
        '''
        if self.driver.current_url != rootUrl:
            try:
                self.driver.get(rootUrl)
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

        return self.driver, cookiesAgreed

    def _urlDiscoverySelenium(self, rootUrl: str, driver: Safari, checkCookies: bool = False):
        '''Discover all anchor tags within page HTML using Selenium'''
        _driver, cookiesAgreed = self.loadPageHtmlWithSelenium(
            rootUrl=rootUrl,
            checkCookies=checkCookies
        )

        property_page_links: list[str] = []

        try:
            property_page_divs = driver.find_elements(
                by=By.XPATH, value=self.link_xpath_selector)

            for div in property_page_divs:
                ancestors = get_tag_ancestors_selenium(
                    div, lambda we: (we.tag_name, we.get_attribute('href')))
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
        '''Discover all anchor tags within page HTML using requests HTML'''
        soup, dom = self.loadPageHtmlWithRequests(rootUrl=rootUrl)

        property_page_links: list[str] = []
        try:
            property_page_divs = dom.xpath(self.link_xpath_selector)

            for div in property_page_divs:
                ancestors = get_tag_ancestors_lxml(
                    div, lambda tag: (tag.tag, tag.attrib.get('href')))
                if any((d[0] == 'a' for d in ancestors)):
                    atag_href = next((d[1] for d in ancestors if d[0] == 'a'))
                    property_page_links.append(atag_href)

        except Exception as e:
            logging.error(exception_to_string(e))

        urlProps = UrlProps(property_page_links, [])
        return urlProps

    def scrapeUrlWithSelenium(self, url: str) -> Safari:
        ''''''
        self.maxDomainHitsCookieCheck = 5
        urlDomain = self.registerNewDomains(rootUrl=url)

        driverType = 'selenium'
        logging.info(f'urlDiscovery[{driverType}]: {url}')

        _checkCookies = True
        if urlDomain is not None:
            _checkCookies = self.cookieCheckNeeded(urlDomain=urlDomain)

        _driver, cookiesAgreed = self.loadPageHtmlWithSelenium(
            rootUrl=url, checkCookies=_checkCookies)

        if cookiesAgreed and urlDomain:
            # Stop checking for cookies:
            self._domainsHit[urlDomain] = self.maxDomainHitsCookieCheck
            
        return _driver
        
    def scrapeUrlWithRequests(self, url: str):
        ''''''
        driverType = 'RequestsRawHTML'
        logging.info(f'urlDiscovery[{driverType}]: {url}')

        return self.loadPageHtmlWithRequests(
            rootUrl=url
            )
    
    def urlDiscovery(self, rootUrl: str, driver: Safari | None = None, useSelenium: bool = False, requiredSubDomain: str | None = None):

        self.maxDomainHitsCookieCheck = 5
        urlDomain = self.registerNewDomains(rootUrl=rootUrl)
        
        driverType = 'selenium' if useSelenium else 'RequestsRawHTML'
        if driver is None:
            driver = self.driver if useSelenium else None
            
        logging.info(f'urlDiscovery[{driverType}]: {rootUrl}')
        if useSelenium and driver is not None:
            _checkCookies = True
            if urlDomain is not None:
                _checkCookies = self.cookieCheckNeeded(urlDomain=urlDomain)

            result = self._urlDiscoverySelenium(
                rootUrl=rootUrl, driver=driver, checkCookies=_checkCookies)

            if result.cookiesAgreed and urlDomain:
                # Stop checking for cookies:
                self._domainsHit[urlDomain] = self.maxDomainHitsCookieCheck

        else:
            result = self._urlDiscoveryHTMLOnly(rootUrl)

        def _removeEmptyUrls(result: list[str]):
            return [url for url in result if url is not None and ((requiredSubDomain is not None and requiredSubDomain in url) or requiredSubDomain is None)]

        return UrlProps(
            anchorTagHrefs=_removeEmptyUrls(result.anchorTagHrefs),
            embeddedScriptAndAnchorTagHrefs=_removeEmptyUrls(
                result.embeddedScriptAndAnchorTagHrefs)
        )

    @abc.abstractproperty
    def link_xpath_selector(self):
        # return '//div[@class="item-title"]'
        return '//a'

    @abc.abstractmethod
    def adjust_page_number(self, page_number: int, set_if_none: bool = False):
        pass

    @abc.abstractmethod
    def list_page_urls(self, NPages: int, append_if_not_results_page: bool = False) -> list[str]:
        pass

    @abc.abstractmethod
    def get_page_number(self) -> int | None:
        pass

    def _urlNeedsJsFromExpectedAnchorCount(self, exampleUrl: str, url: str, expectedHtmlProps: UrlProps, urlProps: UrlProps, urlDict: dict[str, UrlProps]):
        '''Function to check if a url (@exampleUrl) requires browser emulation (selenium) to load the full html by running js on the page
            
            logic uses expected number of anchor tags present in returned html for @exampleUrl
            
            returns `False` for `CanUseRawHTMLRequests.No` and `True` for `CanUseRawHTMLRequests.Yes`
        '''
        if len(expectedHtmlProps.anchorTagHrefs) > 0 \
                and (len(urlProps.anchorTagHrefs) / len(expectedHtmlProps.anchorTagHrefs)) < 0.5:
            urlDict[exampleUrl].canUseRawHTMLRequests = CanUseRawHTMLRequests.No
            return True
        else:
            urlDict[exampleUrl].canUseRawHTMLRequests = CanUseRawHTMLRequests.Yes
            return False

    def urlNeedsJs(self, url: str):
        '''Function to check if a url (@url) requires browser emulation (selenium) to load the full html by running js on the page
            
            logic uses expected number of anchor tags present in returned html for @exampleUrl
        '''
        selUrlProps = self._urlDiscoverySelenium(
            rootUrl=url,
            driver=self.driver,
            checkCookies=True,
        )
        requestsUrlProps = self._urlDiscoveryHTMLOnly(
            rootUrl=url,
        )
        
        if len(selUrlProps.anchorTagHrefs) > 0 \
                and (len(requestsUrlProps.anchorTagHrefs) / len(selUrlProps.anchorTagHrefs)) < 0.5:
            return True
        else:
            return False

    def run_url_discovery_engine(self, urlPioneer: set[str], domain: str, subDomainReq: str | None = None):
        driver = self.driver
        try:
            urlsToSearch = [domain]
            newurls: set[str] = set()

            spinner = Spinner(message='Urls discovered')
            urlTree: RankPairTree = RankPairTree()
            urlDict: dict[str, UrlProps] = defaultdict(
                lambda: UrlProps([], []))

            if domain not in driver.current_url:
                driver.get(domain)

            newurls = set()
            # Get the number of pages and then loop over each page adding more urls
            (url_is_results_page, num_results) = is_results_page(
                driver, xpath_selector=self.link_xpath_selector)
            if url_is_results_page:
                N = num_results
                urlsToSearch = self.list_page_urls(
                    NPages=N, append_if_not_results_page=True)
            else:
                N = 1

            for url in urlsToSearch:
                url = url.removesuffix('/')
                _useSeleniumForThisUrl = self.useSelenium
                exampleUrl = urlTree.getExampleGeneralisationOf(
                    url, removeRegexNodes=True)
                # TODO: Fix this function as taking way too long!
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
                    # Check if selenium is necesary,
                    self._urlNeedsJsFromExpectedAnchorCount(
                        exampleUrl=exampleUrl,
                        url=url,
                        expectedHtmlProps=expectedHtmlProps,
                        urlProps=urlProps,
                        urlDict=urlDict
                    )  # returns false for CanUseRawHTMLRequests.No and true for CanUseRawHTMLRequests.Yes
                    if urlDict[exampleUrl].canUseRawHTMLRequests == CanUseRawHTMLRequests.No:
                        _useSeleniumForThisUrl = True
                        urlProps = self.urlDiscovery(
                            url, driver, useSelenium=_useSeleniumForThisUrl, requiredSubDomain=subDomainReq)
                        urlDict[url] = urlProps
                        urlDict[url].canUseRawHTMLRequests = CanUseRawHTMLRequests.No
                    else:
                        urlDict[url].canUseRawHTMLRequests = CanUseRawHTMLRequests.Yes

                else:
                    urlProps = self.urlDiscovery(
                        url, driver, useSelenium=_useSeleniumForThisUrl, requiredSubDomain=subDomainReq)
                urlDict[url] = urlProps

                newurls = newurls.union(
                    (urlProps.anchorTagHrefs + urlProps.embeddedScriptAndAnchorTagHrefs))

                if isinstance(self._saveFileWrap, JsonFileAppender):
                    self._saveFileWrap.write({'urls': {url: list(newurls)}})
                elif isinstance(self._saveFileWrap, TxtFileAppender):
                    self._saveFileWrap.write(
                        f'\n{url}\n-\t' + '\n-\t'.join(newurls))

            urlsToSearch = list(newurls - urlPioneer)

            urlPioneer = urlPioneer.union(urlsToSearch)

            return urlPioneer

        except Exception as e:
            logging.error(e)
            logging.error(exception_to_string(e))
            print(e)
            if self._fileToClose != False and self._saveFileWrap is not None:
                self._saveFileWrap.closeStream()

            return None


class InfoScraperRequestsBase(_BaseScraper):
    '''Class to scrape web pages using a pattern matching algorithm to extract information from the raw html
        
        The class is limited to raw HTML from requests'''

    def __init__(self) -> None:
        super().__init__()

    def run_scraper(self):
        urls = self.get_urls_to_scrape()
        results = {}
        for url in urls:
            soup = self._request_url_to_soup(url=url)
            content = self.extract_content(soup=soup)
            results[url] = content

            if isinstance(self._saveFileWrap, JsonFileAppender):
                self._saveFileWrap.write(
                    {'urls': {url: content}})
            elif isinstance(self._saveFileWrap, TxtFileAppender):
                self._saveFileWrap.write(
                    f'\n{url}\n-\t' + pformat(content))

        return results

    @abc.abstractmethod
    def get_urls_to_scrape(self) -> list[str]:
        '''Set the urls that the scraper will request'''
        pass

    @abc.abstractmethod
    def extract_content(self, soup: BeautifulSoup) -> dict[str, str]:
        '''method to extract key information using pattern matching from soup'''
        pass
