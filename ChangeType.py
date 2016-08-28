# -*- coding: utf-8 -*-

#=======================================
# Modules
#=======================================
import numpy as np
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