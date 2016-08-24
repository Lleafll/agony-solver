# -*- coding: utf-8 -*-

# Modules
import numpy as np

# Constants
TICKS = 7
TARGET_HISTORY = (1, 1, 1, 1, 1, 1)

# Load
try:
  iteratedTicks = np.load("iteratedTicks.npy")
except EOFError:
  print("is empty")
  exit()

# Processing
print(iteratedTicks)

for k, v in iteratedTicks:
  print(k)

tickresults = iteratedTicks[TICKS][TARGET_HISTORY]

# Debug
print(tickresults)