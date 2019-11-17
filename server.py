from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid

from island_model import WorldModel, IslandCell, Person

def get_portrayay(agent):
    if agent is None:
        portrayal = {"Shape": "rect", "w": 1, "h": 1, 
                     "Color": "LightCyan", "Filled": "true", "Layer": 0}
        
    elif type(agent) is IslandCell:
        portrayal = {"Shape": "rect", "w": 0.9, "h": 0.9, 
                     "Color": "Peru", "Filled": "true", "Layer": 0}
    elif type(agent) is Person:
        portrayal = {"Shape": "circle", "r": 0.7, 
                     "Color": "Black", "Filled": "true", "Layer": 2}
    return portrayal

canvas_element = CanvasGrid(get_portrayay, 100, 100, 500, 500)

model_params = {"n_islands": 7,
                "land_fraction": 0.25,
                "n_agents": 100}

server = ModularServer(WorldModel, [canvas_element], "Islands", model_params)
server.port = 8521

if __name__ == "__main__":
    server.launch()