from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid

from island_model import WorldModel, IslandCell, Person, Port, Ship, AirCell

def get_portrayal(agent):
    if agent is None:
        portrayal = {"Shape": "rect", "w": 1, "h": 1, 
                     "Color": "LightCyan", "Filled": "true", "Layer": 0}
        
    elif type(agent) is IslandCell:
        portrayal = {"Shape": "rect", "w": 0.9, "h": 0.9, 
                     "Color": "Peru", "Filled": "true", "Layer": 0}
    elif type(agent) is Person:
        portrayal = {"Shape": "circle", "r": 0.7, 
                     "Color": "Black", "Filled": "true", "Layer": 2}
    
    elif type(agent) is Port:
        portrayal = {"Shape": "rect", "w": 0.7, "h": 0.7, 
                     "Color": "MidnightBlue", "Filled": "true", "Layer": 2}
    
    elif type(agent) is Ship:
        portrayal = {"Shape": "circle", "r": 0.7, 
                     "Color": "Red", "Filled": "true", "Layer": 2}
    
    elif type(agent) is AirCell:
        if not agent.cloudy and not agent.raining:
            return
        else:
            if agent.cloudy:
                #color = "LightGray"
                color = "rgba(80, 80, 80, 0.5)"
            if agent.raining:
                color = "DarkSlateGray"
            portrayal = {"Shape": "rect", "w": 0.7, "h": 0.7, 
                     "Color": color, "Filled": "true", "Layer": 2}
    
    return portrayal

canvas_element = CanvasGrid(get_portrayal, 100, 100, 500, 500)

model_params = {"n_islands": 7,
                "land_fraction": 0.25,
                "n_agents": 100}

server = ModularServer(WorldModel, [canvas_element], "Islands", model_params)
server.port = 8521
server.verbose = False

if __name__ == "__main__":
    server.launch()