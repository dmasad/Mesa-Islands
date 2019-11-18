
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







