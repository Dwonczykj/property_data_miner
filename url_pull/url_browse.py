
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
from py_utils import exception_to_string, nullPipe
from rank_pair_tree import RankPairTree
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Safari
from selenium.webdriver.common.by import By
from url_parser import URL_RE_PATTERN, ParsedUrlParser

from selenium_interops import (get_tag_ancestors_lxml,
                               get_tag_ancestors_selenium, is_results_page)
from url_discovery import seleniumTryClickWebEl


class CanUseRawHTMLRequests(Enum):
    No = -1
    Unknown = 0
    Yes = 1
    
    

class UrlProps():
    '''A class for determining characteristics of a url:
        - does the url require a browser emulator to render correctly using js
        - are there anchor tag refs on the page
        - are there cookies to agree on the page
        - are there scripts to load on the page
        '''
    def __init__(self, anchorTagHrefs:list[str]=[], embeddedScriptAndAnchorTagHrefs:list[str]=[], cookiesAgreed: bool = False) -> None:
        self.canUseRawHTMLRequests:CanUseRawHTMLRequests = CanUseRawHTMLRequests.Unknown
        self.anchorTagHrefs = anchorTagHrefs
        self.embeddedScriptAndAnchorTagHrefs = embeddedScriptAndAnchorTagHrefs
        self.cookiesAgreed = cookiesAgreed

    def getNumAnchorTags(self):
        return len(self.anchorTagHrefs)
    def getNumHrefsInScriptsAndButtons(self):
        return len(self.embeddedScriptAndAnchorTagHrefs)
    numAnchorTags = property(getNumAnchorTags)
    numHrefsInScriptsAndButtons = property(getNumHrefsInScriptsAndButtons)
    
    
class UrlScraperRequestsBase():
    '''Class to scrape urls using an algorithm that specifies how the engine will discover more urls to scrape
        
        The class is limited to raw HTML from requests'''
    def __init__(self) -> None:
        
        self._BASE_WINDOW_HANDLE_LAZY = ''
        self._domainsHit = defaultdict[str,int](int)
        self._saveFileWrap:IFileAppender|None=None
        self._fileToClose:bool=False
        self.useSelenium = False
        
    def open_file_storage_stream(self, saveOut: str | None = None):
        fileToClose = False
        saveFileWrap: IFileAppender
        urlPioneer = set()
        state = {}
        if saveOut is not None and saveOut.endswith('.txt'):
            fileToClose = True
            saveFileWrap = TxtFileAppender(saveOut[:-4]).openStream()
        elif saveOut is not None:
            fileToClose = True
            saveFileWrap = JsonFileAppender(saveOut).openStream()
            if saveFileWrap.containsData():
                state = saveFileWrap.loadData()
                if state is not None and hasattr(state, 'urls'):
                    urlPioneer = set(
                        UrlScraperRequestsBase._processState(state['urls']))
        else:
            saveFileWrap = DummyFileAppender('Dummy').openStream()
        self._saveFileWrap = saveFileWrap
        self._fileToClose = fileToClose
        return urlPioneer
        
    TX = TypeVar("TX", str, int, float, None, list, dict, bool)

    @staticmethod
    def _processState(state:TX):
        '''A method to allow us to reload the state of the url discovery class from a file so that we dont need to load (pull) the url history tree'''
        if isinstance(state, list) or isinstance(state,Iterable):
            return [u for s in state for u in UrlScraperRequestsBase._processState(s)]
        elif isinstance(state, dict):
            return [u for k in state.keys() for u in [k, *UrlScraperRequestsBase._processState(state[k])]]
        elif isinstance(state, str):
            return [state]
        elif isinstance(state, int) or isinstance(state, float) or isinstance(state, bool):
            return [str(state)]
        else:
            logging.error(f'Cant add to url_discovery state for new state of type: {type(state)}')
            return []
        
    def registerNewDomains(self, rootUrl: str):
        if any(rootUrl.startswith(u) for u in self._domainsHit.keys() if bool(u)):
            urlDomain = next(u
                             for u in self._domainsHit.keys()
                             if bool(u) and rootUrl.startswith(u))
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

        return urlDomain
    
    def run_url_discovery_engine(self, urlPioneer: set[str], domain: str, subDomainReq: str | None = None):
        
        try:
            urlsToSearch = [domain]
            newurls: set[str] = set()

            _i = 0  # explosion depth index
            spinner = Spinner(message='Urls discovered')
            urlTree: RankPairTree = RankPairTree()
            urlDict: dict[str, UrlProps] = defaultdict(
                lambda: UrlProps([], []))
            
            newurls = set()
            for url in urlsToSearch:
                
                exampleUrl = urlTree.getExampleGeneralisationOf(
                    url, removeRegexNodes=True)
                urlTree.embedUrl(url)
                urlProps = self.urlDiscovery(
                        url, requiredSubDomain=subDomainReq)
                
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
        
    def urlDiscovery(self, rootUrl: str, requiredSubDomain: str | None = None):
        
        logging.info(f'urlDiscovery[RequestsRawHTML]: {rootUrl}')

        urlDomain = self.registerNewDomains(rootUrl=rootUrl)
        result = self._urlDiscoveryHTMLOnly(rootUrl)

        def _removeEmptyUrls(result: list[str]):
            return [url for url in result if url is not None and ((requiredSubDomain is not None and requiredSubDomain in url) or requiredSubDomain is None)]

        return UrlProps(
            anchorTagHrefs=_removeEmptyUrls(result.anchorTagHrefs),
            embeddedScriptAndAnchorTagHrefs=_removeEmptyUrls(
                result.embeddedScriptAndAnchorTagHrefs)
        )
        
    @abc.abstractmethod
    def link_discovery_algo(self):
        '''A function that specifies how to pull urls to process from the landing page url that is initialised in the class's run_url_discovery function'''
        pass
    
    @abc.abstractmethod
    def _urlDiscoveryHTMLOnly(self, rootUrl: str) -> UrlProps:
        pass
        
class UrlScraperSeleniumBase(UrlScraperRequestsBase):
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
        agreebtns = self.driver.find_elements(by=By.XPATH,value=_f('I agree'))
        btn_ids = None
        if agreebtns:
            btn_ids = [agreebtn.get_attribute('id') for agreebtn in agreebtns]
        if not btn_ids:
            agreebtns = self.driver.find_elements(by=By.XPATH,value=_f('Allow All'))
            if agreebtns:
                btn_ids = [agreebtn.get_attribute(
                    'id') for agreebtn in agreebtns]
            else:
                btn_ids = []

        if btn_ids:
            for btn_id in btn_ids:
                btn = self.driver.find_element(by=By.ID, value=btn_id)
                if btn.is_displayed():
                    if not seleniumTryClickWebEl(btn):
                        # driver.execute_script(f'$(\'#{btn_id}\').click()')
                        self.driver.execute_script(
                            f'document.getElementById(\'{btn_id}\').click()')
            cookiesAgreed = True

        return cookiesAgreed
    
    def cookieCheckNeeded(self, urlDomain: str):

        if self._domainsHit[urlDomain] < self.maxDomainHitsCookieCheck:
            _checkCookies = True
        else:
            _checkCookies = False
        return _checkCookies

    def urlDiscovery(self, rootUrl: str, driver: Safari | None = None, useSelenium: bool = False, requiredSubDomain: str | None = None):
        self.maxDomainHitsCookieCheck = 5
        driverType = 'selenium' if useSelenium else 'RequestsRawHTML'
        logging.info(f'urlDiscovery[{driverType}]: {rootUrl}')

        urlDomain = self.registerNewDomains(rootUrl=rootUrl)
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
        return ''
    
    @abc.abstractmethod    
    def _urlDiscoverySelenium(self, rootUrl: str, driver: Safari, checkCookies=False) -> UrlProps:
        pass
    
    @abc.abstractmethod
    def _urlDiscoveryHTMLOnly(self, rootUrl: str) -> UrlProps:
        pass
    
    @abc.abstractmethod
    def adjust_page_number(self, page_number:int, set_if_none:bool=False):
        pass
    
    @abc.abstractmethod
    def list_page_urls(self,NPages:int,append_if_not_results_page:bool=False) -> list[str]:
        pass
    
    @abc.abstractmethod
    def get_page_number(self) -> int | None:
        pass
    
    def _urlNeedsJs(self, exampleUrl:str, url:str, expectedHtmlProps: UrlProps, urlProps: UrlProps, urlDict: dict[str, UrlProps]):
        '''Function to check if a url requires browser emulation (selenium) to load the full html by running js on the page'''
        if len(expectedHtmlProps.anchorTagHrefs) > 0 and (len(urlProps.anchorTagHrefs) / len(expectedHtmlProps.anchorTagHrefs)) < 0.5:
            urlDict[exampleUrl].canUseRawHTMLRequests = CanUseRawHTMLRequests.No
        else:
            urlDict[exampleUrl].canUseRawHTMLRequests = CanUseRawHTMLRequests.Yes
    
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
            (url_is_results_page, num_results) = is_results_page(driver, xpath_selector=self.link_xpath_selector)
            if url_is_results_page:
                N = num_results
                urlsToSearch = self.list_page_urls(NPages=N, append_if_not_results_page=True)
            else:
                N = 1
            
                
            for url in urlsToSearch:
                url = url.removesuffix('/')
                _useSeleniumForThisUrl = self.useSelenium
                exampleUrl = urlTree.getExampleGeneralisationOf(
                    url, removeRegexNodes=True)
                urlTree.embedUrl(url) # TODO: Fix this function as taking way too long!
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
                    self._urlNeedsJs(exampleUrl=exampleUrl, url=url, expectedHtmlProps=expectedHtmlProps, urlProps=urlProps, urlDict=urlDict)
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
        

