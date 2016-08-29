from Increment import fill_permuted_incrementation

#==============================================================================
# Profiling
#==============================================================================
import cProfile
cProfile.run("fill_permuted_incrementation(1000)", "fill_permuted_incrementation.profile")
import pstats
pstats.Stats("fill_permuted_incrementation.profile").sort_stats("time").strip_dirs().sort_stats("time").print_stats()

#import statprof
#statprof.start()
#try:
#    fill_permuted_incrementation(1000)
#finally:
#    statprof.stop()
#    statprof.display()

#==============================================================================
# Regular Execution
#==============================================================================
#fill_permuted_incrementation(1000)