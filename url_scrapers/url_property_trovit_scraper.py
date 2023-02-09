import re
from py_utils import int_to_pos_int
from url_scraper import UrlScraper

class UrlPropertyTrovitScraper(UrlScraper):
    def __init__(self) -> None:
        super().__init__()
        self.maxDomainHitsCookieCheck = 5
        self._page_number: int = 0

    @property
    def link_xpath_selector(self):
        return '//div[@class="item-title"]'

    def link_discovery_algo(self):
        pass

    def run_url_discovery(self, domain: str, subDomainReq: str, saveOut: str | None = None):
        urlPioneer = self.open_file_storage_stream(saveOut=saveOut)
        urlPioneer = set()
        self.run_url_discovery_engine(
            urlPioneer=urlPioneer, 
            domain=domain,
            subDomainReq=subDomainReq
            )      

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