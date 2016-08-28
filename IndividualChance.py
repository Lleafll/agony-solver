# -*- coding: utf-8 -*-

#=======================================
# Modules
#=======================================
import numpy as np
from tkFileDialog import askopenfilename

#=======================================
# Parameters
#=======================================
TARGET_HISTORY  = 

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
# Core
#=======================================
print