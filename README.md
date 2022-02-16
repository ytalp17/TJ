# On the Trail of Trader Joe's Warehouses


Recently, I came across a 2015 project by Sam Burer via Hacker News archive. In his project, Sam mainly tries to find the location of warehouses/distribution centers of a well-known grocery retailer called Trader Joe's by just using the location of its stores in the US. He does it very creatively by exploiting centroids of the clusters suggested by the K-means algorithm, a basic algorithm that is primarily used to tackle unsupervised, clustering, problems in the Machine learning domain.

With this project I aim to update his work with a small tweak, you can see it as the 2022 version of [Sam's original post](https://sburer.github.io/2015/06/02/Trader-Joes.html). 

One can find not only the source code of the project but also the dataset that I created by scraping Trader Joe's website. The TraderJoes dataset contains both raw and geocoded addresses of every store Trader Joe's has in the United States. The data is scraped from [TraderJoe's site](https://locations.traderjoes.com/) using the [Beautiful Soup](https://beautiful-soup-4.readthedocs.io/en/latest/) static web scraping module on Python. The code that is used for scraping is also shared in the 'Code' section. Moreover, The dataset has a GeoDataFrame format, with the point location of each store being a shapely object. Hence, it can be utilized better with [the Geopandas module.](https://geopandas.org/en/stable/).

Feel free to utilize the dataset for your own purpose :v:
