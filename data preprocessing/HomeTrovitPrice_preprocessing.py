# -*- coding: utf-8 -*-
"""
Created on Sat Nov 2 2019
Author: WQD190011

transformation and cleaning process

"""

import pandas as pd
import numpy as np

num = 0

dataframe = pd.read_csv('D:\GitHub\WXD7005\HomeTrovit\data extraction\HomeTrovit_raw.csv')
dataframe_clean = dataframe

#Replace "MYR" in the "Price" column value
dataframe_clean['price'] = dataframe_clean['price'].str.replace('MYR', '')
#Convert “Price” to numeric values
dataframe_clean['price'] = pd.to_numeric(dataframe_clean['price'], errors='coerce')
#remove a row or a column from a dataframe which has a NaN or no values in it
dataframe_clean.dropna(subset=['price'], inplace=True)

#Convert “No of Bedroom Available” to numeric values
dataframe_clean['no_of_bedroom'] = pd.to_numeric(dataframe_clean['no_of_bedroom'], errors='coerce')
#Convert “No of bathroom” to numeric values
dataframe_clean['no_of_bathroom'] = pd.to_numeric(dataframe_clean['no_of_bathroom'], errors='coerce')
#remove a row or a column from a dataframe which has a NaN or no values in it
dataframe_clean.dropna(subset=['no_of_bedroom'], inplace=True)
dataframe_clean.dropna(subset=['no_of_bathroom'], inplace=True)

#Convert “Floor Size or Property Size sq. feet” to numeric values
dataframe_clean['property_size'] = pd.to_numeric(dataframe_clean['property_size'], errors='coerce')
#remove a row or a column from a dataframe which has a NaN or no values in it
dataframe_clean.dropna(subset=['property_size'], inplace=True)


#Reassign the Zone
a = dataframe_clean['location']
dataframe_clean['district'] = pd.np.where(a.str.contains('Ampang'), 'Ampang',
                              pd.np.where(a.str.contains('Batu Caves'), 'Batu Caves',
                              pd.np.where(a.str.contains('Cheras'), 'Cheras',
							  pd.np.where(a.str.contains('Damansara'), 'Damansara',
							  pd.np.where(a.str.contains('Gombak'), 'Gombak',
							  pd.np.where(a.str.contains('Hulu Kelang'), 'Hulu Kelang',
							  pd.np.where(a.str.contains('Kepong'), 'Kepong',
							  pd.np.where(a.str.contains('Setapak'), 'Setapak',
							  pd.np.where(a.str.contains('Sri Petaling'), 'Petaling',
							  pd.np.where(a.str.contains('Petaling Jaya'), 'Petaling Jaya',
							  pd.np.where(a.str.contains('Setapak'), 'Setapak',
							  pd.np.where(a.str.contains('Sungai Besi'), 'Sungai Besi',
							  pd.np.where(a.str.contains('Kuala Lumpur'), 'Kuala Lumpur','Others')))))))))))))

#remove a row or a column from a dataframe which has a NaN or no values in it
dataframe_clean['location'].replace('', np.nan, inplace=True)
dataframe_clean.dropna(subset=['location'], inplace=True)
 
#get the Price per sq. feet
dataframe_clean['price_per_square'] = dataframe_clean['price'] / dataframe_clean['property_size']


#drop unneccessary attributes ; 'Url', 'Image', 'Source Info'
dataframe_clean.drop(['url', 'image', 'source_info', 'published_days','location', 'title', 'property_details'], axis=1, inplace=True)

#filter for data property size < 3000 sq feet and price < 2000000
#other remove from dataframe
#other data is irrelevant and lack of data for size > 3000 sq feet and price > 2000000
#dataframe_clean = dataframe_clean[dataframe_clean['property_size'] < 3000]
dataframe_clean = dataframe_clean[dataframe_clean['price'] < 1000000]
#dataframe_clean.reset_index(inplace=True, drop=True)

#drop duplicate data
#dataframe_clean.drop_duplicates(keep=False, inplace=True)
dataframe_clean.drop_duplicates(subset=None, keep='first', inplace=False)

##Save clean data to csv file
dataframe_clean.to_csv('HomeTrovit_clean.csv', index=False)