import numpy as np
import pandas as pd
import geopandas as gpd

class Grid:
    def __init__(self, size, bounds):
        self.size = size
        self.bounds = bounds
        self.minx = None
        self.miny = None
        self.maxx = None
        self.maxy = None
        self.rows = None
        self.columns = None       
        self.grid = self.create()

    def create(self):
        self.bounds['minx'] -= self.bounds['minx'] % self.size
        self.bounds['miny'] -= self.bounds['miny'] % self.size
        self.bounds['maxx'] = self.bounds['maxx'] - (self.bounds['maxx'] % self.size) + self.size
        self.bounds['maxy'] = self.bounds['maxy'] - (self.bounds['maxy'] % self.size) + self.size

        self.minx = np.min(self.bounds['minx'])
        self.miny = np.min(self.bounds['miny'])
        self.maxx = np.max(self.bounds['maxx'])
        self.maxy = np.max(self.bounds['maxy'])

        # grid
        gridx = np.arange(self.minx, self.maxx, self.size)
        gridy = np.arange(self.miny, self.maxy, self.size)

        self.rows = len(gridy)
        self.columns = len(gridx)

        grid = np.zeros((self.rows, self.columns),dtype='float32')

        return grid