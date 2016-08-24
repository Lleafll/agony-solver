# -*- coding: utf-8 -*-

# Modules
import numpy as np
import pickle
from random import random

# Constants
ITERATIONS = 1000000

INCREMENT_MIN = 0
INCREMENT_MAX = 0.32

MAX_TARGETS = 3

# Initial condition
accumulator = random(INCREMENT_MIN, INCREMENT_MAX)

# Variables
targetCount = []
tickCount = 0

# Load 
with open("Result.pickle", "w") as file:
  iteratedTicks = pickle.load(file)

# Core - Incrementation


# Save results
with open("Result.pickle", "w") as file:
  pickle.dump(iteratedTicks, file)