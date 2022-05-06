from __future__ import annotations

import abc
import atexit
import io
import logging
import os
import re
import warnings
from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime
from enum import Enum, IntEnum
from os import path
from pprint import pprint
from typing import Iterable, Literal, TypeVar

import debugpy as debug
import matplotlib.pyplot as plt
import numpy as np
import requests
from bs4 import BeautifulSoup, NavigableString, ResultSet, SoupStrainer, Tag
from file_appender import (DummyFileAppender, FileAppender, IFileAppender,
                           JsonFileAppender, TxtFileAppender)
# from progress.spinner import Spinner
# from progress.counter import Counter
from progress.bar import Bar
from py_utils import exception_to_string, nullPipe
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Safari
from selenium.webdriver.common.by import By

# from url_parser import ParsedUrlParser



class SlowBar(Bar):
    suffix = '%(remaining_hours)d hours remaining'
    @property
    def remaining_hours(self):
        return self.eta // 3600
    
class MaxNBar(Bar):
    suffix = '%(iterations_covered)d iterations covered'
    
    @property
    def iterations_covered(self):
        return self.index

class CanUseRawHTMLRequests(Enum):
    No = -1
    Unknown = 0
    Yes = 1


class UrlProps():
    def __init__(self, anchorTagHrefs:list[str]=[], embeddedScriptAndAnchorTagHrefs:list[str]=[], cookiesAgreed: bool = False) -> None:
        self.canUseBs4:CanUseRawHTMLRequests = CanUseRawHTMLRequests.Unknown
        self.anchorTagHrefs = anchorTagHrefs
        self.embeddedScriptAndAnchorTagHrefs = embeddedScriptAndAnchorTagHrefs
        self.cookiesAgreed = cookiesAgreed

    def getNumAnchorTags(self):
        return len(self.anchorTagHrefs)
    def getNumHrefsInScriptsAndButtons(self):
        return len(self.embeddedScriptAndAnchorTagHrefs)
    numAnchorTags = property(getNumAnchorTags)
    numHrefsInScriptsAndButtons = property(getNumHrefsInScriptsAndButtons)
    
def nth_of_type(elem:Tag):
    count, curr = 0, 0
    for i, e in enumerate(elem.find_parent().find_all(recursive=False), 1):
        if e.name == elem.name:
            count += 1
        if e == elem:
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

def getCssPath(elem, maxTreeSize = 100):
    if elem.attrs.get('id'):
        return '#' + elem.attrs['id']

    rv = [_getElemSelector(elem)]
    _i = 0
    while _i < maxTreeSize:
        _i += 1
        elem = elem.find_parent()
        if not elem or elem.name == '[document]':
            return '>'.join(rv[::-1])
        elif _i >= maxTreeSize:
            return ' ... ' + ' > '.join(rv[::-1])
        elif elem.attrs.get('id'):
            return '#' + elem.attrs['id'] + ' > '.join(rv[::-1])
            
        rv.append(_getElemSelector(elem))
def seleniumTryClickWebEl(wElem):
    clickSuccess = False
    try:
        wElem.click()
        clickSuccess = True
    except Exception as e:
        clickSuccess = False

    return clickSuccess

def selenium_click_css(cssSelector:str, driver:Safari):
    success = False
    webEl = driver.find_element(by=By.CSS_SELECTOR,value=cssSelector)
    if webEl:
        if webEl.is_displayed():
            if not seleniumTryClickWebEl(webEl):
                driver.execute_script(f'document.querySelector(\'{cssSelector}\').click()')
                success = True
    return success

def selenium_click_webEl(webEl, driver):
    success = False
    if webEl.is_displayed():
        if not seleniumTryClickWebEl(webEl):
            if webEl.has_attribute('id'):
                _id = webEl.get_attribute('id')
                driver.execute_script(f'document.getElementById(\'{_id}\').click()')
            else:
                cssSelector = getCssPath(webEl)
                selenium_click_css(cssSelector)
            success = True

    return success




# https://pythex.org/?regex=%5E(%3F%3A(%3FP%3Cprotocol%3Ehttp%5Bs%5D%3F%7Cftp)%3A%5C%2F)%3F%5C%2F%3F(%3FP%3Cdomain%3E%5B%5E%3A%5C%2F%5Cs%5D%2B)(%3F%3A(%3FP%3Cpath%3E(%3F%3A(%3F%3A%5C%2F%5Cw%2B)*)(%3F%3A%5C%2F%5B%5Cw%5C-%5C.%5D%2B%5B%5E%23%3F%5Cs%5D%2B))(%3FP%3Cquery%3E.*)(%3FP%3Cid%3E%23%5B%5Cw%5C-%5D%2B)%3F)%3F%24&test_string=https%3A%2F%2Fassets.adobedtm.com&ignorecase=0&multiline=0&dotall=0&verbose=0
URL_RE_PATTERN = r'^(?:(?P<protocol>http[s]?|ftp):\/)?\/?(?P<domain>[^:\/\s]+)(?:(?P<path>(?:(?:\/\w+)*)(?:\/[\w\-\.]+[^#?\s]+))(?P<query>.*)(?P<id>#[\w\-]+)?)?$'


class UrlDiscoEngine():

    # driver.find_element(By.XPATH, '//button[text()="Some text"]')
    # ID = "id"
    # XPATH = "xpath"
    # LINK_TEXT = "link text"
    # PARTIAL_LINK_TEXT = "partial link text"
    # NAME = "name"
    # TAG_NAME = "tag name"
    # CLASS_NAME = "class name"
    # CSS_SELECTOR = "css selector"

    
    maxSpiderExplodeAllowed:Literal[3] = 3
    defaultSpiderExplodeDepth:Literal[3] = 3
    
    def __init__(self, useSelenium:bool, maxSubUrls:int=-1) -> None:
        self.driver:Safari|None = None
        self.useSelenium = useSelenium
        self.maxSubUrls = maxSubUrls
        self._BASE_WINDOW_HANDLE_LAZY = ''
        self._domainsHit = defaultdict(int)
        if self.useSelenium:
            self.driver = Safari()
            self.driver.implicitly_wait(10)
            self._BASE_WINDOW_HANDLE_LAZY = self.driver.current_window_handle
            self._closeExtraSeleniumWebWindows()
        

    def _closeExtraSeleniumWebWindows(self):
        if len(self.driver.window_handles) > 1 and self._BASE_WINDOW_HANDLE_LAZY in self.driver.window_handles:
            for i,w in enumerate(self.driver.window_handles):
                if w != self._BASE_WINDOW_HANDLE_LAZY:
                    self.driver.switch_to.window(w)
                    self.driver.close()
            self.driver.switch_to.window(self._BASE_WINDOW_HANDLE_LAZY)
        assert self._BASE_WINDOW_HANDLE_LAZY in self.driver.window_handles, 'BASE_WINDOW_HANDLE_LAZY not in driver.window_handles'
        assert len(self.driver.window_handles) == 1, f'{type(self.driver)} should only have 1 window open.'
        

    def _urlDiscoverySelenium(self,rootUrl:str, driver:Safari, checkCookies=False):
        try:
            driver.get(rootUrl)
        except Exception as e:
            logging.error(f'Selenium Fell over trying to get: {rootUrl} with a {type(e).__name__} exception.')
            logging.error(e)
            
        try:
            self._closeExtraSeleniumWebWindows()
        except Exception as e:
            logging.error(f'Selenium Fell over trying to close extra selenium windows in: {rootUrl} with a {type(e).__name__} exception.')
        
        cookiesAgreed = False
        if checkCookies: 
            try:            
                cookiesAgreed = self.find_and_agree_cookies()
            except Exception as e:
                logging.error(f'Selenium Fell over trying to find and agree cookies in: {rootUrl} with a {type(e).__name__} exception.')
        
        anchorTagUrls:list[str]=[]
        scriptTagUrlEmbeds:list[str]=[]
        onClickAttributeUrlEmbeds:list[str]=[]
        try:
            anchorTagUrls = [we.get_attribute('href') for we in driver.find_elements(By.TAG_NAME, 'a')]
            scriptTagUrlEmbeds = [nullPipe(re.match(URL_RE_PATTERN, str(we.text)),lambda x: x.string) for we in driver.find_elements(By.TAG_NAME, 'script')] 
            onClickAttributeUrlEmbeds = [nullPipe(re.match(URL_RE_PATTERN, we.get_attribute('onClick')), lambda x: x.string) for we in driver.find_elements(By.CSS_SELECTOR, '[onClick]') if we.get_attribute('onClick')] 
        except TimeoutException as timeoutExcp:
            if not anchorTagUrls:
                logging.warn(f'Selenium failed to grab anchor tag urls for {rootUrl}.')
                anchorTagUrls = []
            if not scriptTagUrlEmbeds:
                logging.warn(f'Selenium failed to grab script Tag Url Embeds for {rootUrl}.')
                scriptTagUrlEmbeds = []
            if not onClickAttributeUrlEmbeds:
                logging.warn(f'Selenium failed to grab onClick Attribute Url Embeds for {rootUrl}.')
                onClickAttributeUrlEmbeds = []
        except Exception as e:
            logging.error(exception_to_string(e))
        # Button urls should be included in the onClick handler above.
        # buttonTagUrls = [we for we in driver.find_elements(By.TAG_NAME, 'button')]

        # urlPioneer = anchorTagUrls + scriptTagUrlEmbeds + onClickAttributeUrlEmbeds
        # return urlPioneer
        urlProps = UrlProps(anchorTagUrls, scriptTagUrlEmbeds + onClickAttributeUrlEmbeds, cookiesAgreed=cookiesAgreed)
        return urlProps

    def _urlDiscoveryHTMLOnly(self,rootUrl:str):
        
        # http://www.xhaus.com/headers -> View your headers in browser
        headers = {"User-agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36 Edg/96.0.1054.43'}
        if rootUrl.startswith('file:///'):
            with open(re.sub(r'^file:\/\/\/', '/', rootUrl), 'r') as f:
                pageContents = f.read()
        else:
            pageContents = requests.get(rootUrl, headers=headers).content
        # print(page.content)
        soup = BeautifulSoup(pageContents, 'html.parser')
        
        anchorTagUrls = [we.get('href') for we in soup.find_all('a')]
        scriptTagUrlEmbeds = [nullPipe(re.match(URL_RE_PATTERN, str(nullPipe(we.string, lambda y: y, returnIfnull=None))),lambda x: x.string) for we in soup.find_all('script')] 
        onClickAttributeUrlEmbeds = [nullPipe(re.match(URL_RE_PATTERN, we.get('onClick')), lambda x: x.string) for we in soup.find_all(onClick=True) if we.get('onClick')] 
        # Button urls should be included in the onClick handler above.
        # buttonTagUrls = [we for we in driver.find_elements(By.TAG_NAME, 'button')]

        # urlPioneer = anchorTagUrls + scriptTagUrlEmbeds + onClickAttributeUrlEmbeds
        urlProps = UrlProps(anchorTagUrls, scriptTagUrlEmbeds + onClickAttributeUrlEmbeds)
        return urlProps

    def urlDiscovery(self,rootUrl:str, driver:Safari=None, useSelenium:bool=False,requiredSubDomain:str=None):
        maxDomainHitsCookieCheck = 5
        driverType = 'selenium' if useSelenium else 'bs4'
        logging.info(f'urlDiscovery[{driverType}]: {rootUrl}')
        
        if useSelenium and driver is not None:
            if any(rootUrl.startswith(u) for u in self._domainsHit.keys() if bool(u)):
                urlDomain = next(rootUrl.startswith(u) for u in self._domainsHit.keys() if bool(u))
                self._domainsHit[urlDomain] += 1
            else:
                try:
                    urlDomain = re.match(ParsedUrlParser.URL_DOMAIN_MATCH, rootUrl)
                    if urlDomain:
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
            
            result = self._urlDiscoverySelenium(rootUrl=rootUrl, driver=driver, checkCookies=_checkCookies)
        
            if result.cookiesAgreed and urlDomain:
                # Stop checking for cookies:
                self._domainsHit[urlDomain] = maxDomainHitsCookieCheck
                
        else:
            result = self._urlDiscoveryHTMLOnly(rootUrl)
        
        def _removeEmptyUrls(result:list[str]):
            return [url for url in result if url is not None and (requiredSubDomain in url or requiredSubDomain is None)]
        
        return UrlProps(
            anchorTagHrefs=_removeEmptyUrls(result.anchorTagHrefs),
            embeddedScriptAndAnchorTagHrefs=_removeEmptyUrls(result.embeddedScriptAndAnchorTagHrefs)
        )

    

    def find_and_agree_cookies(self):
        cookiesAgreed = False
        assert self.driver is not None, 'Safari webdriver is None'
        _f = lambda btnText: f"//*[text()='{btnText}']"
        agreebtns = self.driver.find_elements(by=By.XPATH,value=_f('I agree'))
        btn_ids= None
        if agreebtns:
            btn_ids = [agreebtn.get_attribute('id') for agreebtn in agreebtns]
        if not btn_ids:
            agreebtns = self.driver.find_elements(by=By.XPATH,value=_f('Allow All'))
            if agreebtns:
                btn_ids = [agreebtn.get_attribute('id') for agreebtn in agreebtns]
            else:
                btn_ids = []

        if btn_ids:
            for btn_id in btn_ids:
                btn = self.driver.find_element(by=By.ID, value=btn_id)
                if btn.is_displayed():
                    if not seleniumTryClickWebEl(btn):
                        # driver.execute_script(f'$(\'#{btn_id}\').click()')
                        self.driver.execute_script(f'document.getElementById(\'{btn_id}\').click()')
            cookiesAgreed = True
        
        return cookiesAgreed


    TX = TypeVar("TX", str, int, float, None, list, dict, bool)

    @staticmethod
    def _processState(state:TX):
        '''A method to allow us to reload the state of the url discovery class from a file so that we dont need to load (pull) the url history tree'''
        if isinstance(state, list) or isinstance(state,Iterable):
            return [u for s in state for u in UrlDiscoEngine._processState(s)]
        elif isinstance(state, dict):
            return [u for k in state.keys() for u in [k, *UrlDiscoEngine._processState(state[k])]]
        elif isinstance(state, str):
            return [state]
        elif isinstance(state, int) or isinstance(state, float) or isinstance(state, bool):
            return [str(state)]
        else:
            logging.error(f'Cant add to url_discovery state for new state of type: {type(state)}')
            return []
        
    def run_url_discovery(self, domain:str, subDomainReq:str, explodeTimes:int=defaultSpiderExplodeDepth, saveOut:str|None=None):
        
        driver = self.driver
            
        if UrlDiscoEngine.maxSpiderExplodeAllowed < explodeTimes:
            warnings.warn(f'Warning: Max allowed Spider Explode to depth of: {UrlDiscoEngine.maxSpiderExplodeAllowed}')
        
        _explodeTimes = max(1,min(UrlDiscoEngine.defaultSpiderExplodeDepth,explodeTimes))
        
        urlPioneer:set[str] = set()
        fileToClose = False    
        saveFileWrap:IFileAppender
        state = {}
        if saveOut is not None and saveOut.endswith('.txt'):
            fileToClose = True
            saveFileWrap = TxtFileAppender(saveOut[:-4]).openStream()
        elif saveOut is not None:
            fileToClose = True
            saveFileWrap = JsonFileAppender(saveOut).openStream()
            if saveFileWrap.containsData():
                state = saveFileWrap.loadData()
                if hasattr(state, 'urls'):
                    urlPioneer = set(UrlDiscoEngine._processState(state['urls']))
        else:
            saveFileWrap = DummyFileAppender('Dummy').openStream()
            
        try:   
            urlsToSearch = [domain]
            newurls = set()
            
            _i = 0 # explosion depth index
            spinner = Spinner(message='Urls discovered')
            urlTree:RankPairTree = RankPairTree()
            urlDict:dict[str,UrlProps] = defaultdict(lambda : UrlProps([], []))
            
            while _i < _explodeTimes:
                _i += 1
                newurls:set[str] = set()
                for url in urlsToSearch:
                    _useSeleniumForThisUrl = self.useSelenium
                    exampleUrl = urlTree.getExampleGeneralisationOf(url, removeRegexNodes=True)
                    urlTree.embedUrl(url)
                    if urlDict[exampleUrl].canUseBs4 != CanUseRawHTMLRequests.Unknown:
                        _useSeleniumForThisUrl = bool(urlDict[exampleUrl].canUseBs4 == CanUseRawHTMLRequests.No)
                        urlProps = self.urlDiscovery(url, driver, useSelenium=_useSeleniumForThisUrl, requiredSubDomain=subDomainReq)
                    elif exampleUrl is not None:
                        _useSeleniumForThisUrl = False
                        expectedHtmlProps:UrlProps = urlDict[exampleUrl]
                        urlProps = self.urlDiscovery(url, driver, useSelenium=_useSeleniumForThisUrl, requiredSubDomain=subDomainReq)
                        if len(expectedHtmlProps.anchorTagHrefs) > 0 and (len(urlProps.anchorTagHrefs) / len(expectedHtmlProps.anchorTagHrefs)) < 0.5:
                            urlDict[exampleUrl].canUseBs4 = CanUseRawHTMLRequests.No
                            _useSeleniumForThisUrl = True
                            urlProps = self.urlDiscovery(url, driver, useSelenium=_useSeleniumForThisUrl, requiredSubDomain=subDomainReq)
                            urlDict[url] = urlProps
                            urlDict[url].canUseBs4 = CanUseRawHTMLRequests.No
                        else:
                            urlDict[url].canUseBs4 = CanUseRawHTMLRequests.Yes
                            urlDict[exampleUrl].canUseBs4 = CanUseRawHTMLRequests.Yes
                    else:
                        urlProps = self.urlDiscovery(url, driver, useSelenium=_useSeleniumForThisUrl, requiredSubDomain=subDomainReq)
                    urlDict[url] = urlProps
                        
                    newurls = newurls.union((urlProps.anchorTagHrefs + urlProps.embeddedScriptAndAnchorTagHrefs))
                    
                    if isinstance(saveFileWrap, JsonFileAppender):
                        saveFileWrap.write({'urls': {url: list(newurls)}})
                    elif isinstance(saveFileWrap, TxtFileAppender):
                        saveFileWrap.write(f'\n{url}\n-\t' + '\n-\t'.join(newurls))
                urlsToSearch = newurls - urlPioneer
                
                if self.maxSubUrls > -1:
                    urlsToSearch = urlsToSearch[:self.maxSubUrls]
                urlPioneer = urlPioneer.union(urlsToSearch)
                
                spinner.message = f'{len(urlPioneer)} urls discovered by explosion #{_i}'
                
            return urlPioneer
        except Exception as e:
            logging.error(e)
            logging.error(exception_to_string(e))
            print(e)
            if fileToClose != False:
                saveFileWrap.closeStream()
            
            return None


    # def save_url_discovery_output(name:str, urlDiscoveryOut:list[str]): 
    #     with open(f'../data/url_pioneer_{name}.txt', 'a+') as f:
    #         for l in urlDiscoveryOut:
    #             f.write(l)
def run_url_discovery_ASDA():
        return UrlDiscoEngine(True, maxSubUrls=-1)\
            .run_url_discovery('https://groceries.asda.com', 'asda.com', explodeTimes = 3, saveOut='ASDA')


    
if __name__ == '__main__':

    logging.basicConfig(filename ='app.log',
                        level = logging.INFO)

    # Example logging calls (insert into your program)
    # logging.critical('Host %s unknown', hostname)
    # logging.error("Couldn't find %r", item)
    # logging.warning('Feature is deprecated')
    # logging.info('Opening file %r, mode = %r', filename, mode)
    # logging.debug('Got here')
    
    UrlDiscoEngine(True).run_url_discovery('https://groceries.asda.com', 'asda.com', explodeTimes = 3, saveOut='ASDA')
    
    

