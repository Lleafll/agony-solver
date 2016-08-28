# -*- coding: utf-8 -*-

#=======================================
# Modules
#=======================================
import ConfigParser
import cPickle
from math import sqrt
import numpy as np
import itertools
import os.path as path
from random import randint
from random import uniform

#=======================================
# Load settings
#=======================================
Config = ConfigParser.ConfigParser()
Config.read("settings.ini")
ITERATIONS = Config.getint("Iteration Settings", "ITERATIONS")
RESET_MIN = Config.getfloat("Iteration Settings", "RESET_MIN")
RESET_MAX = Config.getfloat("Iteration Settings", "RESET_MAX")
INCREMENT_MIN = Config.getfloat("Iteration Settings", "INCREMENT_MIN")
INCREMENT_MAX = Config.getfloat("Iteration Settings", "INCREMENT_MAX")
MIN_TARGETS = Config.getint("Iteration Settings", "MIN_TARGETS")
MAX_TARGETS = Config.getint("Iteration Settings", "MAX_TARGETS")
MAX_TICKS = Config.getint("Iteration Settings", "MAX_TICKS")

#=======================================
# Constants
#=======================================
FILE_NAME = u"%i_%i_%i_%.2f_%.2f_%.2f_%.2f_results.pickle" % (MIN_TARGETS, MAX_TARGETS, MAX_TICKS, RESET_MIN, RESET_MAX, INCREMENT_MIN, INCREMENT_MAX)

#=======================================
# Load or initialize
#=======================================
global iteratedTicks
def initialize_iteratedTicks():
  global iteratedTicks
  iteratedTicks = {}

if path.isfile(FILE_NAME):
    try:
        with open(FILE_NAME, "rb") as f:
            iteratedTicks = cPickle.load(f)
    except EOFError:
        print("File is empty")
        initialize_iteratedTicks()
else:
    print("Import file not found.")
    initialize_iteratedTicks()

#=======================================
# Save results
#=======================================
def save_results():
    print("Saving results...")
    with open(FILE_NAME, "wb") as f:
        cPickle.dump(iteratedTicks, f)
    print("Results saved to %s" % FILE_NAME)
        

#=======================================
# Memoization
#=======================================
def memodict(f):  # Currently not used
    """ Memoization decorator for a function taking a single argument """
    class memodict(dict):
        def __missing__(self, key):
            ret = self[key] = f(key)
            return ret 
    return memodict().__getitem__

#=======================================
# Core - Incrementation
#=======================================
def addTickResult(key, isSuccess):
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

def increment_core(iterations=ITERATIONS, targets=None):
  # Variables
  global iteratedTicks
  if targets is None:
    max_ticks = MAX_TICKS
  else:
    max_ticks = len(targets)
  global ticksSinceShard
  global targetHistory
  global accumulator
  accumulator = uniform(RESET_MIN, RESET_MAX)  # Initial condition
  targetHistory = ()
  ticksSinceShard = 0

  def reset_variables():
    global ticksSinceShard
    global targetHistory
    global accumulator
    ticksSinceShard = 0
    targetHistory = ()
    accumulator = uniform(RESET_MIN, RESET_MAX)

  def addToTargetHistory(currentTargets):
    global targetHistory
    global ticksSinceShard
    targetHistory += (currentTargets,)  # ticksSinceShard is not yet incremented

  for i in range(1, iterations+1):
    if targets is None:
      currentTargets = randint(MIN_TARGETS, MAX_TARGETS)
    else:
      currentTargets = targets[ticksSinceShard]  # ticksSinceShard is not yet incremented

    addToTargetHistory(currentTargets)
    accumulator += uniform(INCREMENT_MIN, INCREMENT_MAX) / sqrt(currentTargets)
    ticksSinceShard += 1

    if accumulator > 1:
      addTickResult(targetHistory, True)
      reset_variables()
    else:
      addTickResult(targetHistory, False)

    # Limit calculation depth
    if ticksSinceShard == max_ticks:
      reset_variables()


#=======================================
# Wrappers
#=======================================
# Calculate randomly
#def random_incrementation():
#  increment_core()

## Calculate systematically
#def permuted_incrementation():
#  try:
#    while True:
#
#      # Just mirroring real loop, LAZY AF
#      total_combinations_with_replacement = 0
#      for tick_count in range(1, MAX_TICKS+1):
#        for target_history in itertools.combinations_with_replacement(range(MIN_TARGETS, MAX_TARGETS+1), tick_count-1):
#          for last_target in range(MIN_TARGETS, MAX_TARGETS+1):
#            total_combinations_with_replacement += 1
#
#      combinations_iterator = 1
#      for tick_count in range(1, MAX_TICKS+1):
#        for target_history in itertools.combinations_with_replacement(range(MIN_TARGETS, MAX_TARGETS+1), tick_count-1):
#          for last_target in range(MIN_TARGETS, MAX_TARGETS+1):
#            targets = target_history + (last_target,)
#            print("Iterating %s (%i/%i)" % (" ".join(str(i) for i in targets), combinations_iterator, total_combinations_with_replacement))
#            increment_core(targets=targets)
#            combinations_iterator += 1
#        save_results()
#
#  except KeyboardInterrupt:
#    print("\nInterrupted\n")
#    save_results()

# Fill holes in permuted values
def fill_permuted_incrementation(iteration_aim):
    try:
        iteration_needed = True
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
                            print("Iterating %s (currently %i iterations)" % (" ".join(str(i) for i in targets), iteration_sum))
                            increment_core(targets=targets)
            save_results()
    except KeyboardInterrupt:
        print("\nInterrupted, saving results...\n")
        save_results()

## Fill all holes, necessary when there are non-permuted values in numpy array
## Only fills values where there are iterations already
#def fill_all_incrementation(iteration_aim):
#  try:
#    iteration_needed = True
#    while iteration_needed:
#      iteration_needed = False
#      for tick_count in range(MAX_TICKS, 0, -1):
#        print("Filling %i ticks" % tick_count)
#        for target_history in itertools.product(range(MIN_TARGETS, MAX_TARGETS+1), repeat=tick_count-1):
#          for last_target in range(MIN_TARGETS, MAX_TARGETS+1):
#              targets = target_history + (last_target,)
#              iteratedTick = iteratedTicks[target_history_tuple_to_key(targets, MAX_TICKS)]
#              iteration_sum = iteratedTick[0] + iteratedTick[1]
#              if iteration_sum > 0 and iteration_sum < iteration_aim:
#                iteration_needed = True
#                print("Iterating %s (currently %i iterations)" % (" ".join(str(i) for i in targets), iteration_sum))
#                increment_core(targets=targets)
#      save_results()
#  except KeyboardInterrupt:
#      print("\nInterrupted, saving results...\n")
#      save_results()


#=======================================
# Execution
#=======================================
fill_permuted_incrementation(1)

#=======================================
# Profiling
#=======================================
#import cProfile
#cProfile.run("fill_permuted_incrementation(10000)", "fill_permuted_incrementation.profile")
#import pstats
#stats = pstats.Stats("fill_permuted_incrementation.profile")
#stats.strip_dirs().sort_stats("time").print_stats()
