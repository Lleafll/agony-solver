# -*- coding: utf-8 -*-

# Modules
from math import sqrt
import numpy as np
import itertools
import os.path as path
from random import randint
from random import uniform

# Constants
ITERATIONS = 100000
INCREMENT_MIN = 0
INCREMENT_MAX = 0.32
MAX_TARGETS = 5
MAX_TICKS = 10
FILE_NAME = u"%i_%i_results.npy" % (MAX_TARGETS, MAX_TICKS)
IMPORT_FROM_FILE = True

# Load or initialize
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

# Save results
def save_results():
  np.save(FILE_NAME, iteratedTicks)
  print("Results saved to %s" % FILE_NAME)

# Core - Incrementation
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
  accumulator = uniform(INCREMENT_MIN, INCREMENT_MAX)  # Initial condition
  targetHistory = np.zeros(MAX_TICKS)
  ticksSinceShard = 0
  
  def reset_variables():
    global ticksSinceShard
    global targetHistory
    global accumulator
    ticksSinceShard = 0
    targetHistory = np.zeros(MAX_TICKS)
    accumulator = uniform(INCREMENT_MIN, INCREMENT_MAX)
  
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
    #if i % 100000 == 0:
    #  print("Iteration %d" % i)
    
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

# Calculate randomly
#increment_core()

# Calculate systematically
try:
  for targets in itertools.combinations_with_replacement(range(1, MAX_TARGETS+1), MAX_TICKS):
    print("Iterating %s" % (" ".join(str(i) for i in targets)))
    increment_core(targets=targets)
  save_results()
except KeyboardInterrupt:
  print("\nInterrupted, saving results...\n")
  save_results()
