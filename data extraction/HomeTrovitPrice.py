# -*- coding: utf-8 -*-
"""
Created on Sun Sept 29 2019
Author: WQD190011

Home Trovit
Cheras
min 100k
floor size > 500 sq

"""
from urllib.parse import urlencode, quote
import bs4
from bs4 import BeautifulSoup
from lxml import etree
import requests
import math
import pandas as pd
import logging
import utils

## define or initialise all the attributes
title1       = []
address1     = []
detail1      = []
url1         = []
image1       = []
source_info1 = []
source_date1 = []
price1       = []
nofbedroom1  = []
nofbathroom1 = []
floorsize1   = []
typeProperty1 = []

num         = 0
num1        = 1
page        = 1
total_page  = 0
total_item  = 0
no_propertylist = 1

# Set up logging
log_name = 'app'
logging.getLogger(log_name).addHandler(logging.StreamHandler())
logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()
logPath = './logs'
fileName = f'{log_name}'
fileHandler = logging.FileHandler("{0}/{1}.log".format(logPath, fileName))
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)
rootLogger.setLevel(logging.INFO)

app_logger = rootLogger

search_term = 'Liverpool'
search_term_url = quote(search_term)
propertyType = ["Apartment","Bungalow","Condo","House","Plex"]
max_no_pages = 100
# search_url = 'https://homes.trovit.my/index.php/cod.search_homes/type.1/what_d.kuala%20lumpur/origin.2/price_min.100000/rooms_min.1/bathrooms_min.1/property_type.'+propertyType[no_propertylist-1]+'/area_min.500/order_by.source_date/resultsPerPage.25/isUserSearch.1'
search_url = f'https://homes.trovit.co.uk/index.php/cod.search_homes/what_d.{search_term}/isUserSearch.1'
#start loop
#loop per propertyhouse
try:
    while no_propertylist <= len(propertyType):
        property_srch_url = f'{search_url}/origin.2/order_by.source_date/property_type.{propertyType[no_propertylist-1]}/'
        app_logger.info(f'GET - {property_srch_url}')
        r    = requests.get(property_srch_url)
        soup = bs4.BeautifulSoup(r.text,'html.parser')
        
        ##retrieve and set the total page number        
        total_item = soup.find('div', {'class':'results-counter js-results-counter'}).find('span').text #type:ignore
        total_item = int(total_item.replace(',',''))
        total_page = math.ceil(total_item/25)
        
        if total_page > 100:
            total_page = 100
        
        #start loop
        #loop per page number
        while page <= total_page:
            property_srch_url_page = f'{property_srch_url}/page.{page}'
            app_logger.info(f'GET - {property_srch_url_page}')
            r = requests.get(property_srch_url_page)
            soup = bs4.BeautifulSoup(r.text,'xml')
            soup_html = bs4.BeautifulSoup(r.text, 'html.parser')
            dom = etree.HTML(str(soup_html),parser=None)

            # if total_page > 1:
            #     num_items_on_page = len(dom.xpath('//div[@class="item-title"]'))
            #     nofitem = min(25, num_items_on_page)
            # else:
            #     nofitem = total_item
            nofitem = len(dom.xpath('//div[@class="item-title"]'))
            
                
            def attr_from_xpath(xpath:str, num:int, attr_name:str='text'):
                try:
                    item_xpath = xpath
                    item = utils.xpath_attr_if_exists(dom, item_xpath, num, attr_name, defaultRes='')
                    assert isinstance(item, str)
                    item = item.replace(',','')
                except IndexError:
                    item = "#NA"
                return item
            
            def attr_from_item_xpath(item_name:str, num:int):
                return attr_from_xpath(xpath=f'//div[contains(@class,"item-{item_name}")]/span', num=num)
            
            #second loop
            #loop per item number     
            while num < nofitem:
                
                ## retrieving of the data
                
                                
                app_logger.info(f'Retrieving titles for search page: {property_srch_url_page}')
                # Title
                title = attr_from_item_xpath('title', num)
                title1.append(title)
                
                # Address or Zone
                address = attr_from_item_xpath('address', num)
                address1.append(address)
                
                # Property Details
                app_logger.info(f'Retrieving property details for search page: {property_srch_url_page}')
                details_xpath_selector =  '//div[contains(@class,"item-description")]/p'
                selection = dom.xpath('//div[contains(@class,"item-description")]/p/*')
                if not selection or len(selection) < num:
                    detail = ''
                else:
                    detail = etree.tostring(selection[num-1], encoding='unicode') #type:ignore
                
                detail1.append(detail)
                
                # URL
                app_logger.info(f'Retrieving urls for search page: {property_srch_url_page}')
                url_xpath_selector =  '//div[contains(@class," js-item-wrapper")]//div[@class="snippet-content"]//a'
                url = attr_from_xpath(url_xpath_selector, num, 'href')
                url1.append(url)
                
                # Image
                img_selector = '//div[contains(@class," js-item-wrapper")]//div[@class="snippet-gallery"]//img'
                img = attr_from_xpath(img_selector, num, 'src')
                image1.append(img)
                
                # Source Info
                app_logger.info(f'Retrieving agent source informations for search page: {property_srch_url_page}')
                source_xpath_selector =  '//div[contains(@class,"item-extra-info")]//span[@class="item-source"]'
                agent_source_of_listing = attr_from_xpath(source_xpath_selector, num)
                source_info1.append(agent_source_of_listing)
                
                # Source Date or Published Date
                try:
                    
                    published_date_xpath_selector =  '//div[contains(@class,"item-extra-info")]//span[@class="item-published-time"]'
                    source_date = utils.xpath_attr_if_exists(dom, published_date_xpath_selector, num, 'text', defaultRes='')
                    assert isinstance(source_date, str)
                    source_date = source_date.replace(',','')
                    # source_date = source_date.replace('+','')
                    # source_date = source_date.replace('days ago','')  
                    # source_date = source_date.replace(' ','')
                except IndexError:
                    source_date = "#NA"
                source_date1.append(source_date)
                
                # Price
                app_logger.info(f'Retrieving prices for search page: {property_srch_url_page}')
                price = attr_from_item_xpath('price', num)
                price1.append(price)
                
                # Bed & Bathrooms Spans
                dom_item_properties = utils.xpath_element_if_exists(dom, '//div[contains(@class,"item-properties")]', num)
                nofbathroom = '#NA'
                if dom_item_properties is not None:
                    # No of Bedroom Available
                    app_logger.info(f'Retrieving nos_of_beds for search page: {property_srch_url_page}')
                    try:
                        nofbedroom = utils.xpath_attr_if_exists(dom_item_properties, '//div[contains(@class,"item-rooms")]/span', 0, 'text', None)
                        assert isinstance(nofbedroom, str)
                        nofbedroom = nofbedroom.replace(',','')
                        if '\xa0BE' not in nofbedroom:
                            pass
                        nofbedroom = nofbedroom.replace('\xa0BE', '')
                        nofbedroom = nofbedroom.replace(' br','')
                    except IndexError:
                        item = "#NA"
                    
                    
                    
                    # No of Bathroom Available
                    # if(num1 == 1):
                    #     num1 = 1
                    # else:
                    #     num1 = num1 + 2
                
                
                    try:
                        nofbathroom = utils.xpath_attr_if_exists(dom_item_properties, '//div[contains(@class,"item-baths")]/span', 0, 'text', None)
                        assert isinstance(nofbathroom, str)
                        nofbathroom = nofbathroom.replace(',','')
                        if '\xa0BA' not in nofbathroom:
                            pass
                        nofbathroom = nofbathroom.replace('\xa0BA', '')
                        nofbathroom = nofbathroom.replace(' br','')
                    except IndexError:
                        item = "#NA"
                
                nofbedroom1.append(nofbedroom)
                nofbathroom1.append(nofbathroom)
                
                # Floor Size or Property Size
                # TODO: For this - require smart-scraping key information extraction tech
                # app_logger.info(f'Retrieving sq_footages for search page: {property_srch_url_page}')
                # try:
                #     floorsize   = soup.find_all(itemprop="floorSize")[num].get("content")
                #     floorsize = floorsize.replace(',','')
                # except IndexError:
                #     floorsize   = "#NA"
                # floorsize1.append(floorsize)    
                
                typeProperty = propertyType[no_propertylist-1]
                typeProperty1.append(typeProperty)  
                
                num += 1
                num1 += 1
                
                app_logger.info({
                    'title': title1,
                    'location': address1,
                    'property_details': detail1,
                    'url': url1,
                    'image': image1,
                    'source_info': source_info1,
                    'published_days': source_date1,
                    'price': price1,
                    'no_of_bedroom': nofbedroom1,
                    'no_of_bathroom': nofbathroom1,
                    'property_size': floorsize1,
                    'property_type': typeProperty1
                })
                
            num   = 0
            num1  = 1
            page += 1
        num   = 0
        num1  = 1
        page  = 1        
        no_propertylist += 1
        
except Exception as e:
    app_logger.exception(e)

# Saving all the data into Cheras_HomeTrovit_raw.xls file
        
cols = ['title', 
        'location', 
        'property_details',
        'url', 
        'image', 
        'source_info', 
        'published_days', 
        'price',
        'no_of_bedroom', 
        'no_of_bathroom', 
        # 'property_size', 
        'property_type'
        ]

dataframe = pd.DataFrame({
    'title': title1,
    'location': address1,
    'property_details': detail1,
    'url': url1,
    'image': image1,
    'source_info': source_info1,
    'published_days': source_date1,
    'price': price1,
    'no_of_bedroom': nofbedroom1,
    'no_of_bathroom': nofbathroom1,
    # 'property_size': floorsize1,
    'property_type': typeProperty1
    })[cols]

dataframe.to_csv(f'HomeTrovit_raw_{search_term}.csv', index=False)
        