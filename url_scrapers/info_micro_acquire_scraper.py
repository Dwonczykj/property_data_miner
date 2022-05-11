

from bs4 import BeautifulSoup

from url_scraper_base import InfoScraperRequestsBase


class InfoMicroAcquireRequestsScraper(InfoScraperRequestsBase):
    '''Class to scrape Startup key information
        
        The class is limited to raw HTML from requests'''
    def __init__(self) -> None:
        super().__init__()
        
    def get_urls_to_scrape(self) -> list[str]:
        domain = 'https://app.microacquire.com/marketplace'
        soup = self._request_url_to_soup(domain)
        dom = self._soup_to_xml(soup)
        
        
        xpath = "//a[contains(@class,'custom-link')]"
        
        anchors = dom.xpath(xpath)
        
        return [
            selected.get('href')
            for selected in anchors
            if selected.get('href')
        ]
        
    def extract_content(self, soup: BeautifulSoup) -> dict[str, str]:
        dom = self._soup_to_xml(soup)
        asking_price = dom.xpath("//span[@class='asking-price-title']").get('text', 'N/A')
        revenue_multiple_metric = dom.xpath("//span[@class='status__label']").get('text', 'N/A')
        number_of_customers = dom.xpath(
            "//div[contains(@class,'project-info-item')]/span[contains(text(),'Number of customers')]/./../div/span").get('text', 'N/A')
        
        
        return {
            'asking_price': asking_price,
            'revenue_multiple_metric': revenue_multiple_metric,
            'number_of_customers': number_of_customers,
        }
        
            