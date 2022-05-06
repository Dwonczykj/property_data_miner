import logging

from rank_pair_tree import RankPairTree
from trovit_property_url_scraper import TrovitPropertyUrlScraper

if __name__ == '__main__':

    logging.basicConfig(filename ='app.log',
                        level = logging.INFO)
    
    # rpt = RankPairTree(url='https://homes.trovit.co.uk/index.php/cod.search_homes/type.1/what_d.Liverpool/sug.0/isUserSearch.1/origin.2/order_by.relevance/region.Merseyside/price_max.300000/rooms_min.2/bathrooms_min.2/page.1')
    # rpt.embedUrl(url='https://homes.trovit.co.uk/index.php/cod.search_homes/type.1/what_d.Liverpool/sug.0/isUserSearch.1/origin.2/order_by.relevance/region.Merseyside/price_max.300000/rooms_min.2/bathrooms_min.2/page.2')
    # print(rpt)
    # debug=True

    # Example logging calls (insert into your program)
    # logging.critical('Host %s unknown', hostname)
    # logging.error("Couldn't find %r", item)
    # logging.warning('Feature is deprecated')
    # logging.info('Opening file %r, mode = %r', filename, mode)
    # logging.debug('Got here')
    
    # TrovitPropertyUrlScraper().run_url_discovery('https://groceries.asda.com', 'asda.com', explodeTimes = 3, saveOut='ASDA')
    # trovit_landing_page_search = 'https://homes.trovit.co.uk/index.php/cod.search_homes/type.1/what_d.Liverpool/sug.0/isUserSearch.1/origin.2/order_by.relevance/region.Merseyside/price_max.300000/rooms_min.2/bathrooms_min.2/date_from.1/'
    trovit_landing_page_search = 'https://homes.trovit.co.uk/index.php/cod.search_homes/type.1/what_d.Liverpool/sug.0/isUserSearch.1/origin.2/order_by.relevance/region.Merseyside/price_max.300000/rooms_min.2/bathrooms_min.2/'
    TrovitPropertyUrlScraper().run_url_discovery(trovit_landing_page_search, 'rd.clk.thribee', saveOut='Liverpool')
