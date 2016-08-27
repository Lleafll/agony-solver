# -*- coding: utf-8 -*-

#=======================================
# Modules
#=======================================
import itertools
import math
from math import log
from math import sqrt
import matplotlib.pyplot as plt
import numpy as np
from operator import mul
from scipy.optimize import curve_fit
from tkFileDialog import askopenfilename

#=======================================
# Load
#=======================================
# Ask file name
filetypes = [("Numpy Files", "*.npy"), ("All", "*")]
filepath = askopenfilename(filetypes=filetypes)

# Load
iteratedTicks = np.load(filepath)
MAX_TICKS = len(iteratedTicks.shape) - 1
MAX_TARGETS = iteratedTicks.shape[0] - 1
print("%s loaded" % filepath)
total_iterations = 0

#=======================================
# Change dtype of array
#=======================================
iteratedTicks = iteratedTicks.astype(int)

#=======================================
# Saving new array
#=======================================
print("Saving results...")
np.save("Int.npy", iteratedTicks)
print("Results saved to %s" % "Int.npy")