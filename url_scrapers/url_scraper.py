import logging
from url_scraper_selenium_base import UrlLinkScraperSeleniumBase
from selenium.webdriver import Safari
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from bs4.element import PageElement, ResultSet
		
def el_get_children(el:WebElement):
    try:
        return el.find_elements_by_xpath('../descendant::*')
    except:
        return None

class UrlScraper(UrlLinkScraperSeleniumBase):
    def __init__(self, forceUseSelenium:bool=False) -> None:
        super().__init__()
        self.maxDomainHitsCookieCheck = 5
        self.urlNeedsEmulation = forceUseSelenium
        self.url = ''
        
    @property
    def link_xpath_selector(self):
        # return '//div[@class="item-title"]'
        return '//a'
        
    def scrapeUrl(self, url:str):
        self.url = url
        self.urlNeedsEmulation = self.urlNeedsJs(url=url)
        if self.urlNeedsEmulation:
            self.driver = self.scrapeUrlWithSelenium(url=url)
            return _UrlScraperSelenium(urlScraper=self)
        else:
            self.soup, self.dom = self.scrapeUrlWithRequests(url=url)
            return _UrlScraperRequests(urlScraper=self)
        
    def close(self):
        if self.driver:
            self.driver.close()
        
    
class _UrlScraperSelenium():
    def __init__(self, urlScraper:UrlScraper) -> None:
        self.baseScraper = urlScraper
        self.baseScraper.driver.implicitly_wait(10)
        
    def close(self):
        if self.baseScraper:
            self.baseScraper.close()
            
    @property
    def driver(self):
        return self.baseScraper.driver
        
    def getRootHtml(self, url:str):
        driver: Safari = self.baseScraper.scrapeUrlWithSelenium(url=url)
        we: WebElement = driver.find_element(by=By.XPATH, value="/")
        return self.getElementHtml(we)
    
    def getElementHtml(self, element: WebElement):
        return element.get_attribute('innerHTML')
    
    def getElementText(self, element: WebElement):
        return element.text
    
    def getRootText(self, url:str):
        driver: Safari = self.baseScraper.scrapeUrlWithSelenium(url=url)
        we: WebElement = driver.find_element(by=By.XPATH, value="/")
        return we.text
        
    def find_all(self, selector:str, by:str=By.CSS_SELECTOR):
        results: list[WebElement] = self.baseScraper.driver.find_elements(
            by=by, value=selector)
        return results
        
    def move_siblings(self, element:WebElement, move_count:int):
        sib: WebElement | None = element
        if move_count < 0:
            _m = max(-100, move_count)
            for i in range(_m, 0, 1):
                if sib is None:
                    return None
                sib = sib.find_element_by_xpath("preceding-sibling::*")
        elif move_count > 0:
            _m = min(100, move_count)
            for i in range(_m, 0, -1):
                if sib is None:
                    return None
                sib = sib.find_element_by_xpath("following-sibling::*")
        return sib
    
    def search_and_list_results(self, search_text: str, search_selector: str | None = None, li_selector: str | None = None) -> list[WebElement]:
        'i.e. input#search'
        curUrl = self.baseScraper.driver.current_url
        potential_search_inputs = []
        if search_selector is not None:
            potential_search_inputs = self.driver.find_elements_by_css_selector(search_selector)
        if not potential_search_inputs:
            all_inputs = self.baseScraper.driver.find_elements_by_css_selector('input')
            potential_search_inputs:list[WebElement] = [p for p in all_inputs if p.get_attribute('id') and 'search' in p.get_attribute('id').lower()]
            
        for p in potential_search_inputs:
            p.send_keys(search_text)
            p.submit()
            if curUrl != self.baseScraper.driver.current_url:
                break
        all_ul_tags = []
        if li_selector is not None:
            all_ul_tags = self.driver.find_elements_by_css_selector(
                li_selector)
        if not all_ul_tags:
            all_ul_tags = self.baseScraper.driver.find_elements_by_css_selector('ul')
        potential_ul_results: list[WebElement] = [
            li for li in all_ul_tags 
            if search_text.lower() in li.get_attribute('innerHTML').lower()
        ]
        if not potential_ul_results:
            potential_ul_results = all_ul_tags
        lis = [li for ul in potential_ul_results for li in ul.find_elements_by_css_selector('li') if el_get_children(ul) and li and li.is_displayed()]
        # def get_title_if_exists(tag:WebElement):
        #     potential_titles = tag.find_elements_by_xpath(
        #         "//*[contains(concat(' ', normalize-space(@class), ' '), ' " + 'title' + " ')]")
        #     if not potential_titles:
        #         return tag.text
        #     else:
        #         return potential_titles[0].text
        return lis
            

class _UrlScraperRequests():
    def __init__(self, urlScraper:UrlScraper) -> None:
        self.baseScraper = urlScraper
        
    def close(self):
        if self.baseScraper:
            self.baseScraper.close()
        
    def getRootHtml(self, url:str):
        soup, dom = self.baseScraper.scrapeUrlWithRequests(url=url)
        return str(soup)
    
    def getRootText(self, url:str):
        soup, dom = self.baseScraper.scrapeUrlWithRequests(url=url)
        return soup.get_text()
    
    def getElementHtml(self, element: PageElement):
        return str(element)
    
    def getElementText(self, element: PageElement):
        return element.get_text()

    def find_all(self, selector:str, by:str=By.CSS_SELECTOR):
        results: ResultSet[PageElement] = self.baseScraper.soup.find_all(selector)
        return results
    
    def move_siblings(self, element:PageElement, move_count:int):
        
        sib: PageElement | None = element
        if move_count < 0:    
            _m = max(-100,move_count)
            for i in range(_m,0,1):
                if sib is None:
                    return None
                sib = sib.previous_sibling
        elif move_count > 0:
            _m = min(100,move_count)
            for i in range(_m,0,-1):
                if sib is None:
                    return None
                sib = sib.next_sibling
        return sib
    
    def search_and_list_results(self, search_text: str, search_selector: str | None = None, li_selector: str | None = None):
        'i.e. input#search'
        self.baseScraper = UrlScraper(forceUseSelenium=True)
        newScraper = self.baseScraper.scrapeUrl(self.baseScraper.url)
        return newScraper.search_and_list_results(search_text=search_text, search_selector=search_selector, li_selector=li_selector)
        
