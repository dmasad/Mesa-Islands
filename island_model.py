from mesa import Model, Agent
from mesa.time import RandomActivation
from mesa.space import MultiGrid

class IslandCell:
    ''' One tile of land.
    '''
    
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
                if grid.is_cell_empty(c):
                    possible_cells.append(c)
                    landlocked = False
            cell.landlocked = landlocked
        next_cell = self.random.choice(possible_cells)
        new_island = IslandCell(next_cell, self)
        self.cells.append(new_island)
        grid.place_agent(new_island, next_cell)


class WorldModel(Model):
    
    def __init__(self, n_islands=1, land_fraction=0.25):
        
        self.schedule = RandomActivation(self)
        
        # Set world parameters
        self.width = 100
        self.height = 100
        self.grid = MultiGrid(self.height, self.width, torus=True)
        
        # Set up islands
        self.n_islands = n_islands
        self.land_fraction = land_fraction
        self.islands = []
    
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
        
        
        
        