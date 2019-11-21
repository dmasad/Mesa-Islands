'''
Weather submodel
'''

from itertools import product
import numpy as np
from mesa import Agent
from utils import rotate_vector

class AirCell(Agent):
    layer = "Weather"
    
    # Weather model parameters
    land_temp = 0.012
    water_temp = 0.01 #0.005
    cloudy_factor = 0.75 #0.5
    
    land_humidity = 0.01
    water_humidity = 0.05
    rain_temp = -0.02
    
    def __init__(self, unique_id, model, starting_temp, starting_humidity,
                 wind_vector=[0,0]):
        self.unique_id = unique_id
        self.model = model
        self.temperature = starting_temp
        self.humidity = starting_humidity
        self.wind_vector = wind_vector
        self.next_temperature = self.temperature
        self.next_humidity = self.humidity
        self.pos = (-1, -1)
        
        self.cloudy = False
        self.raining = False
    
    def convey_weather(self):
        ''' Carry temperature and humidity to the next cell based on the wind
        '''
        grid = self.model.grid
        x, y = self.pos
        next_x = round(x + self.wind_vector[0])
        next_y = round(y + self.wind_vector[1])
        next_x, next_y = grid.torus_adj((next_x, next_y))
        next_cell = grid[next_x][next_y]["Weather"]
        next_cell.next_temperature = self.temperature
        next_cell.next_humidity = self.humidity
    
    def update_cell(self):
        self.temperature = self.next_temperature
        self.humidity = self.next_humidity
        
        grid = self.model.grid
        x, y = self.pos
        # Update temperature
        if grid[x][y]["Land"] is not None:
            delta = self.land_temp
        else:
            delta = self.water_temp
        if self.cloudy:
            delta *= self.cloudy_factor
        self.temperature += delta
        if self.raining:
            self.temperature -= delta
        # Adjust for wind speed
        # Faster winds cool the air down
        # Assumes the wind speed is roughly in the (0, 3) range
        wind_speed = (self.wind_vector[0]**2 + self.wind_vector[1]**2)**0.5
        self.temperature -= wind_speed * 0.01
        
        # Update humidity
        if self.raining:
            #self.humidity -= 0.05
            self.humidity *= 0.8
        elif grid[x][y]["Land"] is None:
            self.humidity += self.water_humidity
        else:
            self.humidity += self.land_humidity
            #self.humidity += np.random.normal(0.03, 0.01)
        
    def average_cell(self):
        neighbors = self.model.grid.get_neighbors(self.pos, True, True)
        neighbors = [cell for cell in neighbors if cell.layer=="Weather"]
        nearby_temp = sum(cell.temperature for cell in neighbors)/len(neighbors)
        nearby_humidity = sum(cell.humidity for cell in neighbors)/len(neighbors)
        self.temperature = (self.temperature + nearby_temp)/2
        self.humidity = (self.humidity + nearby_humidity)/2
    
    
    def update_weather(self):
        self.cloudy = (self.humidity > 0.6 + 0.3 * self.temperature)    
        self.raining =  (self.humidity > 0.6 + 0.5 * self.temperature)

class WeatherSubmodel:
    ''' Convenience class to group the methods involved in the weather submodel
    '''
    def __init__(self, model):
        ''' Instantiate a weather submodel attached to the parent model
        '''
        
        self.model = model
        # Convenience pass-throughs to keep line lengths shorter
        self.grid = model.grid
        self.random = model.random
        
        self.width = model.width
        self.height = model.height
        
        self.weather_cells = []
        starting_wind_direction = self.random.randrange(0, 360)
        self.wind = rotate_vector(np.array([1, 0]), 
                                  np.radians(starting_wind_direction))
        
    def setup_weather(self):        
        self.weather_cells = []
        for (x, y) in product(range(self.width), range(self.height)):
            weather_cell = AirCell(f"Cell{x}{y}", self.model, 0.7, 
                                    self.model.random.random(), (0, 0))
            #self.schedule.add(weather_cell)
            self.weather_cells.append(weather_cell)
            self.model.grid.place_agent(weather_cell, (x, y))
        self.update_wind()
    
    def update_wind(self, wind=None):
        ''' Compute a vector field for winds and update all cells.
        '''
        if wind is None:
            wind = self.wind
        
        # Set up the wind vector field
        scale = 1
        x = np.linspace(-scale, scale, self.width)
        y = np.linspace(-scale, scale, self.height)
        X, Y = np.meshgrid(x, y)
        U = wind[0] - X**2 + Y
        V = wind[1] + X - Y**2
        for (x, y) in product(range(self.width), range(self.height)):
            wind_vector = [float(U[x, y]), float(V[x, y])]
            self.grid[x][y]["Weather"].wind_vector = wind_vector
    
    def weather_step(self):
        ''' Advance the weather by one timestep.
        
        Not handled via the parent model's scheduler since (a) the sequential
        multi-stage updating doesn't play nicely with most schedulers, and
        (b) one weather timestep may not be the same as one agent timestep.
        '''   
        # Rotate the global wind vector randomly and update
        self.wind = rotate_vector(self.wind, self.random.normalvariate(0, 0.5))
        self.update_wind()
        # Run each method for each cell; this is easier than four for loops
        for method in ["convey_weather", "update_cell", 
                       "average_cell", "update_weather"]:
            for cell in self.weather_cells:
                getattr(cell, method)()
    