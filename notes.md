
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


