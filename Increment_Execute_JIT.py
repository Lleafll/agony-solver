import pyximport
pyximport.install()

from Increment import fill_permuted, fill_same, fill_permuted_small

fill_permuted_small()

#import cProfile
#cProfile.run("fill_same()", "fill_same.profile")
#import pstats
#pstats.Stats("fill_same.profile").sort_stats("time").strip_dirs().sort_stats("time").print_stats()
