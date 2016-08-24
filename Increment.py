# -*- coding: utf-8 -*-

# Modules
from math import sqrt
import numpy as np
import itertools
import json
import cPickle as pickle
from random import randint
from random import uniform

# Debug
from pympler.asizeof import asizeof
from pympler import muppy
from pympler import refbrowser
from pympler import summary
from pympler import tracker

# Debug
summarytracker = tracker.SummaryTracker()

# Constants
ITERATIONS = 10000
INCREMENT_MIN = 0
INCREMENT_MAX = 0.32
MAX_TARGETS = 5
MAX_ARRAY_DIMENSIONS = 10

# Load
#global totalIterations
with open("iterationresult.pickle", "r") as file:
  try:
    iteratedTicks = pickle.load(file)
  except EOFError:
    iteratedTicks = {}
    #totalIterations = 0
    print("iterationresult.pickle is empty")

# Core - Incrementation
def increment_core(iterations=ITERATIONS, targets=None):
  # Variables
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
    np.append(targetHistory, currentTargets - 1)  # -1 because it's used for indexing
    np.sort(targetHistory)

  def addTickResult(isSuccess):
    if not ticksSinceShard in iteratedTicks:
      try:
        iteratedTicks[ticksSinceShard] = np.zeros(((MAX_TARGETS,) * ticksSinceShard) + (2,))
      except:
        print(MAX_TARGETS)
        print(ticksSinceShard)
        print(((MAX_TARGETS,) * ticksSinceShard) + (2,))
        raise MemoryError
    
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
      # Debug
      #print(ticksSinceShard)
      
      reset_variables()
  
  #global totalIterations
  #totalIterations += iterations
  #print("Total iterations: %d" % totalIterations)
      
  # Save results
  with open("iterationresult.pickle", "w") as file:
    pickle.dump(iteratedTicks, file)
  print("Results saved in iterationresult.pickle")

# Calculate randomly
#increment_core()

# Calculate systematically
for ticks in range(1, MAX_ARRAY_DIMENSIONS+1):
  for targets in itertools.combinations_with_replacement(range(1, MAX_TARGETS+1), ticks):
    print("Iterating", targets)
    increment_core(targets=targets)