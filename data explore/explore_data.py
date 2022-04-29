import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import mpl_toolkits
import os
cwd = os.getcwd()

data = pd.read_csv("HomeTrovit_clean.csv")

data['no_of_bedroom'].value_counts().plot(kind='bar')
plt.title('number of bedroom')
plt.xlabel('no of bedroom')
plt.ylabel('count')


data['no_of_bathroom'].value_counts().plot(kind='bar')
plt.title('number of bathroom')
plt.xlabel('no of bathroom')
plt.ylabel('count')

plt.scatter(data.price,data.property_size)
plt.title('Price vs Square Feet')

plt.scatter(data.no_of_bedroom, data.price)
plt.title('No of Bedroom and Price')
plt.xlabel('No of Bedroom')
plt.ylabel('Price')
plt.show()

plt.scatter(data.no_of_bathroom, data.price)
plt.title('No of Bathroom and Price')
plt.xlabel('No of Bathroom')
plt.ylabel('Price')
plt.show()



plt.scatter(data.district,data.price)
plt.title("Which district is the pricey location")