# -*- coding: utf-8 -*-

# Modules
from math import sqrt
import numpy as np
import itertools
from random import randint
from random import uniform

# Constants
ITERATIONS = 10000
INCREMENT_MIN = 0
INCREMENT_MAX = 0.32
MAX_TARGETS = 4
MAX_ARRAY_DIMENSIONS = 8
FILE_NAME = u"iteratedTicks.npy"

# Load
global iteratedTicks
try:
  iteratedTicks = np.load(FILE_NAME)
except EOFError:
  iteratedTicks = {}
  print("%s is empty" % FILE_NAME)
except IOError:
  iteratedTicks = {}
  print("%s is empty" % FILE_NAME)
  

# Core - Incrementation
def increment_core(iterations=ITERATIONS, targets=None):
  # Variables
  global iteratedTicks
  if targets is None:
    max_ticks = MAX_ARRAY_DIMENSIONS
  else:
    max_ticks = len(targets)
  global ticksSinceShard
  global targetHistory
  global accumulator
  accumulator = uniform(INCREMENT_MIN, INCREMENT_MAX)  # Initial condition
  targetHistory = np.array([])
  ticksSinceShard = 0
  
  def reset_variables():
    global ticksSinceShard
    global targetHistory
    global accumulator
    ticksSinceShard = 0
    targetHistory = np.array([])
    accumulator = uniform(INCREMENT_MIN, INCREMENT_MAX)
  
  def addToTargetHistory(currentTargets):
    global targetHistory
    targetHistory = np.sort(np.append(targetHistory, currentTargets - 1))  # -1 because it's used for indexing

  def addTickResult(isSuccess):
    global iteratedTicks
    if not ticksSinceShard in iteratedTicks:
      try:
        iteratedTicks[ticksSinceShard] = np.zeros(((MAX_TARGETS,) * ticksSinceShard) + (2,))
      except:
        print(MAX_TARGETS)
        print(ticksSinceShard)
        print(((MAX_TARGETS,) * ticksSinceShard) + (2,))
        raise
    
    if isSuccess:
      iteratedTicks[ticksSinceShard][tuple(targetHistory)][1] += 1
    else:
      iteratedTicks[ticksSinceShard][tuple(targetHistory)][0] += 1

  for i in range(1, iterations+1):
    if i % 10000 == 0:
      print("Iteration %d" % i)
    
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
      
  # Save results
  np.save(FILE_NAME, iteratedTicks)
  print("Results saved in %s" % FILE_NAME)

# Calculate randomly
#increment_core()

# Calculate systematically
for ticks in range(MAX_ARRAY_DIMENSIONS+1, 1, -1):
  for targets in itertools.combinations_with_replacement(range(1, MAX_TARGETS+1), ticks):
    print("Iterating", targets)
    increment_core(targets=targets)