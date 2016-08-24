# -*- coding: utf-8 -*-

# Modules
from math import sqrt
#import numpy as np
import pickle
from random import randint
from random import uniform

# Constants
ITERATIONS = 5
INCREMENT_MIN = 0
INCREMENT_MAX = 0.32
MAX_TARGETS = 3

# Variables
accumulator = uniform(INCREMENT_MIN, INCREMENT_MAX)  # Initial condition
targetHistory = []
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
  targetHistory.append(currentTargets)
  targetHistory.sort()

def addTickResult(ticksSinceShard, isSuccess):
  if ticksSinceShard in iteratedTicks:
    dict = iteratedTicks[ticksSinceShard]
  else:
    iteratedTicks[ticksSinceShard] = {}
    dict = iteratedTicks[ticksSinceShard]
  
  for targets in targetHistory:
    if targets in dict:
      dict = dict[targets]
    else:
      dict[targets] = {}
      dict = dict[targets]
  
  if isSuccess:
    if "gain" in dict:
      dict["gain"] += 1
    else:
      dict["gain"] = 1
  else:
    if "noGain" in dict:
      dict["noGain"] += 1
    else:
      dict["noGain"] = 1

for i in range(0, ITERATIONS):
  if i % 1000 == 0:
    print("Iteration %d" % i)
    
    # Debug
    import gc
    gc.collect()  # don't care about stuff that would be garbage collected properly
    import objgraph
    objgraph.show_most_common_types()
    #from guppy import hpy
    #hp = hpy()
    #before = hp.heap()

  
  currentTargets = randint(1, MAX_TARGETS)
  addToTargetHistory(currentTargets)
  accumulator += uniform(INCREMENT_MIN, INCREMENT_MAX) / sqrt(currentTargets)
  ticksSinceShard += 1
  
  if accumulator > 1:
    addTickResult(ticksSinceShard, True)
    ticksSinceShard = 0
    targetCount = []
    accumulator -= 1
  else:
    addTickResult(ticksSinceShard, False)

# Debug
print(iteratedTicks) 

# Save results
with open("iterationresult.pickle", "w") as file:
  pickle.dump(iteratedTicks, file)