# -*- coding: utf-8 -*-

#=======================================
# Modules
#=======================================
from math import sqrt
import numpy as np
import itertools
import os.path as path
from random import randint
from random import uniform

#=======================================
# Constants
#=======================================
ITERATIONS = 10000
RESET_MIN = 0
RESET_MAX = 0.99
INCREMENT_MIN = 0
INCREMENT_MAX = 0.32
MAX_TARGETS = 5
MAX_TICKS = 10
FILE_NAME = u"%i_%i_%.2f_%.2f_%.2f_%.2f_results.npy" % (MAX_TARGETS, MAX_TICKS, RESET_MIN, RESET_MAX, INCREMENT_MIN, INCREMENT_MAX)
IMPORT_FROM_FILE = True

#=======================================
# Load or initialize
#=======================================
global iteratedTicks
def initialize_iteratedTicks():
  global iteratedTicks
  iteratedTicks = np.zeros(((MAX_TARGETS+1,) * MAX_TICKS) + (2,))

if IMPORT_FROM_FILE:
  if path.isfile(FILE_NAME):
    iteratedTicks = np.load(FILE_NAME)
  else:
    raise Exception("Import file not found.") 
else:
  initialize_iteratedTicks()

#=======================================
# Save results
#=======================================
def save_results():
  print("Saving results...")
  np.save(FILE_NAME, iteratedTicks)
  print("Results saved to %s" % FILE_NAME)

#=======================================
# Core - Incrementation
#=======================================
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
  targetHistory = np.zeros(MAX_TICKS)
  ticksSinceShard = 0
  
  def reset_variables():
    global ticksSinceShard
    global targetHistory
    global accumulator
    ticksSinceShard = 0
    targetHistory = np.zeros(MAX_TICKS)
    accumulator = uniform(RESET_MIN, RESET_MAX)
  
  def addToTargetHistory(currentTargets):
    global targetHistory
    global ticksSinceShard
    targetHistory[ticksSinceShard] = currentTargets  # ticksSinceShard is not yet incremented

  def addTickResult(isSuccess):
    global iteratedTicks    
    if isSuccess:
      iteratedTicks[tuple(targetHistory)][1] += 1
    else:
      iteratedTicks[tuple(targetHistory)][0] += 1

  for i in range(1, iterations+1):
    if targets is None:
      currentTargets = randint(1, MAX_TARGETS)
    else:
      currentTargets = targets[ticksSinceShard]  # ticksSinceShard is not yet incremented
    
    addToTargetHistory(currentTargets)
    accumulator += uniform(INCREMENT_MIN, INCREMENT_MAX) / sqrt(currentTargets)
    ticksSinceShard += 1
    
    if accumulator > 1:
      addTickResult(True)
      reset_variables()
    else:
      addTickResult(False)
    
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
        for target_history in itertools.combinations_with_replacement(range(1, MAX_TARGETS+1), tick_count-1):
          for last_target in range(1, MAX_TARGETS+1):
            total_combinations_with_replacement += 1
      
      combinations_iterator = 1
      for tick_count in range(1, MAX_TICKS+1):
        for target_history in itertools.combinations_with_replacement(range(1, MAX_TARGETS+1), tick_count-1):
          for last_target in range(1, MAX_TARGETS+1):
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
        for target_history in itertools.combinations_with_replacement(range(1, MAX_TARGETS+1), tick_count-1):
          for last_target in range(1, MAX_TARGETS+1):
              targets = target_history + (last_target,)
              iteratedTick = iteratedTicks[targets + (0,) * (MAX_TICKS - tick_count)]
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
def fill_permuted_incrementation(iteration_aim):
  try:
    iteration_needed = True
    while iteration_needed:
      iteration_needed = False
      for tick_count in range(MAX_TICKS, 0, -1):
        print("Filling %i ticks" % tick_count)
        for target_history in itertools.product(range(1, MAX_TARGETS+1), repeat=tick_count-1):
          for last_target in range(1, MAX_TARGETS+1):
              targets = target_history + (last_target,)
              iteratedTick = iteratedTicks[targets + (0,) * (MAX_TICKS - tick_count)]
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
fill_permuted_incrementation(1000)
