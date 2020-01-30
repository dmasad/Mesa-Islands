# Mesa Islands
### (a very in-progress storyworld)

Most agent-based models are built for research or analysis purposes. Some things that look an awful lot like ABMs are built to be [parts of] games. This model was built for roughly the same reasons as people build model train sets or dollhouses -- it was fun to build and play with, and it might be fun to look at. Additionally, it's intended to be a tech demonstration for the [Mesa ABM library](https://github.com/projectmesa/mesa) which I'm a co-developer of.

Right now, every run of the model generates a random archipelago of islands, with ports on their coasts, and ships that sail between them. It also generates a language model -- either a random collection of weighted syllables, or a Markov model based on English -- which it uses to name the ports and ships. Finally, the model also generates simulated weather, with temperature and humidity giving rise to clouds which are blown around by the wind and pour down rain. 

There are lots more features I'd like to implement, including sailors and other simulated people to sail the ships and populate the ports, goods for the ships to carry and trade, having the weather actually affect the ships' voyages, and more. Getting stories out of these also requires curation, which is not implemented either. If you want to add those features here -- or fork the model and modify it yourself -- feel free!

The basic idea of an island-heavy storyworld (and the term *storyworld* itself) comes from [James Ryan's](https://www.jamesryan.world/) dissertation, [Curating Simulated Storyworlds](https://www.researchgate.net/publication/330855103_Curating_Simulated_Storyworlds). The weather model is almost entirely based on Nick McDonald's [procedural weather patterns](https://weigert.vsos.ethz.ch/2018/07/10/procedural-weather-patterns/) blog post.

## How to Run

Make sure you have the latest version of Mesa installed:

```
pip install -e git+https://github.com/projectmesa/mesa
```
The language model also uses [PyTracery](https://github.com/aparrish/pytracery).

Then run `server.py`.

(Online version coming soon)

You can also run the notebook *Testing.ipynb* which runs the simulation headlessly and generates some static visualizations for debugging purposes.

## Files and submodels

#### island_model.py

Implements the main simulation class, `WorldModel` and the main geographic classes. This is also where the island placement is done, and other submodels and agents are instantiated.

#### sailing_model.py

Implements the `Ship` and `Port` classes. `Port`s don't do anything right now, but `Ship` objects are Mesa agents which choose destinations at random, follow a path to sail to them, and keep a log of their location and current weather conditions. 

This file also has the `calculate_sea_lanes` function, which builds a NetworkX graph of sea cells and uses it to calculate the shortest paths from port to port, for ships to follow. Calculating shortest-paths once makes pathfinding easier, since ships don't need to do it themselves every iteration or even every voyage. It also means that ships tend to follow the same paths as one another; whether this is a realistic feature or a weird simulation artifact is up to the viewer.

#### language_model.py

Implements two language models, which are used to generate random names for ports, ships, and eventually people. 

`RandomLanguage` compiles all possible two-letter combinations of a vowel and a letter (from 'aa' to 'zy'), then assigns a random weight to each and uses them to generate random words to serve as names. It also has a hard-coded list of titles and virtues, which are used to generate ship names. 

`MarkovLanguage` uses a Markov chain (specifically, the `MarkovChain` class) to generate a fake language that looks like some corpus. Specifically, I use a corpus of English towns and cities to create place-names, and a corpus of English-language names to generate person and ship names.

#### weather_model.py

The weather simulation is its own submodel, with its own execution loop. The weather model consists of air cells, where each world grid cell has a corresponding air cell. Air cells have a temperature, a humidity level, and a wind vector. The weather model also maintains a global wind vector. Each step of the model, the following steps happen:

1. The global wind vector rotates by a random angle
2. The wind in each cell is updated
3. Based on each cell's individual wind vector, its temperature and humidity are conveyed to another cell. Think of this as the air being blown around.
4. Temperature and humidity in each cell are updated based on wind speed and whether the cell is over land or water, and whether it is currently cloudy or raining.
5. Each cell's temperature and humidity are updated based on its neighbors.
6. The cell's state -- clear, cloudy or rain -- is updated based on its current temperature and humidity.

This model is primarily derived from Nick McDonald's [procedural weather patterns](https://weigert.vsos.ethz.ch/2018/07/10/procedural-weather-patterns/) blog post and accompanying code. Unlike that model, this weather model does not incorporate terrain elevation; and this model implements wind on a per-cell basis instead of one global wind vector, to account for the fact that this world is intended to be larger. Finally, the parameters were largely tweaked by trial and error until I got weather that looked about right.

#### layer_grid.py

Implements `LayeredGrid`, an extension to Mesa's `Grid` and `MultiGrid` that's intended to help manage models with many different kinds of agents sharing the same cells. A `LayeredGrid` is defined with multiple layers, each one meant to store one specific type of object. Each cell is a dictionary keyed on layer; that makes it easy to quickly check only one layer of a cell, without needing to iterate through every other object that might also be on the cell.

#### server.py

Implements the visualization function and launches the Mesa server. The main innovation here is that it demonstrates how to implement transpart colors in the Mesa front-end via the `rgb(...)` syntax. 

#### utils.py

Holds a couple small helper functions.

#### notes.md

A running log of notes to myself that I kept during the development of the model. Captures various design decisions, pain-points, iterations, shortcuts, and my thought process in general. I'm not sure how readable or useful it is to anyone else (or even to me at more than a couple days' remove).