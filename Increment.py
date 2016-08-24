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
ITERATIONS = 100000
INCREMENT_MIN = 0
INCREMENT_MAX = 0.32
MAX_TARGETS = 3

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
    iteratedTicks[ticksSinceShard] = np.zeros(((MAX_TARGETS,) * ticksSinceShard) + (2,))
  
  if isSuccess:
    iteratedTicks[ticksSinceShard][tuple(targetHistory)][1] += 1
  else:
    iteratedTicks[ticksSinceShard][tuple(targetHistory)][0] += 1

for i in range(1, ITERATIONS+1):
  if i % 10000 == 0:
    print("Iteration %d" % i)
    
    # Debug
    import gc
    gc.collect()  # don't care about stuff that would be garbage collected properly
    #import objgraph
    #objgraph.show_most_common_types()

    summarytracker.print_diff()
    
    #summary.print_(summary.summarize(muppy.get_objects()))
    
    #refbrowser.InteractiveBrowser(iteratedTicks).main()
    #raw_input("Press Enter to continue...")
    
    #print(asizeof(iteratedTicks))
  
  currentTargets = randint(1, MAX_TARGETS)
  addToTargetHistory(currentTargets)
  accumulator += uniform(INCREMENT_MIN, INCREMENT_MAX) / sqrt(currentTargets)
  ticksSinceShard += 1
  
  if accumulator > 1:
    addTickResult(True)
    ticksSinceShard = 0
    targetHistory = np.array([])
    accumulator -= 1
  else:
    addTickResult(False)

# Debug
#print(iteratedTicks)

# Save results
with open("iterationresult.pickle", "w") as file:
  pickle.dump(iteratedTicks, file)