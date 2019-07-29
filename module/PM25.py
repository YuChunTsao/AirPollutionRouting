import requests, json
import numpy as np
import pandas as pd
import geopandas as gpd
from dateutil.parser import parse
from shapely.geometry import MultiPolygon, Polygon, Point

class PM25:
    """
        return pandas dataframe
    """
    def __init__(self):
        self.url = 'https://pm25.lass-net.org/GIS/IDW/data/data.json'
        self.time = None
        # as a filename
        self.parseTime = None
        self.points = None
        self.columns = None
        self.pm25 = None

        self.__get()

    
    def __get(self):
        r = requests.get(self.url)
        result = r.json()

        self.time = result['latest-updated-time']
        self.points = result['points']
        self.columns = result['point-meta']

        b = parse(self.time)
        self.parseTime = b.strftime("%Y%m%dT%H%M%SZ")

        self.pm25 = pd.DataFrame(self.points, columns=self.columns)

        print(self.time)
        print(self.parseTime)
        # print(self.points)
        print(self.columns)
        
    def selectPoints(self):
        """ select points by location """
        ### TWD97's WGS84 bounds
        # 114.32 17.36
        # 123.61 26.96
        ### 

        self.pm25 = self.pm25.loc[self.pm25['gps_lat'] > 17.36]
        self.pm25 = self.pm25.loc[self.pm25['gps_lat'] < 26.96]
        self.pm25 = self.pm25.loc[self.pm25['gps_lon'] > 114.32]
        self.pm25 = self.pm25.loc[self.pm25['gps_lon'] < 123.61]       

        ### create geometry
        self.pm25['Coordinates'] = list(zip(self.pm25.gps_lon, self.pm25.gps_lat))
        self.pm25['Coordinates'] = self.pm25['Coordinates'].apply(Point)

        ### create geodataframe
        pm25_point_wgs84 = gpd.GeoDataFrame(self.pm25, geometry='Coordinates')
        pm25_point_wgs84.crs = {'init' :'epsg:4326'}

        #### reproject (epsg:4326 -> epsg:3826)
        crs = "+proj=tmerc +lat_0=0 +lon_0=121 +k=0.9999 +x_0=250000 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs"
        pm25_point = pm25_point_wgs84.to_crs(crs)

        ### select layer by location (taipei county - twd97)
        taipei_county_twd97 = gpd.read_file('../data/taipei_county_twd97.shp')

        ### check point(pm25_point_twd97) wthin polygon(taipei_county_twd97)
        polygon = taipei_county_twd97.geometry[0]
        result = pm25_point.within(polygon)    # within() will return bool
        result = result * 1

        ### clip
        self.pm25['status'] = result.tolist()
        pm25_point = gpd.GeoDataFrame(self.pm25, geometry='Coordinates')
        pm25_point.crs = {'init' :'epsg:4326'}

        ### reproject
        crs = "+proj=tmerc +lat_0=0 +lon_0=121 +k=0.9999 +x_0=250000 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs"
        pm25_point = pm25_point.to_crs(crs)
        taipei_pm25_point = pm25_point.loc[pm25_point['status'] == 1]   

        # remove bias
        df = taipei_pm25_point[taipei_pm25_point['pm2.5'] > taipei_pm25_point['pm2.5'].mean() + 3*taipei_pm25_point['pm2.5'].std()]
        taipei_pm25_point = taipei_pm25_point.drop(df.index.tolist())

        ### output file 
        taipei_pm25_point.to_file('../data/points/taipei_pm25_point_' + self.parseTime + '.shp', driver='ESRI Shapefile', encoding='utf-8')      

        return taipei_pm25_point

if __name__ == '__main__':
    pm25 = PM25()
    points = pm25.selectPoints()
    print(points)
    