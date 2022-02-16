#!/usr/bin/env python
# coding: utf-8

# Trader Joe's web site is designed in a way that information of a store can be find by 
#first determining the state where the store is located. Thus, [list of states in which 
#Trader Joe's located](https://locations.traderjoes.com/) is welcomed us. Then, one needs 
#to determine [the city](https://locations.traderjoes.com/ca/) within a specific state 
#where the store is located so that one can see [the list of all the stores](https://locations.traderjoes.com/ca/los-angeles/) 
#within the selected city.

# In general it can be summarized as: State(e.g. Califronia)-> City(e.g. Los Angles)-> Store(e.g. Trader Joe's Hollywood). Hence, I planned my scraping strategy accordingly: define 3 main specific functions that makes the transition between each parts possible. Luckly, their site has static content which can be easily scraped by utilizing [the Beautiful Soup module.](https://www.crummy.com/software/BeautifulSoup/bs4/doc/).

#libraries that you would need
import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import requests #makes the http request, necessary for geocoding
from bs4 import BeautifulSoup #module for static web site scraping
import json #reads and downloads json formats from the website
from geopy.geocoders import Nominatim #geocoding
from geopy.exc import GeocoderTimedOut
from geopy.extra.rate_limiter import RateLimiter
import re #string manipulation 
import time #sleep Zzzz.
import folium #mapping
import geopandas #geospatial data
import pickle #to pickle (ssaving with very low sizes)
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler


#parses all the state links in the first page where list of all the states with Trader Joe's are listed.
def parse_statelinks(states):
    
    URL_state = states.find('a')['href']
    page_state = requests.get(URL_state)

    soup_state = BeautifulSoup(page_state.content, "html.parser")
    results_state = soup_state.find(id="contentbegin")
    cities = results_state.find_all("div", class_="itemlist")
    
    return cities

#Makes the transition from the selected state, and parses (returns) the cities with Trader Joe's within
def states2cities(soup):
    cities = []
    results = soup.find(id="contentbegin")
    states = results.find_all("div", class_="itemlist")
    cities.extend([parse_statelinks(states[i]) for i in range(len(states))])
    
    return cities
    

#Makes the transition from the selected city, and parses the stores (Trader Joe's) within,
#returns list of dictionaries (json format) that contains address information about each store.

def city2stores(city):
    store_list = []
    
    URL_city = city.find('a')['href']
    page_city = requests.get(URL_city)
    soup_city = BeautifulSoup(page_city.text, "html.parser")
    
    results_city = soup_city.find(id="contentbegin")
    city_results = results_city.find_all("script", {"type":"application/ld+json"})
    
    for i in range(len(city_results)):
        store_list.append(json.loads("".join(results_city.find_all("script", {"type":"application/ld+json"})[i])))
    
    
    return store_list


#Geocode the given store addresses from address string to shapely point object.

def city_geocode(store):
    
    PostalAddress = store['address']
    
    #create the full adress of the store whom you want to geocode, fix the abbrivation (e.g. change Rd. to Road)
    street_address = street_address_fix(PostalAddress['streetAddress'])
    address = street_address.split(',')[0] + ', ' + PostalAddress['addressLocality'] + ', ' + PostalAddress['addressRegion'] + ', '+ PostalAddress['addressCountry']

    #geocode using OSM Nominatim
    rnd = np.random.randint(1, 20)
    time.sleep(rnd)
    
    #first try to geocode the given address as it is written
    location = locator.geocode(address)
    
    
    #if doesn't work tweak the given address: remove any numbers,except the postal code, in the main part of the given address
    if location is None:
        street_address = re.sub(r'[0-9]+', '', street_address.split(',')[0])
        address = street_address + ', ' + PostalAddress['addressLocality'] + ', ' + PostalAddress['addressRegion'] + ', '+ PostalAddress['addressCountry']
        location = locator.geocode(address)
        
    #if doesn't work tweak the given address: get rid of address related verbs as Road, Street etc. additionally
    if location is None:
        street_address = street_abbv_remove(street_address)
        address = street_address + ', ' + PostalAddress['addressLocality'] + ', ' + PostalAddress['addressRegion'] + ', '+ PostalAddress['addressCountry']
        location = locator.geocode(address)
    
    #if it doesnt work just take the center of the city as the last resort.
    if location is None:
        address = PostalAddress['addressLocality'] + ', ' + PostalAddress['addressRegion'] + ', '+ PostalAddress['addressCountry'] + ', ' + PostalAddress['postalCode']
        location = locator.geocode(address)
        
    try:
        return [dict({'address': location.address, 'lon': location.longitude, 'lat' : location.latitude , 'point' : location.point})]
    except:
        return dict({})



#function that helps to make street related abbrivation changes.
def street_address_fix(StreetAddress):
    replacements = {'RD': 'ROAD',
                    'RD.': 'ROAD',
                    'CIR': 'CIRCLE',
                    'CIR.': 'CIRCLE',
                    'DR': 'DRIVE',
                    'DR.': 'DRIVE',
                    'LN': 'LANE',
                    'LN.': 'LANE',
                    'CT': 'COURT',
                    'CT.': 'COURT',
                    'PL': 'PLACE',
                    'PL.': 'PLACE',
                    'ST': 'STREET',
                    'ST.': 'STREET',
                    'BLVD': 'BOULEVARD',
                    'BLVD.': 'BOULEVARD'}

    StreetAddress = StreetAddress.upper().split()
    
    for i in range(len(StreetAddress)):
        if StreetAddress[i] in replacements.keys():
            StreetAddress[i] = replacements[StreetAddress[i]]
    
    StreetAddress = ' '.join(StreetAddress)
    StreetAddress = ' '.join( [s for s in StreetAddress.split() if len(s)>2] )


    return StreetAddress




def street_abbv_remove(StreetAddress):
    replacements = {'ROAD': ' ',
                    'CIRCLE': ' ',
                    'DRIVE': ' ',
                    'LANE': ' ',
                    'COURT': ' ',
                    'PLACE': ' ',
                    'STREET': ' ',
                    'BOULEVARD': ' '}

    StreetAddress = StreetAddress.upper().split()
    
    for i in range(len(StreetAddress)):
        if StreetAddress[i] in replacements.keys():
            StreetAddress[i] = replacements[StreetAddress[i]]
            
    StreetAddress = ' '.join(StreetAddress)
    StreetAddress = ' '.join( [s for s in StreetAddress.split() if len(s)>2] )


    return StreetAddress


#The main part, for loop and the functions within returns a list of dictionaries, one needs to convert them 
#into dataframe in order to get something like the one that I shared in the dataset section.

URL = "https://locations.traderjoes.com/"

page = requests.get(URL)
soup = BeautifulSoup(page.content, "html.parser")
geopy.geocoders.options.default_timeout = 25 #set high to not get Max retries exceeded type of error
locator = Nominatim(user_agent="personal_project")


stores = []
states = states2cities(soup) #lists of all the states url where store related informations exist

for j in range(len(states)): #state -> city
    for i in range(len(states[j])):   #city -> store
        tmp = city2stores(states[j][i])
        for k in range(len(tmp)):  # ..stores..
            a = city_geocode(tmp[k])
            stores.extend(a)
            
        
#with open('stores.pickle', 'wb') as handle:
#pickle.dump(stores, handle, protocol=pickle.HIGHEST_PROTOCOL)


#Small fix with one address

stores_data = pd.DataFrame(stores)

address = stores_data[stores_data.lon==stores_data.lon.max()].address
locator = Nominatim(user_agent="personal_project")

stores[384]['address'] = locator.geocode('77 Boston Turnpike, Shrewsbury, MA,USA').address
stores[384]['lon'] =locator.geocode('77 Boston Turnpike, Shrewsbury, MA,USA').longitude
stores[384]['lat'] = locator.geocode('77 Boston Turnpike, Shrewsbury, MA,USA').latitude
stores[384]['point'] = locator.geocode('77 Boston Turnpike, Shrewsbury, MA,USA').point



#Ground Truths of Warehouse addresses
warehouse_address = ['Nazareth, PA 18064, USA', 'Suwanee, GA 30024, USA', '30 Commerce Blvd, Middleborough, MA , USA',
                    'Minooka 60447, IL, USA','5111 Bear Creek Ct, Irving, TX 75061, USA','2388 Mason Ave, Daytona Beach, FL 32117, USA',
                    '200 Phoenix Xing, Bloomfield, CT 06002, USA','10288 Calabash Ave, Fontana, CA 92335, USA','2121 Boeing Way, Stockton, CA 95206, USA',
                    '3707 Hogum Bay Rd NE, Lacey, WA 9851','4681 Edison Ave, Chino, CA 91710, USA','10401 W Van Buren St, Tolleson, AZ 85353, USA']

def real_warehouse_address(rwa):
    
    adrs = locator.geocode(rwa)
    return [dict({'address': adrs.address, 'lon': adrs.longitude, 'lat' : adrs.latitude , 'point' : adrs.point})]

    
rwa = []
for adrs in warehouse_address:
    rwa.append(real_warehouse_address(adrs))


### Analysis Part

coordinates = stores_data[['lon','lat']].values
#standardize? or Not
#scaler = StandardScaler()
#scaled_coordinates = scaler.fit_transform(coordinates)

kmeans = KMeans(
    init="k-means++",
    n_clusters=19,
    n_init=10,
    max_iter=100, random_state=17)
kmeans.fit(coordinates)

warehouse = pd.DataFrame(kmeans.cluster_centers_, columns = ['lon','lat'])
labels = pd.DataFrame(kmeans.labels_, columns= ['labels'])
stores_data = pd.concat([stores_data,labels], axis = 1 ) 
stores_data['labels'] = stores_data['labels'].astype(str)



#Mapping with folium part
m = folium.Map(location=[37, -102], zoom_start=4)

stores_data.apply(lambda row:folium.CircleMarker(location=[row["lat"], row["lon"]], 
                                              radius=1.5, color='orange')
                                             .add_to(m), axis=1)


for w in range(len(warehouse)):

    folium.CircleMarker(
        location=[warehouse.iloc[w]['lat'],warehouse.iloc[w]['lon']],
        radius=5,
        popup="Laurelhurst Park",
        color="darkred",
        fill=True,
        fill_color="darkred",
    ).add_to(m)
    
for j in stores_data.labels.unique():
    temp = stores_data[stores_data.labels==j]
    for i in range(len(temp)):
        folium.PolyLine([(warehouse.loc[int(j)].lat,warehouse.loc[int(j)].lon),(temp.iloc[i].lat,temp.iloc[i].lon)],
                        color='black',
                        weight=1,
                        opacity=0.6).add_to(m)    
        

        
for k in range(len(rwa)):   
    
    folium.CircleMarker(
        location=[rwa[k][0]['lat'],rwa[k][0]['lon']],
        radius=5,
        color="green",
        fill=True,
        fill_color="green",
        opacity = 1
    ).add_to(m)


m


# In[ ]:
#stores_data.groupby(['labels']).address.count()

