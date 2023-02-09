


import logging
import re
from typing import Any, Callable, TypeVar
from lxml import etree

from py_utils import exception_to_string, nullPipe
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Safari
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from url_parser import URL_RE_PATTERN

from css_selector_utils import getCssPath


def seleniumTryClickWebEl(wElem: WebElement, cbToConfirmClicked: Callable[[WebElement], bool] | None = None):
    clickSuccess = False
    try:
        wElem.click()
        if cbToConfirmClicked:
            return cbToConfirmClicked(wElem)
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
                driver.execute_script(
                    f'document.querySelector(\'{cssSelector}\').click()')
                success = True
    return success


def selenium_click_webEl(webEl:WebElement, driver:Safari):
    success = False
    if webEl.is_displayed():
        if not seleniumTryClickWebEl(webEl):
            if webEl.get_attribute('id') is not None:
                _id = webEl.get_attribute('id')
                driver.execute_script(
                    f'document.getElementById(\'{_id}\').click()')
            else:
                cssSelector = getCssPath(webEl)
                selenium_click_css(cssSelector, driver)
            success = True

    return success


T = TypeVar("T")

def get_tag_ancestors_selenium(we:WebElement, transformer:Callable[[WebElement],T]) -> list[T]:
    w = we
    ancestors = []
    try:
        while w is not None:
            ancestors = [transformer(w)] + ancestors
            w = w.find_element(by=By.XPATH, value="./..")
    finally:
        return ancestors


def get_tag_ancestors_lxml(we: etree._Element, transformer: Callable[[etree._Element], T]) -> list[T]:
    w = we
    ancestors = []
    while w is not None:
        ancestors = [transformer(w)] + ancestors
        xPathRes:list[etree._Element] = w.xpath("./..")
        w = xPathRes[0] if xPathRes else None
        # w = w.xpath("//parent")
    return ancestors

def get_embedded_links_selenium(web_el:WebElement):
    
    current_url = 'N/A'
    anchorTagUrls: list[str] = []
    scriptTagUrlEmbeds: list[str] = []
    onClickAttributeUrlEmbeds: list[str] = []
    
    try:
        driver:Safari|None = web_el.parent
        if driver:
            current_url = driver.current_url
        anchorTagUrls = [we.get_attribute(
            'href') for we in web_el.find_elements(By.TAG_NAME, 'a')]
        scriptTagUrlEmbeds = [nullPipe(re.match(URL_RE_PATTERN, str(
            we.text)), lambda x: x.string if x is not None else '') for we in web_el.find_elements(By.TAG_NAME, 'script')]
        onClickAttributeUrlEmbeds = [nullPipe(re.match(URL_RE_PATTERN, we.get_attribute(
            'onClick')), lambda x: x.string if x is not None else '') for we in web_el.find_elements(By.CSS_SELECTOR, '[onClick]') if we.get_attribute('onClick')]
    except TimeoutException as timeoutExcp:
        if not anchorTagUrls:
            logging.warn(
                f'Selenium failed to grab anchor tag urls for {current_url}..{web_el}.')
            anchorTagUrls = []
        if not scriptTagUrlEmbeds:
            logging.warn(
                f'Selenium failed to grab script Tag Url Embeds for {current_url}..{web_el}.')
            scriptTagUrlEmbeds = []
        if not onClickAttributeUrlEmbeds:
            logging.warn(
                f'Selenium failed to grab onClick Attribute Url Embeds for {current_url}..{web_el}.')
            onClickAttributeUrlEmbeds = []
    except Exception as e:
        logging.error(exception_to_string(e))
        
    return (anchorTagUrls, scriptTagUrlEmbeds, onClickAttributeUrlEmbeds)

def is_results_page(driver:Safari, xpath_selector:str|None=None):
    '''Check for list results which contain embedded links
        - driver: Safari webdriver
        - xpath_selector: optional xpath selector str to use to identify list items
    '''
    # Train a DTC to check if page is results page or not by finding 100 different results pages, images results etxc, then 100 non landing pages
    if xpath_selector:
        key_list_item_selector = xpath_selector
        list_items = driver.find_elements(by=By.XPATH,value=key_list_item_selector)
        if list_items:
            return (True, len(list_items))
        else:
            return (False, 0)
    else:
        li_selector = "//ul/li"
        list_items = driver.find_elements(by=By.XPATH,value=li_selector)
        # TODO:  Find the  subset  of these tags that are actually for the results? Do the tags need to contain further content such as a title re?
        if list_items:
            first_item = list_items[0]
            (anchorTagUrls, scriptTagUrlEmbeds, onClickAttributeUrlEmbeds) = get_embedded_links_selenium(web_el=first_item)
            if anchorTagUrls: 
                key_list_item_selector = f"{li_selector}//a"
            elif scriptTagUrlEmbeds: 
                key_list_item_selector = f"{li_selector}//script"
            elif onClickAttributeUrlEmbeds:
                key_list_item_selector = f"{li_selector}//[@onClick]"
            else:
                key_list_item_selector = ""
            ws = driver.get_window_size()
            assert (ws is float or ws is int) and ws > 0, 'window size must be greater than 0'
            item_locations_pcnt = [(li.location / ws)*100.0 for li in list_items]
            if min(item_locations_pcnt) < 0.3 and max(item_locations_pcnt) > 0.7:
                # TODO: need to apply smarter filtering to the list of items to exclude other lists on the page
                return (True, len(item_locations_pcnt))
            else:
                return (False, 0)
        else:
            return (False, 0)
    
    
            