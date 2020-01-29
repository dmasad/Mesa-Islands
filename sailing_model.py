''' Sailing submodel


'''
from itertools import product

import networkx as nx

from mesa import Agent

class Port:
    layer = "Ships"
    
    def __init__(self, name, pos):
        self.pos = pos
        self.name = name

class Ship(Agent):
    layer = "Ships"
    
    def __init__(self, unique_id, name, model, starting_port):
        ''' Create a ship
        '''
        self.unique_id = unique_id
        self.name = name
        self.model = model
        self.destination = None
        self.current_path = None
        self.current_step = None
        
        self.condition = "At port"
        self.current_port = starting_port.name
        self.pos = starting_port.pos
        self.log = []
    
    def choose_destination(self):
        ''' Chart a course to a random port.
        '''
        # Choose a port
        next_port = self.random.choice(list(self.model.ports.values()))
        if (self.current_port, next_port.name) not in self.model.sea_lanes:
            return
        
        self.destination = next_port.name
        self.condition = "Sailing"
        self.current_step = 0
        self.path = self.model.sea_lanes[(self.current_port, self.destination)]
        log_msg = f"{self.name} departed {self.current_port} for {self.destination}"
        self.model.log(log_msg)
        self.log.append(log_msg)
    
    def sail(self):
        self.current_step += 1
        if self.current_step == len(self.path):
            self.condition = "At port"
            self.current_port = self.destination
            self.destination = None
            log_msg = f"{self.name} arrived at {self.current_port}."
            self.model.log(log_msg)
            self.log.append(log_msg)
            return
            
        next_step = self.path[self.current_step]
        self.model.grid.move_agent(self, next_step)
    
    def add_to_log(self):
        
        log_entry = f"Day {self.model.schedule.steps}\n"
        if self.condition == "At port":
            log_entry += f"\tAt port at {self.current_port}\n"
        else:
            x, y = self.pos
            weather = self.model.grid[x][y]["Weather"]
            if weather.raining:
                log_entry += "\tRaining\n"
            elif weather.cloudy:
                log_entry += "\tCloudy\n"
            w_x, w_y = weather.wind_vector
            log_entry += f"\tWind: {w_x:.2f} by {w_y:.2f}\n"
            log_entry += f"\t Temperature: {weather.temperature:.1f}\n"
        self.log.append(log_entry)
        
    
    def step(self):
        self.add_to_log()
        if self.condition == "Sailing":
            self.sail()
        elif self.condition == "At port":
            if self.random.random() < 0.25:
                self.choose_destination()
                

def get_closest_land(model, cell):
    ''' Get the distance to the closest land cell, for weighting.
    '''
    min_dist = model.width + model.height
    for (x, y) in product(range(model.width), range(model.height)):
        if model.grid[x][y]["Land"] is None: continue
        dist = model.grid.get_distance((x, y), cell)
        min_dist = min(min_dist, dist)
    return min_dist
        

def calculate_sea_lanes(model):
    ''' Build a network of sea cells + ports, then calculate shortest paths
    '''
    # Build the graph
    # TODO: This can be streamlined for code aesthetics and performance
    G = nx.Graph()
    for x in range(model.width):
        for y in range(model.height):
            cell = (x, y)
            if model.grid[x][y]["Land"] is None:
                G.add_node(cell)
                for neighbor in model.grid.get_neighborhood(cell, False):
                    # Get distance from land
                    dist = get_closest_land(model, neighbor)
                    x, y = neighbor
                    if model.grid[x][y]["Land"] is None:
                        G.add_edge(cell, neighbor, weight=dist)
    # Add ports:
    for port in model.ports.values():
        G.add_node(port.pos)
        for neighbor in model.grid.get_neighborhood(port.pos, False):
            x, y = neighbor
            if model.grid[x][y]["Land"] is None:
                G.add_edge(port.pos, neighbor)
    
    # Now do the pathfinding:
    sea_lanes = {}
    for start_name, start_port in model.ports.items():
        for end_name, end_port in model.ports.items():
            if (start_name == end_name or 
                (end_name, start_name) in sea_lanes): 
                continue
            try:
                path = nx.shortest_path(G, start_port.pos, end_port.pos,
                                        weight='weight')
                sea_lanes[(start_name, end_name)] = path
                path = list(path)
                path.reverse()
                sea_lanes[(end_name, start_name)] = path
            except:
                print(f"Could not find path between {start_name} and {end_name}")
    return sea_lanes
            