import json
import requests
import openrouteservice
from openrouteservice import convert
from module.Exposure import Exposure

from geojson import Feature, Point , LineString, FeatureCollection
import polyline
import geopandas as gpd
from pyproj import Proj
from shapely import geometry
from shapely.geometry import shape, Polygon, mapping, MultiPolygon, LineString, Point

class Direction:
    def __init__(self, origin, destination, mode):
        # 設定起點終點進行路線規劃
        print("open route service directions api")
        f = open("./APIKEY", "r")
        self.key = f.read()
        self.origin = origin
        self.destination = destination
        self.mode = mode
        self.client = openrouteservice.Client(key=self.key) # Specify your personal API key
        self.avoided_point_list = []
        self.idw_grid = gpd.read_file('./data/taipei_grid_500m_20190610052502.geojson')
        # self.barriers_level_1 = self.__selectBarriers(1)
        # self.barriers_level_2 = self.__selectBarriers(2)
        # self.barriers_level_3 = self.__selectBarriers(3)
        self.barriers = []
        # self.barriers.append(self.barriers_level_1)
        # self.barriers.append(self.barriers_level_2)
        # self.barriers.append(self.barriers_level_3)

    def start(self):
        routes_list = []
        # 第一次路線規劃 - 最短路徑
        ORS_route, ORS_route_steps = self.CreateRoute()
        exposure = Exposure(ORS_route, ORS_route_steps)

        # geodataframe
        exposure_route = exposure.calculate()
        routes_list.append(exposure_route)

        self.barriers_level_1 = self.__selectBarriers(1, ORS_route)
        self.barriers_level_2 = self.__selectBarriers(2, ORS_route)
        self.barriers_level_3 = self.__selectBarriers(3, ORS_route)

        self.barriers.append(self.barriers_level_1)
        self.barriers.append(self.barriers_level_2)
        self.barriers.append(self.barriers_level_3)        
        
        barriers_list = []
        for index, barrier in enumerate(self.barriers):
            print("level = " + str(index))
            for geom, value in zip(barrier.geometry, barrier.value):
                poly = list(geom)[0]
                # self.avoided_point_list = []
                self.avoided_point_list.append(poly)

                # # 障礙區顯示 - GeoJSON
                barrier = Feature(geometry=poly, properties={"value": value}) 
                barriers_list.append(barrier)

                try:
                    ORS_route, ORS_route_steps = self.CreateRoute()

                    # calculate air pollution exposure
                    exposure = Exposure(ORS_route, ORS_route_steps)
                    exposure_route = exposure.calculate()

                    # 判斷若路線相同就不回傳
                    total_distance = exposure_route['route_info']['total_distance']
                    if total_distance in [route['route_info']['total_distance'] for route in routes_list]:
                        print("same")
                    else:
                        routes_list.append(exposure_route)
                    print('Generated alternative route, which avoids affected areas.')  

                except Exception: 
                    print('Sorry, there is no route available between the requested destination because of too many blocked streets.')   

        # 依照空氣污染總暴露量進行排序，由小至大。
        # routes_list.sort(key=lambda x: x['route_info']['total_exposure'])
        routes_list.sort(key=lambda x: x['route_info']['average_exposure'])


        # 回傳前五筆
        if len(routes_list) < 5:
            result = {"result": routes_list[0:len(routes_list)]}
        else:
            result = {"result": routes_list[0:5]}

        return result

    def CreateRoute(self):
        coords = [[self.origin['lng'], self.origin['lat']], [self.destination['lng'], self.destination['lat']]]
        route_request = {'coordinates': coords, 
                        'format_out': 'geojson',
                        'profile': self.mode,
                        'preference': 'shortest',
                        'instructions': True,
                        'options': {'avoid_polygons': geometry.mapping(MultiPolygon(self.avoided_point_list))}} 
        
        # result = client.directions(coords,  profile=self.mode)
        ORS_route = self.client.directions(**route_request)
        ORS_route_steps = self.__toGeoJSON(ORS_route)

        # with open('./data/ORS_route.geojson', 'w') as outfile:
        #     json.dump(ORS_route, outfile)   

        return ORS_route, ORS_route_steps


    def __selectBarriers(self, level, route):
        # 普通
        if level == 1:
            min = 15.4
            # max = 35.4

        # 對敏感族群不健康
        if level == 2:
            min = 35.4
            # max = 54.4


        # 對所有族群不健康
        if level == 3:
            min = 54.4
            # max = 150.4   

        barriers_level = self.idw_grid.loc[self.idw_grid['value'] > min] 

        # 與路線交集的障礙區
        route_gdf = gpd.GeoDataFrame.from_features(route)
        # route = gpd.read_file('./data/ORS_route.geojson')
        barriers = gpd.sjoin(barriers_level, route_gdf, op='intersects')
        # print(len(barriers))
        # print(barriers)

        return barriers

    
    def __toGeoJSON(self, data):
        geometry = data['features'][0]['geometry']
        steps = data['features'][0]['properties']['segments'][0]['steps']
        coordinates = geometry['coordinates']   
        metadata = data['metadata']
        profile = metadata['query']['profile']
        timestamp = metadata['timestamp']   

        legs = []
        for step in steps:
            points_index = step['way_points']
            if points_index[0] == points_index[1]:
                print("line end")
                continue
            else:
                points = coordinates[points_index[0]:points_index[1] + 1]
                linestring = LineString(points)

                leg = Feature(geometry = linestring, properties= {
                    'distance': step['distance'],
                    'duration': step['duration'],
                    'type': step['type'],
                    'instruction': step['instruction'],
                    'name': step['name'],
                    'way_points': step['way_points'],
                    'profile': profile,
                    'timestamp': timestamp
                })

                legs.append(leg)
            
        legs = FeatureCollection(legs)

        # print(json.dumps(legs, indent=4, sort_keys=True))

        with open('./data/ORS_route_steps.geojson', 'w') as outfile:
            json.dump(legs, outfile)        

        return legs


