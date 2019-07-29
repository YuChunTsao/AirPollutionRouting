from PM25 import PM25
from Grid import Grid

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import MultiPolygon, Polygon, Point

class IDW:
    def __init__(self, x, y, v, grid, power):
        self.x = x
        self.y = y
        self.v = v
        self.grid = grid
        self.power = power
        self.result = self.__calculate()
        self.polygon = self.__toPolygon()

    def __calculate(self):
        grid = self.grid.create()
        for i in range(grid.shape[0]):
            for j in range(grid.shape[1]):
                distance = np.sqrt((self.x-i)**2+(self.y-j)**2)
                if (distance**self.power).min()==0: 
                    grid[i,j] = self.v[(distance**self.power).argmin()]
                else:
                    total = np.sum(1/(distance**self.power))
                    grid[i,j] = np.sum(self.v/(distance**self.power)/total)
        return grid
    
    def __toPolygon(self):
        # x, y origin
        XleftOrigin = self.grid.minx
        XrightOrigin = self.grid.minx + self.grid.size
        YtopOrigin = self.grid.maxy
        YbottomOrigin = self.grid.maxy - self.grid.size

        polygons = []

        for i in range(self.grid.rows):
            Xleft = XleftOrigin
            Xright = XrightOrigin
            for j in range(self.grid.columns):
                polygons.append(Polygon([(Xleft, YtopOrigin), (Xright, YtopOrigin), (Xright, YbottomOrigin), (Xleft, YbottomOrigin)]))
                Xleft = Xleft + self.grid.size
                Xright = Xright + self.grid.size        
            YtopOrigin = YtopOrigin - self.grid.size
            YbottomOrigin = YbottomOrigin - self.grid.size

        self.result = self.result[::-1]
        pm25_value = self.result.ravel()

        df = pd.DataFrame({
            'value': pm25_value
        })
        crs = "+proj=tmerc +lat_0=0 +lon_0=121 +k=0.9999 +x_0=250000 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs"
        grid = gpd.GeoDataFrame(df, geometry=polygons, crs=crs)  

        return grid
        # grid.plot(column='value', cmap='RdYlGn_r')
        # plt.show()      
    
    def toGeoJSON(self, gdf, output_time):
        crs = "+proj=longlat +datum=WGS84 +no_defs"
        intersection_wgs84 = gdf.to_crs(crs)
        color_list = []
        for i in range(len(intersection_wgs84)):
            value = intersection_wgs84.iloc[i]['value']
            color = self.__setColor(value)
            color_list.append(color) 
                    
        intersection_wgs84["color"] = color_list    
        intersection_wgs84["geometry"] = [MultiPolygon([feature]) if type(feature) == Polygon else feature for feature in intersection_wgs84["geometry"]]
        intersection_wgs84.to_file('../data/grids/taipei_grid_' + str(self.grid.size) + 'm_' + output_time + '.geojson', driver='GeoJSON', encoding='utf8')    

    def __setColor(self, value):
        color = None
        if value <= 15.4:
            color = '#00E800'
        if value > 15.4 and value <= 35.4:
            color = '#FFFF00'
        if value > 35.4 and value <= 54.4:
            color = '#FF7E00'
        if value > 54.4 and value <= 150.4:
            color = '#FF0000'
        if value > 150.4 and value <= 250.4:
            color = '#8F3F97'
        if value > 250.4 and value <= 350.4:
            color = '#7E0023'
        if value > 350.4 and value <= 500.4:
            color = '#7E0023'

        return color        

if __name__ == '__main__':
    pm25 = PM25()
    points = pm25.selectPoints()

    # type is Point
    geometry = points.geometry

    taipei_county_twd97 = gpd.read_file('../data/taipei_county_twd97.shp')
    bounds = taipei_county_twd97.bounds
    grid = Grid(500, bounds)

    # get lat, lng and value
    x = [int(np.ceil((lat - grid.minx)/grid.size)) for lat in geometry.x]
    x = np.asarray(x)
    y = [int(np.ceil((lng - grid.miny)/grid.size)) for lng in geometry.y]
    y = np.asarray(y)
    v = [value for value in points['pm2.5']]
    v = np.asarray(v) 
    idw = IDW(y,x,v,grid,2)

    intersection = gpd.overlay(taipei_county_twd97, idw.polygon, how='intersection')
    intersection.to_file('../data/grids/taipei_grid_' + str(grid.size) + 'm_' + pm25.parseTime + '.shp', driver='ESRI Shapefile', encoding='utf-8')

    idw.toGeoJSON(intersection, pm25.parseTime)

    