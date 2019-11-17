from mesa.space import Grid, accept_tuple_argument

class LayeredGrid(Grid):
    ''' Every cell contains a dictionary of layers to contents.
    
    TODO: Implement 'empties' API
    '''
    
    def __init__(self, width, height, torus, layers):
        '''
        
        Args:
            layers: A dictionary mapping layer name to content type,
                    either "Single" or "Multi"
        '''
        self.layers = layers
        super().__init__(width, height, torus)
    
    def default_val(self, layer=None):
        if layer is None:
            return {layer: self.default_val(layer)
                    for layer in self.layers}
        elif layer not in self.layers:
            raise Exception("`layer` must be one of the specified layers")
        else:
            if self.layers[layer] == "Single":
                return None
            if self.layers[layer] == "Multi":
                return set()
    
    def _place_agent(self, pos, agent):
        ''' Place the agent at the given location and layer. '''
        if not hasattr(agent, "layer"):
            raise Exception("Object must have a `layer` property")
        if agent.layer not in self.layers:
            raise Exception("Object must have a valid layer name")
        x, y = pos
        layer = agent.layer
        if self.layers[layer] == "Single":
            if self.grid[x][y][layer] is not None:
                raise Exception("That cell is already occupied")
            else:
                self.grid[x][y][layer] = agent
        if self.layers[layer] == "Multi":
            self.grid[x][y][layer].add(agent)
    
    def _remove_agent(self, pos, agent):
        if not hasattr(agent, "layer"):
            raise Exception("Object must have a `layer` property")
        if agent.layer not in self.layers:
            raise Exception("Object must have a valid layer name")
        x, y = pos
        layer = agent.layer
        if self.layers[layer] == "Single":
            self.grid[x][y][layer] = None
        if self.layers[layer] == "Multi":
            self.grid[x][y][layer].remove(agent)
    
    @accept_tuple_argument
    def iter_cell_list_contents(self, cell_list):
        ''' TODO: Can probably be made more compact. '''
        for x, y in cell_list:
            for layer, layer_type in self.layers.items():
                if layer_type == "Multi":
                    for c in self[x][y][layer]:
                        yield c
                if layer_type == "Single" and self[x][y][layer] is not None:
                    yield self[x][y][layer]
    
        
        