# -*- coding: utf-8 -*-

#=======================================
# Modules
#=======================================
import configparser
import itertools
from libc.stdlib cimport rand, RAND_MAX
import os.path as path
import pickle
import cProfile
from cpython cimport bool
from random import uniform

#=======================================
# Load settings
#=======================================
Config = configparser.ConfigParser()
Config.read("settings.ini")
cdef:
    unsigned int ITERATIONS = Config.getint("Iteration Settings", "ITERATIONS")
    float RESET_MIN = Config.getfloat("Iteration Settings", "RESET_MIN")
    float RESET_MAX = Config.getfloat("Iteration Settings", "RESET_MAX")
    float INCREMENT_MIN = Config.getfloat("Iteration Settings", "INCREMENT_MIN")
    float INCREMENT_MAX = Config.getfloat("Iteration Settings", "INCREMENT_MAX")
    unsigned int MIN_TARGETS = Config.getint("Iteration Settings", "MIN_TARGETS")
    unsigned int MAX_TARGETS = Config.getint("Iteration Settings", "MAX_TARGETS")
    unsigned int MAX_TICKS = Config.getint("Iteration Settings", "MAX_TICKS")
    bool PRINT_OUTPUT = Config.getboolean("Iteration Settings", "PRINT_OUTPUT")
    bool DEBUG = Config.getboolean("Iteration Settings", "DEBUG")

#=======================================
# Constants
#=======================================
FILE_NAME = u"%i_%i_%i_%.2f_%.2f_%.2f_%.2f_results.pickle" % (MIN_TARGETS, MAX_TARGETS, MAX_TICKS, RESET_MIN, RESET_MAX, INCREMENT_MIN, INCREMENT_MAX)

#=======================================
# Load or initialize
#=======================================
cdef dict iteratedTicks
def initialize_iteratedTicks():
  global iteratedTicks
  iteratedTicks = {}

if not DEBUG and path.isfile(FILE_NAME):
    try:
        with open(FILE_NAME, "rb") as f:
            iteratedTicks = pickle.load(f)
    except EOFError:
        print("File is empty")
        initialize_iteratedTicks()
else:
    print("Import file not found.")
    initialize_iteratedTicks()

#=======================================
# Save results
#=======================================
cdef void save_results():
    if DEBUG:
        return
    print("Saving results...")
    with open(FILE_NAME, "wb") as f:
        pickle.dump(iteratedTicks, f)
    print("Results saved to %s" % FILE_NAME)

#=======================================
# Core - Incrementation
#=======================================
cdef void addTickResult(tuple key, bool isSuccess):
  global iteratedTicks
  try:
      if isSuccess:
        iteratedTicks[key][1] += 1
      else:
        iteratedTicks[key][0] += 1
  except KeyError:
      iteratedTicks[key] = [0, 0]
      if isSuccess:
        iteratedTicks[key][1] += 1
      else:
        iteratedTicks[key][0] += 1

cdef:
    int ticksSinceShard
    tuple targetHistory
    float accumulator

cdef void reset_variables():
    global ticksSinceShard
    global targetHistory
    global accumulator
    ticksSinceShard = 0
    targetHistory = ()
    accumulator = rand() / (RAND_MAX * RESET_MAX) - RESET_MIN

cdef float rng_increment():
    return rand() * INCREMENT_MAX / RAND_MAX - INCREMENT_MIN

cdef void increment_core(tuple targets, unsigned int max_iterations):
    # Variables
    global iteratedTicks  
    global ticksSinceShard
    global targetHistory
    global accumulator
    
    cdef unsigned int iteration_counter = 0
    cdef unsigned int currentTargets
    while iteration_counter < max_iterations:
        reset_variables()
        for currentTargets in targets:
            iteration_counter += 1
            
            targetHistory += (currentTargets,)
            accumulator += rng_increment()
            ticksSinceShard += 1
        
            if accumulator > 1:
                addTickResult(targetHistory, True)
                reset_variables()
                break
            else:
                addTickResult(targetHistory, False)

#=======================================
# Wrappers
#=======================================
# Fill holes in permuted values
#pr = cProfile.Profile()
cdef tuple targets
def fill_permuted_incrementation(iteration_aim):
    try:
        iteration_needed = True
        iterations_total = 0
        while iteration_needed:
            iteration_needed = False
            for tick_count in range(MAX_TICKS, 0, -1):
                print("Filling %i ticks" % tick_count)
                for target_history in itertools.combinations_with_replacement(range(MIN_TARGETS, MAX_TARGETS+1), tick_count-1):
                    for last_target in range(MIN_TARGETS, MAX_TARGETS+1):
                        targets = target_history + (last_target,)
                        try:
                            iteratedTick = iteratedTicks[targets]
                            iteration_sum = iteratedTick[0] + iteratedTick[1]
                        except KeyError:
                            iteration_sum = 0
                        if iteration_sum < iteration_aim:
                            iteration_needed = True
                            increment_core(targets, ITERATIONS)
                            iterations_total += ITERATIONS
                            if iterations_total > 10000000 and PRINT_OUTPUT:
                                print("Iterating %s (currently %i iterations)" % (" ".join(str(i) for i in targets), iteration_sum))
                                iterations_total = 0

            save_results()
    except KeyboardInterrupt:
        print("\nInterrupted, saving results...\n")
        save_results()

#=======================================
# Execution
#=======================================
#fill_permuted_incrementation(100)

#=======================================
# Profiling
#=======================================
#cProfile.run("fill_permuted_incrementation(1000)", "fill_permuted_incrementation.profile")
#import pstats
#import StringIO
#s = StringIO.StringIO()
#ps = pstats.Stats("fill_permuted_incrementation.profile", stream=s).sort_stats("time").strip_dirs().sort_stats("time").print_stats()
#print s.getvalue()
