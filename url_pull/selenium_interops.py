

from css_selector_utils import getCssPath
import selenium.common
import xml.etree.ElementTree as ET

def seleniumTryClickWebEl(wElem):
    clickSuccess = False
    try:
        wElem.click()
        clickSuccess = True
    except Exception as e:
        clickSuccess = False

    return clickSuccess


def selenium_click_css(cssSelector, driver):
    success = False
    webEl = driver.find_element_by_css_selector(cssSelector)
    if webEl:
        if webEl.is_displayed():
            if not seleniumTryClickWebEl(webEl):
                driver.execute_script(
                    f'document.querySelector(\'{cssSelector}\').click()')
                success = True
    return success


def selenium_click_webEl(webEl, driver):
    success = False
    if webEl.is_displayed():
        if not seleniumTryClickWebEl(webEl):
            if webEl.has_attribute('id'):
                _id = webEl.get_attribute('id')
                driver.execute_script(
                    f'document.getElementById(\'{_id}\').click()')
            else:
                cssSelector = getCssPath(webEl)
                selenium_click_css(cssSelector, driver)
            success = True

    return success


def get_tag_ancestors_selenium(we):
    ancestors = [we]
    w = we
    while w.parent is not None:
        w = w.parent
        ancestors = [w] + ancestors
    return ancestors    

def get_tag_ancestors_lxml(we):
    ancestors = [we]
    w = we
    while w.getparent() is not None:
        w = w.xpath("//parent")
        ancestors = [w] + ancestors
    return ancestors    
