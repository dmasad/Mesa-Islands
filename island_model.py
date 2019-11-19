import networkx as nx

from mesa import Model, Agent
from mesa.time import RandomActivation
#from mesa.space import MultiGrid
from layer_grid import LayeredGrid

from utils import (weighted_random, make_weighted_syllables, make_word, 
                   make_place_name_model)

import tracery

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
        self.model.log(f"{self.name} departed {self.current_port} for {self.destination}")
    
    def sail(self):
        self.current_step += 1
        if self.current_step == len(self.path):
            self.condition = "At port"
            self.current_port = self.destination
            self.destination = None
            self.model.log(f"{self.name} arrived at {self.current_port}.")
            return
            
        next_step = self.path[self.current_step]
        self.model.grid.move_agent(self, next_step)
    
    def step(self):
        if self.condition == "Sailing":
            self.sail()
        elif self.condition == "At port":
            if self.random.random() < 0.25:
                self.choose_destination()


class AirCell(Agent):
    layer = "Weather"
    # Weather model parameters
    land_temp = 0.01
    water_temp = 0.005
    cloudy_factor = 0.5
    
    land_humidity = 0
    water_humidity = 0.05
    rain_temp = -0.02
    
    def __init__(self, unique_id, model, starting_temp, starting_humidity):
        self.unique_id = unique_id
        self.model = model
        self.temperature = starting_temp
        self.humidity = starting_humidity
        self.pos = None
        
        self.cloudy = False
        self.raining = False
    
    def step(self):
        grid = self.model.grid
        x, y = self.pos
        x += self.model.wind[0]
        y += self.model.wind[1]
        grid.move_agent(self, grid.torus_adj((x, y)))
        
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
        
        # Update humidity
        if self.raining:
            self.humidity -= 0.05
        elif grid[x][y]["Land"] is None:
            self.humidity += self.water_humidity
        
        # Average with neighbors
        neighbors = grid.get_neighbors(self.pos, True, True)
        neighbors = [cell for cell in neighbors if cell.layer=="Weather"]
        nearby_temp = sum(cell.temperature for cell in neighbors)/len(neighbors)
        nearby_humidity = sum(cell.humidity for cell in neighbors)/len(neighbors)
        self.temperature = (self.temperature + nearby_temp)/2
        self.humidity = (self.humidity + nearby_humidity)/2
        
        
        #self.cloudy = (self.humidity > 0.3 + 0.3 * self.temperature)    
        #self.raining =  (self.humidity > 0.35 + 0.5 * self.temperature)
        self.cloudy = (self.humidity > 0.4 + 0.3 * self.temperature)    
        self.raining =  (self.humidity > 0.6 + 0.5 * self.temperature)
            
        

class WorldModel(Model):
    
    # Tracery grammar for naming things:
    grammar = {
        "virtue": ["Courage", "Kindness", "Wisdom", "Cunning", "Charity", 
                   "Mercy", "Love", "Pride", "Glory"],
        "title": ["Prince", "Princess", "Duke", "President", "Exilarch", 
                  "Duchess", "Elector", "Senator"],
        "ship_names": ["#virtue# of #place#", "#place# #virtue#", 
                       "#title# of #place#", "#place# #title#", 
                       "#virtue# #virtue#", "#title#'s #virtue#"]
    }
    
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
                                        "Weather": "Multi"})
        
        # Set up islands
        self.n_islands = n_islands
        self.land_fraction = land_fraction
        self.islands = []
        self.make_islands()
        
        # Generate language
        self.syllable_weights = make_weighted_syllables(3)
        self.make_place_name = make_place_name_model(self.syllable_weights, 
                                                     n_prefixes=2, 
                                                     prob_prefix=0.3,
                            syllable_count_weights={2: 1, 3: 3, 4: 1, 5:0.5})
        
        # Set up people
        self.n_agents = n_agents
        self.syllable_weights = make_weighted_syllables()
        # self.create_agents()
        
        # Set up seafaring: ports and shipping lanes
        self.ports = {}
        self.ports_per_island = 1
        #self.create_ports()
        self.sea_lanes = {}
        #self.calculate_sea_lanes()
        
        # Update ship naming scheme with port names
        self.grammar["place"] = [port for port in self.ports]
        self.grammar = tracery.Grammar(self.grammar)
        
        # Set up ships
        # self.make_ships()
        
        # Set up weather
        self.wind = [1, 0]
        self.setup_weather()
        
        # Set up logging
        self.verbose = True
        self._log = []
    
    def make_islands(self):
        '''
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
    
    def setup_weather(self):
        self.weather_cells = []
        for x in range(self.width):
            for y in range(self.height):
                weather_cell = AirCell(f"Cell{x}{y}", self, 0.7, 0)
                #self.schedule.add(weather_cell)
                self.weather_cells.append(weather_cell)
                self.grid.place_agent(weather_cell, (x, y))
    
    def create_agents(self):
        for i in range(self.n_agents):
            name = make_word(self.syllable_weights)
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
            name = self.grammar.flatten("#ship_names#")
            port = self.random.choice(ports)
            ship = Ship(name, name, self, port)
            self.grid.place_agent(ship, port.pos)
            self.schedule.add(ship)
    
    def create_ports(self):
        ''' Choose random non-landlocked island cell for a port 
        '''
        port_count = 0
        for island in self.islands:
            possible_cells = [cell for cell in island.cells 
                              if not cell.landlocked]
            for _ in range(self.ports_per_island):
                cell = self.random.choice(possible_cells)
                #name = f"Port {port_count}"
                name = self.make_place_name()
                port = Port(name, cell.pos)
                self.grid.place_agent(port, cell.pos)
                self.ports[name] = port
                port_count += 1
    
    def calculate_sea_lanes(self):
        ''' Build a network of sea cells + ports, then calculate shortest paths
        '''
        # Build the graph
        # TODO: This can be streamlined for code aesthetics and performance
        G = nx.Graph()
        for x in range(self.width):
            for y in range(self.height):
                cell = (x, y)
                if self.grid[x][y]["Land"] is None:
                    G.add_node(cell)
                    for neighbor in self.grid.get_neighborhood(cell, False):
                        x, y = neighbor
                        if self.grid[x][y]["Land"] is None:
                            G.add_edge(cell, neighbor)
        # Add ports:
        for port in self.ports.values():
            G.add_node(port.pos)
            for neighbor in self.grid.get_neighborhood(port.pos, False):
                x, y = neighbor
                if self.grid[x][y]["Land"] is None:
                    G.add_edge(port.pos, neighbor)
        
        # Now do the pathfinding:
        for start_name, start_port in self.ports.items():
            for end_name, end_port in self.ports.items():
                if (start_name == end_name or 
                    (end_name, start_name) in self.sea_lanes): 
                    continue
                try:
                    path = nx.shortest_path(G, start_port.pos, end_port.pos)
                    self.sea_lanes[(start_name, end_name)] = path
                    path = list(path)
                    path.reverse()
                    self.sea_lanes[(end_name, start_name)] = path
                except:
                    print(f"Could not find path between {start_name} and {end_name}")
                
    def step(self):
        # Update the weather
        # Update the wind
        if self.random.random() < 0.25:
            d = self.random.choice([0, 1])
            self.wind[d] = self.random.choice([-1, 0, 1])
        self.random.shuffle(self.weather_cells)
        for cell in self.weather_cells:
            cell.step()
        self.schedule.step()
    
    def log(self, message):
        log_entry = f"{self.schedule.steps}: {message}"
        if self.verbose:
            print(log_entry)
        self._log.append(log_entry)
        
        
        
        
        
        
        