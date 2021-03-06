
# Islands rising from the ocean

There are different ways to generate terrain, from Perlin noise to elaborate models that incorporate erosion and weather. Right now I'm going to use a simpler technique: starting from a seed point, randomly pick a neighboring empty point (that is, one that's still 'ocean') and turn it into land. This will serve two purposes: I think it will give me the generative aesthetic effect that I want, and it will let me experiment with Mesa agents that span multiple grid cells.

The first algorithm for choosing new island cells is unacceptably slow; when trying to fill 25% of a 100x100 world with land, it takes upwards of 30 seconds to run. As islands become bigger, more and more cells are interior cells, but they are all checked every time anyway. Since cells never stop being inland, let's label them as such as soon as we discover that they are. 

I'm not doing formal profiling, but this feels like it's running a lot faster (though it's still not instantaneous).

# Generating a language

I just want an extremely simply speculative name generator. To get this, I first build a list of syllables by brute-forcing every combination of an alphabet letter with a vowel: 'aa', 'ab', 'ba', ... 'zy', 'yz'. Then I assign each syllable a weight drawn from a long-tailed Zipf distribution. I don't actually know the true distribution of syllables across languages, but *words* are approximately Zipf-distributed (as far as I remember) so this seems like a good guess. To make a word / name, the code chooses some number of syllables via a weighted-random draw; with probability 0.5, the final letter is truncated to make sure all words aren't of even length. 

This is an extremely crude method of generating a language that is only barely anchored in any real linguistics at all, but it has the advantage of generating names that (a) are generally legible to someone used to reading English, and (b) look vaguely like the kind of names you'd see in old-timey pulp genre fiction. Three names chosen at random from a generated list are  'Udsir', 'Fives', 'Iguxfa', all of which sound like they'd be right at home in a lesser Conan the Barbarian novel.

# Adding people

The simplest behavior we want from a people agent is to walk to a random adjacent non-water tile. This immediately highlights a problem with the way Mesa implements the MultiGrid class: if a cell is non-empty, it contains a list; to find out if one of those items is of a certain class (for example, a patch-like IslandCell) we need to check each and every item in that list.

For now we can get around this by assuming that water cells will just be empty. This won't work forever, since at some point we might want to have things in the water (e.g. boats). But it's 23:00 and I want to get *something* done, so.

This works! And even renders slowly but not too painfully in Mesa's browser-based front-end.

# Adding ships

I initially assumed that the model should involve people walking around on the islands. But the very existence of islands -- and the fact that the map is mostly sea -- suggests that interesting agents might actually be ships going between islands. Implementing ships also opens up two interesting technical challenges: (a) addressing the cell contents issue discussed above, since ships need to move across cells that are empty, have one or more other ship in them, or land cells which have a port; and (b) pathfinding via A* or similar, since the ships should probably be able to navigate from port to port.

## Building a layered grid

There are [at least] two potential approaches to building a layered grid for Mesa. One of them is to have the LayerGrid be a thin wrapper around several underlying grid objects, one per layer; the other is to have each cell be a dictionary, with each layer being a value. 

I'm going to implement the latter for now, because it seems simpler and more in line with how other grid classes are implemented.

An API question here is whether layers should (a) come automatically from the agent class; (b) be an agent-specified property; (c) be specified by hand by the coder for each operation. For now I'm going to go with (b) since it seems like it provides the flexibility to have multiple classes on the same layer (e.g. wolves and sheep, or merchant ships and pirate ships) but minimizes the chances for random typos present in (c). 

Another Mesa improvement note: since we generally work with `pos` tuples, wouldn't it make sense to allow grids to accept a `grid[pos]` accessor to get to the coordinates directly? 

It needs more (read: any) testing, but for now it seems to work!

## Ship pathfinding

I realized two things: (a) with lots of ships and only a few ports, I don't want to constantly recalculate pathfinding for routes that were already solved, and (b) I don't really actually want to implement A* from scratch. Instead, I'm going to cheat and build a graph of sea tiles, and then use NetworkX to calculate shortest paths. The real question here is whether this network will end up too big, especially with lots and lots of irrelevant nodes. 

Some initial testing suggests this is fast enough, so let's do it.

We'll randomly select `N` (initially 1) shore cell per island to be a port; then build the navigation network to generate shortest paths; the place ships at ports and have them move along those paths each step.

Two things I might implement later on: (a) paths can be discrete knowledge objects that ships (or captains / sailors) can discover and pass along to one another; (b) weight graphs so that ships want to stick closer to land. 

Hitting a problem with the network somehow not being disconnected around the ports. Possible a residual effect of some cells being marked as non-landlocked because their landlockedness didn't get updated in the final round?

(Well, possible, but after way too much time I just forgot an argument in the shortest-path syntax)

## Adding the ships

Now to implement the actual ships. As a first step, we'll just have some ships start at random ports, and choose a new port at random to sail to. A next step after that might be to have a trade model that determines the destinations.

A fun inintentional phenomenon that emerges when all the ships start in port at the same time and leave close together is that they look like they're convoying. 

Last addition for now: name the ports and ships using the language model.

This more or less works. The main aesthetic problem now is that too many randomly-generated names read all together just start to look like gibberish; for example:

    70: Charity Courage departed Giruuntyu for Naaud
    70: President's Wisdom arrived at Vaukij.
    70: Elector's Wisdom departed Ec Noyw for Kievu
    70: Ib Ucygry Glory departed Giruuntyu for Kievu
    70: Naaud Prince arrived at Kievu.

# Weather simulation

Now we're getting into real overkill territory. There's almost certainly a better way to do this, but I'm going to try a simple weather model as an ABM. Agents will be cells of air, blown around by the wind. Each cell will have a temperature and humidity. Temperature goes up over land, and when there are no clouds; humidity goes up over water. Clouds and rain happen with high humidity and low temperature.

The first simulation run with the first draft of weather enabled is Lovecraftian. The world suddenly fills with clouds, then never-ending rain that covers everything.

Turning off humidity gains while rain is actively falling produces oscillation between rain and clouds, but the world is still mostly cloudly.

Time to add temperature and humidity diffusion?

This seems to help, and the rain still does some oscillation things, but the world is still extremely cloudy.

One more tweak to add sooner rather than later: let's have the wind change direction every so often. This doesn't seem to make a huge difference.

Increasing the humidity lost by rain does seem to produce bands of rain that are quite nice, but things are still too cloudy. The main issue is that the clouds are everywhere, not just in nice bands. One possibility is that we just need to raise the threshold for clouds / rain? But this didn't really end up working either.

Another thing that's happening is that the islands are warm enough to keep rain and clouds both away.

If nothing else, we can probably speed up the performance of the weather model by making it psuedo-matrixy. Instead of moving cells around, we can grab a cell via a wind vector and transfer the properties to it. That keeps the ABM architecture, but reduces the need to make 100x100 move calls, with all the weird accompanying artifacts. It's almost certainly the case that wind speeds (and specifically variable wind speeds) are a critical factor missing from the model.

One last experiment: initializing cells with random humidity. This actually produces surprisingly interesting and intricate patterns as the clouds grow, though they still end up everywhere.

Oh no. The models I'm loosely basing this on assume mostly land, but this is mostly ocean. Which means that variable-temperature water might actually be important. Does that mean I'm going to need to model ocean currents?

The updated implementation of the cell model (Without moving cells around, which was a terrible idea born of it being late at night) seems to run much better. This also has the happy side effect of adding per-cell wind direction and speed. Now to add a wind vector field (instead of just a universal wind vector), and adjust temperature for it.

Adding just a static vector field yields interesting and improved weather patterns (including finally more clouds over land). However, after a little while the weather patterns seem to reach an equilibrium and stabilize -- probably a sign of progress, but less interesting visually.

Before we add shifting winds, let's try to adjust the air temperature based on wind speed and see what happens. 

This (plus, and this is probably important, having rainfall reduce humidity by a fraction instead of a constant) produce increasingly nice-looking weather patterns, though they still seem to stabilize. So, finally, it's time to allow the winds to shift.

Random wind shifts do in fact make the weather patterns less stable and look more natural, though cloud cover is still pretty universal.

Even without the front-end, the model is getting into slow territory (minutes to run 100 steps with no frontend).

It looks like the actual distribution of humidity in the air is much more interesting than the distribution of clouds. Simply tweaking the cloud threshold actually seems to improve things a lot. Clouds still move around in great big bands, but at least they don't cover the entire map.

### Refactoring

Taking a brief detour to refactor some of the codebase into a few semi-independent submodels in order to keep things from becoming too messy.

Spinning off the weather model into its own class because it has a lot of moving parts that are largely independent of the rest of the model; weather cells in particular have their own updating logic that's different from that of agents, in that each submodel step requires multiple internal steps executed on each weather cell -- wind, temperature/humidity change, diffusion, and cloudy/raining checks.

Spinning the language model into its own subclass because it should be largely reusable across different models, and we may even want to have multiple languages within one world. It will also make it easier to swap language models (e.g. replace random syllables with a Markov chain trained on real names) without changing the rest of the code, so long as the alternative models implement the same API.

TODO: spin shipping off into its own submodel too.

## Markov chain language models

Markov chains are almost as good as neural nets at generating fake words and phrases that sound almost right, so let's use those to generate some place names. 

Corpora are all from: https://github.com/dariusk/corpora

Some generated place-names:
    Trader
    Lanteld
    Whipston
    Chille
    Ashoroudbackeldhametersilley
    Atton
    Earlestle
    Haxmunwickfasingstley
    Shipton-Thridgwad
    Bare

And some first names:
    Hairetevor
    Mayton
    Jordo
    Mare
    Mathan
    Jalin
    Lillyn
    Brianicaren
    Mark
    Ashlexany

## Modifying the sailing model

Coming back to this after several months. In order to get more interesting sea lanes, I'm trying adding a cost to move from cell to cell. Initially, the cost was just the distance to land for each cell. (Sidebar: it turns out that `get_distance` is only implemented for `ContinuousSpace` so I had to copy that into `LayeredGrid`). That increases setup time substantially, and actually led to less-interesting paths, since now the optimal route from A to C is to follow the route from A to B and then B to C.

Changing the cost to the square-root of distance actually produces some diagonal-ish paths, which are obviously more interesting than nothing but straight lines.

The run-time on this is unacceptably long. Instead of doing the smart thing and profiling, I'm just going to swap in random weights and see how much that matters. Yup, the unnecessarily-repeated distance calculations (which, upon further examination, were being done multiple times for each cell, yikes) were driving the time, but also the randomly-weighted paths look a lot more organic anyway.