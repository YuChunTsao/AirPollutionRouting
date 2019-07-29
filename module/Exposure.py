import os
import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.ops import transform
from functools import partial
import pyproj
import matplotlib.pyplot as plt
from geojson import Feature, FeatureCollection

class Exposure:
    def __init__(self, ORS_route, ORS_route_steps):
        self.idw_grid = gpd.read_file('./data/taipei_grid_500m_20190610052502.geojson')
        # self.route = gpd.read_file('./data/ORS_route.geojson')
        # self.route_steps = gpd.read_file('./data/ORS_route_steps.geojson')
        self.route = gpd.GeoDataFrame.from_features(ORS_route)
        self.route_steps = gpd.GeoDataFrame.from_features(ORS_route_steps)
        self.grid = self.__cutWithRouteBound()

    # cut grid with route's bound
    def __cutWithRouteBound(self):
        bounding_box = self.route.envelope
        df = gpd.GeoDataFrame(gpd.GeoSeries(bounding_box), columns=['geometry'])
        self.idw_grid['grid_ID'] = self.idw_grid.index.tolist()
        intersections = gpd.overlay(df, self.idw_grid, how='intersection')
        # polygon
        return intersections     

    def calculate(self):
        data = []

        # reproject
        project = partial(
            pyproj.transform,
            pyproj.Proj(init='EPSG:4326'),
            pyproj.Proj(init='EPSG:3826')
        )    
        
        # intersects
        for index1, r in self.route_steps.iterrows():
            for index2, g in self.grid.iterrows():
                if r.geometry.intersects(g.geometry) is True:
                    r_geom = r.geometry
                    r_geom = transform(project, r_geom)
                    g_geom = g.geometry
                    g_geom = transform(project, g_geom)

                    data.append({
                        'SID': index1,
                        'GID': g.grid_ID,
                        'distance': r_geom.intersection(g_geom).length,
                        'total_distance': r.distance,
                        'duration': r.duration * (r_geom.intersection(g_geom).length / r.distance),
                        'total_duration': r.duration,
                        'grid_pm25': g.value,
                        'instruction': r.instruction,
                        'profile': r.profile,
                        'geometry': r_geom.intersection(g_geom)                
                    })       

        result = gpd.GeoDataFrame(data)
        result['ID'] = result.index.tolist()
        result['distance_weights'] = result['distance'] / result['total_distance']
        result['segment_pm25'] = result['grid_pm25'] * result['distance_weights']  

        
        diss_result = result.dissolve(by='SID', aggfunc='sum')
        self.route_steps['segment_pm25'] = diss_result['segment_pm25']
        self.route_steps['distance_value'] = diss_result['distance']
        self.route_steps['duration_value'] = diss_result['duration']

        color_list = []
        for i in range(len(self.route_steps)):
            value = self.route_steps.iloc[i]['segment_pm25']
            color = self.setColor(value)
            color_list.append(color) 

        self.route_steps['color'] = color_list

        self.route_steps['segment_exposure'] = self.route_steps['segment_pm25'] * (self.route_steps['duration_value']/60) * 7

        # calculate total exposure 
        total_exposure = self.route_steps.segment_exposure.sum()
        # calculate total distance
        total_distance = self.route_steps.distance_value.sum()
        # calculate total duration
        total_duration = self.route_steps.duration_value.sum()
        # calculate average exposure
        average_exposure = ((self.route_steps['distance_value'] / total_distance) * self.route_steps['segment_pm25']).sum()

        print("total exposure = " + str(total_exposure) + ' ug/m3')
        print("total distance = " + str(total_distance) + ' meter')
        print("average exposure = " + str(average_exposure) + ' ug/m3')

        result = {
            "route_info": {
                "total_exposure": total_exposure,
                "total_distance": total_distance,
                "total_duration": total_duration,
                "average_exposure": average_exposure
            },
            "data": self.route_steps.to_json()
        }

        return result

    def setColor(self, value):
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

