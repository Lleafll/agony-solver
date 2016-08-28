# -*- coding: utf-8 -*-

#=======================================
# Modules
#=======================================
import ConfigParser
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
FILE_NAME = u"%i_%i_%i_%.2f_%.2f_%.2f_%.2f_results.npy" % (MIN_TARGETS, MAX_TARGETS, MAX_TICKS, RESET_MIN, RESET_MAX, INCREMENT_MIN, INCREMENT_MAX)

#=======================================
# Load or initialize
#=======================================
global iteratedTicks
def initialize_iteratedTicks():
  global iteratedTicks
  iteratedTicks = np.zeros(((MAX_TARGETS-MIN_TARGETS+2,) * MAX_TICKS) + (2,), dtype=np.int)

if path.isfile(FILE_NAME):
  iteratedTicks = np.load(FILE_NAME)
else:
  print("Import file not found.")
  initialize_iteratedTicks()

#=======================================
# Save results
#=======================================
def save_results():
  print("Saving results...")
  np.save(FILE_NAME, iteratedTicks)
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
target_history_tuple_to_key_memo = {}
def target_history_tuple_to_key(target_history, max_ticks):
    memo_key = (target_history, max_ticks)
    if memo_key in target_history_tuple_to_key_memo:
        return target_history_tuple_to_key_memo[memo_key]
    else:
        key = tuple(i - MIN_TARGETS + 1 for i in target_history)
        key += (max_ticks - len(target_history)) * (0,)
        target_history_tuple_to_key_memo[memo_key] = key
        return key

def addTickResult(key, isSuccess):
  global iteratedTicks
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
      addTickResult(target_history_tuple_to_key(targetHistory, max_ticks), True)
      reset_variables()
    else:
      addTickResult(target_history_tuple_to_key(targetHistory, max_ticks), False)

    # Limit calculation depth
    if ticksSinceShard == max_ticks:
      reset_variables()


#=======================================
# Wrappers
#=======================================
# Calculate randomly
def random_incrementation():
  increment_core()

# Calculate systematically
def permuted_incrementation():
  try:
    while True:

      # Just mirroring real loop, LAZY AF
      total_combinations_with_replacement = 0
      for tick_count in range(1, MAX_TICKS+1):
        for target_history in itertools.combinations_with_replacement(range(MIN_TARGETS, MAX_TARGETS+1), tick_count-1):
          for last_target in range(MIN_TARGETS, MAX_TARGETS+1):
            total_combinations_with_replacement += 1

      combinations_iterator = 1
      for tick_count in range(1, MAX_TICKS+1):
        for target_history in itertools.combinations_with_replacement(range(MIN_TARGETS, MAX_TARGETS+1), tick_count-1):
          for last_target in range(MIN_TARGETS, MAX_TARGETS+1):
            targets = target_history + (last_target,)
            print("Iterating %s (%i/%i)" % (" ".join(str(i) for i in targets), combinations_iterator, total_combinations_with_replacement))
            increment_core(targets=targets)
            combinations_iterator += 1
        save_results()

  except KeyboardInterrupt:
    print("\nInterrupted\n")
    save_results()

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
              iteratedTick = iteratedTicks[target_history_tuple_to_key(targets, MAX_TICKS)]
              iteration_sum = iteratedTick[0] + iteratedTick[1]
              if iteration_sum < iteration_aim:
                iteration_needed = True
                print("Iterating %s (currently %i iterations)" % (" ".join(str(i) for i in targets), iteration_sum))
                increment_core(targets=targets)
      save_results()
  except KeyboardInterrupt:
      print("\nInterrupted, saving results...\n")
      save_results()

# Fill all holes, necessary when there are non-permuted values in numpy array
# Only fills values where there are iterations already
def fill_all_incrementation(iteration_aim):
  try:
    iteration_needed = True
    while iteration_needed:
      iteration_needed = False
      for tick_count in range(MAX_TICKS, 0, -1):
        print("Filling %i ticks" % tick_count)
        for target_history in itertools.product(range(MIN_TARGETS, MAX_TARGETS+1), repeat=tick_count-1):
          for last_target in range(MIN_TARGETS, MAX_TARGETS+1):
              targets = target_history + (last_target,)
              iteratedTick = iteratedTicks[target_history_tuple_to_key(targets, MAX_TICKS)]
              iteration_sum = iteratedTick[0] + iteratedTick[1]
              if iteration_sum > 0 and iteration_sum < iteration_aim:
                iteration_needed = True
                print("Iterating %s (currently %i iterations)" % (" ".join(str(i) for i in targets), iteration_sum))
                increment_core(targets=targets)
      save_results()
  except KeyboardInterrupt:
      print("\nInterrupted, saving results...\n")
      save_results()


#=======================================
# Execution
#=======================================
fill_permuted_incrementation(10000)

#=======================================
# Profiling
#=======================================
#import cProfile
#cProfile.run("fill_permuted_incrementation(10000)", "fill_permuted_incrementation.profile")
#import pstats
#stats = pstats.Stats("fill_permuted_incrementation.profile")
#stats.strip_dirs().sort_stats("time").print_stats()
