import numpy as np
import networkx as nx

from mesa import Model, Agent
from mesa.time import RandomActivation
#from mesa.space import MultiGrid

from layer_grid import LayeredGrid

from weather_model import WeatherSubmodel, AirCell
from language_model import RandomLanguageModel, MarkovLanguage
from sailing_model import Port, Ship, calculate_sea_lanes
from utils import (weighted_random, make_weighted_syllables, make_word, 
                   make_place_name_model, rotate_vector)

class IslandCell:
    ''' One tile of land.
    '''
    layer = "Land"
    
    def __init__(self, pos, island):
        ''' Set a new tile of land.
        
        TODO: Any other properties the cell might have.
        '''
        self.pos = pos
        self.island = island
        self.landlocked = False

class Island(Agent):
    ''' An island is composed of multiple tiles.
    '''
    def __init__(self, name, model):
        self.unique_id = name
        self.model = model
        self.cells = []
    
    def grow(self):
        ''' Add a cell in an empty adjacent tile.
        '''
        grid = self.model.grid
        possible_cells = []
        # Find open cells nearby
        # This can probably be more efficient, but premature optimization etc.
        for cell in self.cells:
            if cell.landlocked: continue
            neighbors = grid.get_neighborhood(cell.pos, False) # No diagonals
            landlocked = True
            for c in neighbors:
                x, y = c
                #if grid.is_cell_empty(c):
                if grid[x][y]["Land"] is None:
                    possible_cells.append(c)
                    landlocked = False
            cell.landlocked = landlocked
        next_cell = self.random.choice(possible_cells)
        new_island = IslandCell(next_cell, self)
        self.cells.append(new_island)
        grid.place_agent(new_island, next_cell)

class Person(Agent):
    layer = "People"
    
    def __init__(self, unique_id, name, model):
        '''
        '''
        self.unique_id = unique_id
        self.model = model
        self.name = name
        self.pos = None  # Will get handled when agent is added to grid.
    
    def step(self):
        # Take a random step to an adjacent non-water tile
        grid = self.model.grid
        possible_steps = []
        for x, y in grid.get_neighborhood(self.pos, True):
            #if len(grid[x][y]) > 0:
            if grid[x][y]["Land"] is not None:
                possible_steps.append((x, y))
        next_step = self.random.choice(possible_steps)
        # TODO: Better logging of actions
        # print(f"{self.name} moved from {self.pos} to {next_step}")
        grid.move_agent(self, next_step)


class WorldModel(Model):
    
    def __init__(self, n_islands=1, land_fraction=0.25, n_agents=100):
        
        self.schedule = RandomActivation(self)
        self.running = True
        
        # Set world parameters
        self.width = 100
        self.height = 100
        #self.grid = MultiGrid(self.height, self.width, torus=True)
        self.grid = LayeredGrid(self.width, self.height, torus=True, 
                                layers={"Land": "Single", 
                                        "People": "Multi",
                                        "Ships": "Multi",
                                        "Weather": "Single"})
        
        # Set up islands
        self.n_islands = n_islands
        self.land_fraction = land_fraction
        self.islands = []
        self.make_islands()
        
        # Generate language
        #self.language = RandomLanguageModel()
        self.language = MarkovLanguage.make_psuedo_english()
        
        # Set up people
        self.n_agents = n_agents
        # self.create_agents()
        
        # Set up seafaring: ports and shipping lanes
        self.ports = {}
        self.ports_per_island = 1
        self.create_ports()
        self.sea_lanes = calculate_sea_lanes(self)
        
        # Set up ships
        self.make_ships()
        
        # Set up weather
        self.weather = WeatherSubmodel(self)
        self.weather.setup_weather()
        
        # Set up logging
        self.verbose = False
        self._log = []
    
    def make_islands(self):
        ''' Grow islands one random adjacent cell at a time.
        '''
        # Create islands
        for i in range(self.n_islands):
            island = Island(i, self)
            starting_cell = (self.random.randrange(0, self.width),
                             self.random.randrange(0, self.height))
            first_cell = IslandCell(starting_cell, island)
            island.cells.append(first_cell)
            self.grid.place_agent(first_cell, first_cell.pos)
            self.islands.append(island)
        
        # Create land
        total_cells = int(self.land_fraction * self.width * self.height)
        for _ in range(total_cells):
            island = self.random.choice(self.islands)
            island.grow()
    
    def create_agents(self):
        ''' Create Person agents, who walk around on land.
        TODO: Do something more interesting with them.
        '''
        for i in range(self.n_agents):
            #name = make_word(self.syllable_weights)
            syllables = self.random.choice([2, 3, 3, 3, 4, 5])
            name = self.language.make_word(syllables)
            agent = Person(i, name, self)
            # Pick a starting island and cell
            island = self.random.choice(self.islands)
            cell = self.random.choice(island.cells)
            self.grid.place_agent(agent, cell.pos)
            self.schedule.add(agent)
    
    def make_ships(self):
        ports = list(self.ports.values())
        for i in range(self.n_agents):
            #name = f"Ship {i}"
            name = self.language.make_ship_name()
            port = self.random.choice(ports)
            ship = Ship(name, name, self, port)
            self.grid.place_agent(ship, port.pos)
            self.schedule.add(ship)
    
    def create_ports(self):
        ''' Choose random non-landlocked island cell for a port 
        
        TODO: Make sure ports aren't placed on lakes where there's no outlet
        to any other ports.
        '''
        port_count = 0
        for island in self.islands:
            possible_cells = [cell for cell in island.cells 
                              if not cell.landlocked]
            for _ in range(self.ports_per_island):
                cell = self.random.choice(possible_cells)
                name = self.language.make_place_name()
                self.language.add_place_name(name)
                port = Port(name, cell.pos)
                self.grid.place_agent(port, cell.pos)
                self.ports[name] = port
                port_count += 1
    

    def step(self):
        self.weather.weather_step()
        self.schedule.step()
    
    def log(self, message):
        log_entry = f"{self.schedule.steps}: {message}"
        if self.verbose:
            print(log_entry)
        self._log.append(log_entry)
        
        
        
        
        
        
        