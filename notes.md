
# Islands rising from the ocean

There are different ways to generate terrain, from Perlin noise to elaborate models that incorporate erosion and weather. Right now I'm going to use a simpler technique: starting from a seed point, randomly pick a neighboring empty point (that is, one that's still 'ocean') and turn it into land. This will serve two purposes: I think it will give me the generative aesthetic effect that I want, and it will let me experiment with Mesa agents that span multiple grid cells.

The first algorithm for choosing new island cells is unacceptably slow; when trying to fill 25% of a 100x100 world with land, it takes upwards of 30 seconds to run. As islands become bigger, more and more cells are interior cells, but they are all checked every time anyway. Since cells never stop being inland, let's label them as such as soon as we discover that they are. 

I'm not doing formal profiling, but this feels like it's running a lot faster (though it's still not instantaneous).

