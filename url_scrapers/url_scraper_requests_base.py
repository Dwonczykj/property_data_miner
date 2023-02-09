
import abc
import logging
import re
from collections import defaultdict
from enum import Enum
from pprint import pformat
from typing import Iterable, TypeVar

import requests
from bs4 import BeautifulSoup
from file_appender import (DummyFileAppender, IFileAppender, JsonFileAppender,
                           TxtFileAppender)
from lxml import etree
# from progress.bar import Bar
# from progress.counter import Counter
from progress.spinner import Spinner
from py_utils import exception_to_string, nullPipe
from rank_pair_tree import RankPairTree
from selenium.webdriver import Safari
from selenium.webdriver.common.by import By
from selenium_interops import is_results_page, seleniumTryClickWebEl
from url_parser import URL_RE_PATTERN, ParsedUrlParser
from url_props import UrlProps, CanUseRawHTMLRequests
    

class _BaseScraper():
    def __init__(self) -> None:

        self._BASE_WINDOW_HANDLE_LAZY = ''
        self._domainsHit = defaultdict[str, int](int)
        self._saveFileWrap: IFileAppender | None = None
        self._fileToClose: bool = False
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
                        UrlLinkScraperRequestsBase._processState(state['urls']))
        else:
            saveFileWrap = DummyFileAppender('Dummy').openStream()
        self._saveFileWrap = saveFileWrap
        self._fileToClose = fileToClose
        return urlPioneer
    
    def registerNewDomains(self, rootUrl: str):
        '''Checks for cookie policies if this domain has not been seen before'''
        urlDomain:str|None = None
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
    
    def _request_url_to_soup(self, url: str) -> BeautifulSoup:
        urlDomain = self.registerNewDomains(rootUrl=url)

        # http://www.xhaus.com/headers -> View your headers in browser
        headers = {
            "User-agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36 Edg/96.0.1054.43'}
        if url.startswith('file:///'):
            with open(re.sub(r'^file:\/\/\/', '/', url), 'r') as f:
                pageContents = f.read()
        else:
            pageContents = requests.get(url, headers=headers).content
        # print(page.content)
        soup = BeautifulSoup(pageContents, 'html.parser')

        return soup
    
    def _soup_to_xml(self, soup:BeautifulSoup) -> etree._Element:
        dom = etree.HTML(str(soup), parser=None)
        return dom

    
    
class UrlLinkScraperRequestsBase(_BaseScraper):
    '''Class to scrape urls using an algorithm that specifies how the engine will discover more urls to scrape
        
        The class is limited to raw HTML from requests'''
    def __init__(self) -> None:
        super().__init__()
        
    TX = TypeVar("TX", str, int, float, None, list, dict, bool)

    @staticmethod
    def _processState(state:TX):
        '''A method to allow us to reload the state of the url discovery class from a file so that we dont need to load (pull) the url history tree'''
        if isinstance(state, list) or isinstance(state,Iterable):
            return [u for s in state for u in UrlLinkScraperRequestsBase._processState(s)]
        elif isinstance(state, dict):
            return [u for k in state.keys() for u in [k, *UrlLinkScraperRequestsBase._processState(state[k])]]
        elif isinstance(state, str):
            return [state]
        elif isinstance(state, int) or isinstance(state, float) or isinstance(state, bool):
            return [str(state)]
        else:
            logging.error(f'Cant add to url_discovery state for new state of type: {type(state)}')
            return []
        
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
    
    def _urlDiscoveryHTMLOnly(self, rootUrl: str) -> UrlProps:
        
        soup = self._request_url_to_soup(url=rootUrl)
        
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
