# -*- coding: utf-8 -*-

# Modules
from math import sqrt
import numpy as np
import json
import pickle
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
ITERATIONS = 1000000
INCREMENT_MIN = 0
INCREMENT_MAX = 0.32
MAX_TARGETS = 5
MAX_ARRAY_DIMENSIONS = 11

# Variables
accumulator = uniform(INCREMENT_MIN, INCREMENT_MAX)  # Initial condition
targetHistory = np.array([])
ticksSinceShard = 0

# Load 
with open("iterationresult.pickle", "r") as file:
  try:
    iteratedTicks = pickle.load(file)
  except EOFError:
    iteratedTicks = None
    print("iterationresult.pickle is empty")
if iteratedTicks is None:
  iteratedTicks = {}

# Core - Incrementation
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

for i in range(1, ITERATIONS+1):
  if i % 10000 == 0:
    print("Iteration %d" % i)
  
  currentTargets = randint(1, MAX_TARGETS)
  addToTargetHistory(currentTargets)
  accumulator += uniform(INCREMENT_MIN, INCREMENT_MAX) / sqrt(currentTargets)
  ticksSinceShard += 1
  ticksSinceShard = ticksSinceShard <= MAX_ARRAY_DIMENSIONS and ticksSinceShard or MAX_ARRAY_DIMENSIONS
  
  if accumulator > 1:
    addTickResult(True)
    ticksSinceShard = 0
    targetHistory = np.array([])
    accumulator -= 1
  else:
    addTickResult(False)

# Save results
with open("iterationresult.pickle", "w") as file:
  pickle.dump(iteratedTicks, file)