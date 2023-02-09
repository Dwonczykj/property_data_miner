# Write a webscraper in python to scrape all products and their prices from all embedded links from url groceries.asda.com

import json
import re
from url_scraper import UrlScraper, _UrlScraperRequests, _UrlScraperSelenium
from selenium.webdriver import Safari
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from bs4.element import PageElement, ResultSet
from typing import Any, Callable
from jsons.classes import JsonSerializable
from pprint import pprint

def is_number(x:str):
    try:
        y = float(x)
        return True
    except:
        return False


class ProductAttribute(JsonSerializable):
    # _foo: int
    css_selector: str
    attribute: str
    location: str | None


# c = ProductAttribute(, 2)
# jsons.dump(c, strip_privates=True)
# ProductAttribute.from_json()

    
output = {}






with open('groceries_scrapers/asda_groceries.json', 'r') as f:
    products_obj = json.load(f)
    products = products_obj['products']

def extract_text_default(we:WebElement) -> str:
    return we.text

def extract_price(we:WebElement) -> str:
    matches = re.findall(r'(?:£|$)\s?[0-9,]+(?:\.[0-9]+)?', we.text)
    if matches:
        return str(matches[0]).replace(' ','')
    else:
        return '£0.00'
    

def extract_package_size(we: WebElement) -> str:
    matches = re.findall(r'[0-9]+(?:\.[0-9]+)?\s?\w+', we.text)
    if matches:
        return str(matches[0])
    else:
        return we.text.replace('Net Content', '')

parsers: dict[str, Callable] = {
    'carbohydrates_per_large_serving': extract_text_default,
    'protein_per_large_serving': extract_text_default,
    'fats_per_large_serving': extract_text_default,
    'fibre_per_large_serving': extract_text_default,
    'salt_per_large_serving': extract_text_default,
    'ingredients': extract_text_default,
    'kcal_per_large_serving': extract_text_default,
    'name': extract_text_default,
    'package_size': extract_package_size,
    'price': extract_price,
    'use_by_estimate': extract_text_default,
    }

def filter_elements_default(elements:list[WebElement]):
    return [el for el in elements]

def filter_package_size_elements_default(elements:list[WebElement]):
    return [el for el in elements if 'Net Content' in el.text]

def filter_carbohydrate_elements_default(elements:list[WebElement]):
    return [el for el in elements if 'Carbohydrate' in el.text]

def filter_protein_elements_default(elements:list[WebElement]):
    return [el for el in elements if 'Protein' in el.text]

def filter_Salt_elements_default(elements:list[WebElement]):
    return [el for el in elements if 'Salt' in el.text]

def filter_fat_elements_default(elements:list[WebElement]):
    return [el for el in elements if 'Fat' in el.text]

def filter_fibre_elements_default(elements:list[WebElement]):
    return [el for el in elements if 'Fibre' in el.text]

def filter_kcal_elements_default(elements:list[WebElement]):
    return [el for el in elements if 'kcal' in el.text]

filter_callables: dict[str, Callable] = {
    'carbohydrates_per_large_serving': filter_carbohydrate_elements_default,
    'protein_per_large_serving': filter_protein_elements_default,
    'fats_per_large_serving': filter_fat_elements_default,
    'fibre_per_large_serving': filter_fibre_elements_default,
    'salt_per_large_serving': filter_Salt_elements_default,
    'ingredients': filter_elements_default,
    'kcal_per_large_serving': filter_kcal_elements_default,
    'name': filter_elements_default,
    'package_size': filter_package_size_elements_default,
    'price': filter_elements_default,
    'use_by_estimate': filter_elements_default,
    }


def extract_key_info(
    scraper: _UrlScraperRequests | _UrlScraperSelenium, 
    product_url: str, 
    product_attribute_key:str
    ):
    product_name = products[product_url]['search_name']
    product_attribute = products[product_url][product_attribute_key]
    product_attribute_selector = product_attribute['css_selector']
    product_attribute_matches = scraper.find_all(product_attribute_selector, by=By.CSS_SELECTOR)
    filtered_product_attribute_matches = \
        filter_callables[product_attribute_key](product_attribute_matches)
    if filtered_product_attribute_matches:
        if "filters" in product_attribute.keys():
            for filter_key in product_attribute["filters"].keys():
                _filtered_product_attribute_matches = [p for p in filtered_product_attribute_matches]
                if filter_key == 'inner_text':
                    _filtered_product_attribute_matches = [
                        el for el in filtered_product_attribute_matches 
                        if scraper.getElementText(el) == product_attribute["filters"][filter_key]
                        ]
                else:
                    raise Warning(
                        f"Filter named \"{filter_key}\" is not a recognised filter")
                filtered_product_attribute_matches = _filtered_product_attribute_matches
    
    if 'location' in product_attribute.keys() and is_number(product_attribute['location']):
        move_children = int(product_attribute['location'])
        filtered_product_attribute_matches = [
            scraper.move_siblings(m, move_count=move_children)
            for m in filtered_product_attribute_matches
        ]
    if filtered_product_attribute_matches:
        if len(filtered_product_attribute_matches) > 1:
            pprint([m.text for m in filtered_product_attribute_matches])
        if product_attribute['attribute'] == 'inner_text':
            product_attribute_value_matches = [
                parsers[product_attribute_key](m)
                # scraper.getElementText(m)
                for m in filtered_product_attribute_matches
            ]
        else:
            raise KeyError(
                f"Attribute named \"{product_attribute['attribute']}\" is not a recognised attribute")
        print(
            f'\"{product_attribute_key}" of \"{product_name}\" is \"{product_attribute_value_matches}\"')
        return product_attribute_value_matches
    else:
        return []
    
for product_url in products.keys():
    
    scraper = UrlScraper().scrapeUrl(product_url)
    
    def search_and_click_first(search_text: str, search_selector: str | None = None, li_selector:str|None=None):
        results_li_elements: list[WebElement] = scraper.search_and_list_results(
            search_text=search_text, 
            search_selector=search_selector, 
            li_selector=li_selector
            )
        if results_li_elements:
            results_li_elements[0].click()
    
    search_and_click_first('Tuna', 'input#search', 'li.co-item.co-item--rest-in-shelf')
    
    product_name = products[product_url]['search_name']
    
    # price_selector = products[product_url]['price']['css_selector']
    # prices = scraper.find_all(price_selector, by=By.CSS_SELECTOR)
    # if prices:
    #     price = scraper.getElementText(prices[0])
    #     print(f'price of {product_name} is {price}')
    
    prices = extract_key_info(
        scraper=scraper, 
        product_url=product_url, 
        product_attribute_key='price'
        )
    
    package_sizes = extract_key_info(
        scraper=scraper, 
        product_url=product_url, 
        product_attribute_key='package_size'
        )
    
    use_by_estimates = extract_key_info(
        scraper=scraper, 
        product_url=product_url, 
        product_attribute_key='use_by_estimate'
        )
    
    carbohydrates = extract_key_info(
        scraper=scraper, 
        product_url=product_url, 
        product_attribute_key='carbohydrates_per_large_serving'
        )
    proteins = extract_key_info(
        scraper=scraper, 
        product_url=product_url, 
        product_attribute_key='protein_per_large_serving'
        )
    fats = extract_key_info(
        scraper=scraper, 
        product_url=product_url, 
        product_attribute_key='fats_per_large_serving'
        )
    fibres = extract_key_info(
        scraper=scraper, 
        product_url=product_url, 
        product_attribute_key='fibre_per_large_serving'
        )
    salts = extract_key_info(
        scraper=scraper, 
        product_url=product_url, 
        product_attribute_key='salt_per_large_serving'
        )
    kcals = extract_key_info(
        scraper=scraper, 
        product_url=product_url, 
        product_attribute_key='kcal_per_large_serving'
        )
    
    output[product_url] = {
        'carbohydrates_per_large_serving': carbohydrates,
        'protein_per_large_serving': proteins,
        'fats_per_large_serving': fats,
        'fibre_per_large_serving': fibres,
        'salt_per_large_serving': salts,
        # 'ingredients': filter_elements_default,
        'kcal_per_large_serving': kcals,
        # 'name': filter_elements_default,
        'package_size': package_sizes,
        'price': prices,
        'use_by_estimate': use_by_estimates,
    }
    pprint(output[product_url])
    
    # package_size_obj = products[product_url]['package_size']
    # package_size_selector = package_size_obj['css_selector']
    # package_sizes = scraper.find_all(package_size_selector, by=By.CSS_SELECTOR)
    # if package_sizes:
    #     if "filters" in package_size_obj.keys():
    #         filtered_pkg_sizes = []
    #         for filter_key in package_size_obj["filters"].keys():
    #             if filter_key == 'inner_text':
    #                 filtered_pkg_sizes = [tag for tag in package_sizes if getattr(tag, 'inner_text') == package_size_obj["filters"][filter_key]]
    #                 if filtered_pkg_sizes:
    #                     if is_number(package_size_obj['location']):
    #                         move_children = int(package_size_obj['location'])
    #                         getattr(
    #                             filtered_pkg_sizes[0].find_next_sibling(), 'inner_text')
    #                     elif package_size_obj['location'] == 'inner_text': 
    #                         pkg_size = getattr(
    #                             filtered_pkg_sizes[0], 'inner_text')
    #                         print(f'pkg_size of {product_name} is {pkg_size}')
    #             else:
    #                 raise Warning(f"Filter named \"{filter_key}\" is not a recognised filter")
    #     else:
    #         if is_number(package_size_obj['location']):
    #             move_children = int(package_size_obj['location'])
    #             getattr(
    #                 package_sizes[0].find_next_sibling(), 'inner_text')
    #         elif package_size_obj['location'] == 'inner_text': 
    #             pkg_size = getattr(
    #                 package_sizes[0], 'inner_text')
    #             print(f'pkg_size of {product_name} is {pkg_size}')
    

    # find all the links
    # links = soup.find_all('a')

    # # loop through all the links
    # for link in links:
        
    #     # get the link
    #     link_url = link.get('href')
        
    #     # check if the link contains 'groceries.asda.com'
    #     if 'groceries.asda.com' in link_url:
            
    #         # get the product name
    #         product_name = link.find('h3').text
            
    #         # url to get the price
    #         price_url = link_url + '#details'
            
    #         # create a requests object
    #         r1 = requests.get(price_url)
            
    #         # get the html content
    #         data1 = r1.text
            
    #         # create a beautiful soup object
    #         soup1 = BeautifulSoup(data1, 'html.parser')
            
    #         # get the price
    #         price = soup1.find('div', class_='price-per-sellable-unit').text
            
    #         # print the product name and price
    #         print(product_name, '-', price)
    
    scraper.close()
