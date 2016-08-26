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
for i in range(1, iteratedTicks.shape[0]):
    key = (i,) + (0,) * (MAX_TICKS - 1)
    result = iteratedTicks[key]    
    total_iterations += result[0] + result[1]
print("Total iterations: %i" % total_iterations)

#=======================================
# Core
#=======================================
def calculate_result(key):
    result = iteratedTicks[key]
    noGain = result[0]
    gain = result[1]
    gainSum = noGain + gain    
    if gainSum > 0:
        chance = gain / gainSum
        if chance > 0:
            return chance

#=======================================
# Fit
#=======================================
def fit_func(x, c, d, e):
    #return c*np.exp(d/x) + e
    return c / (1 + np.exp(d * x)) + e

#=======================================
# Iteration & Plot
#=======================================
plot_range = np.arange(1, MAX_TARGETS, 0.01)
for current_targets in range(1, MAX_TARGETS+1):
    plt.figure()
    legend_handles = []
    for history_targets in range(1, MAX_TICKS):  # Start at 2 ticks since chance is 0 without former ticks anyway
        x = np.array([])
        y = np.array([])
        print("Fitting %i ticks" % history_targets)    
        for targets in itertools.product(range(1, MAX_TARGETS+1), repeat=history_targets):  # Different from Increment.py but ensures that all combinations get used
            # Target factor calculation
            target_factor = reduce(mul, targets)  # Product of all targets
            target_factor = pow(target_factor, 1.0/history_targets)
                    
##            target_factor = reduce(mul, map(sqrt, targets)) / history_targets # Product of all targets
            
            targets += (current_targets,)
            targets += (0,) * (MAX_TICKS - history_targets - 1)
            
##            target_factor = sum(targets) / (1.0 * history_targets)
               
            chance = calculate_result(targets)

            if not chance is None:
                x = np.append(x, target_factor)
                y = np.append(y, chance)
        
        plt.plot(x, y, "+", label=history_targets)
        
        if x.any() and y.any() and x.shape[0] > 2 and y.shape[0] > 2:
            opt, cov = curve_fit(fit_func, x, y, maxfev=100000)
        else:
            opt = [0, 0, 0]
        plt.plot(plot_range, fit_func(plot_range, *opt))
        print(opt)

        legend_handles.append("%i Ticks" % (history_targets))
        legend_handles.append("%i Ticks Fit" % (history_targets))

    plt.title(u"%i Current Targets" % current_targets)
    plt.ylabel(u"Chance")
    plt.xlabel(u"Targets")
    plt.gca().set_ylim([0, 1])
    plt.legend(legend_handles, loc="upper right")
    plt.tight_layout()
plt.show()

#=======================================
# Finishing
#=======================================
print("Finished")
