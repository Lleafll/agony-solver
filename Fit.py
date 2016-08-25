# -*- coding: utf-8 -*-

# Modules
import itertools
import math
from math import log
import matplotlib.pyplot as plt
import numpy as np
from operator import mul
from scipy.optimize import curve_fit
from tkFileDialog import askopenfilename

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

# Core
def calculate_result(key):
    result = iteratedTicks[key]
    noGain = result[0]
    gain = result[1]
    gainSum = noGain + gain
    if gainSum > 0:
        chance = gain / gainSum
        if chance > 0:
            return chance
    else:
        print(key, "noGain + gain == 0")

# Fit
def exp_fit(x, c, d, e, f):
    return c*np.exp(d/x) + e + f*x

# Plot
plot_range = np.arange(1, MAX_TARGETS, 0.01)
plt.figure()
legend_handles = []
for ticks_to_plot in range(1, MAX_TICKS+1):
    x = np.array([])
    y = np.array([])
    print("Iterating %i ticks" % ticks_to_plot)    
    for targets in itertools.combinations_with_replacement(range(1, MAX_TARGETS+1), ticks_to_plot):
        target_factor = reduce(mul, targets)  # Product of all targets
        target_factor = pow(target_factor, 1.0/ticks_to_plot)
        targets += (0,) * (MAX_TICKS - ticks_to_plot)

        chance = calculate_result(targets)
        if not chance is None:
            x = np.append(x, target_factor)
            y = np.append(y, chance)
    
    if x.any() and y.any():
        opt, cov = curve_fit(exp_fit, x, y, maxfev=100000)
    else:
        opt = [0, 0, 0, 0]
    plt.plot(x, y, "+", label=ticks_to_plot)
    plt.plot(plot_range, exp_fit(plot_range, *opt))
    legend_handles.append("%i Ticks, %f, %f" % (ticks_to_plot, opt[0], opt[1]))

    print(opt)
    
plt.ylabel(u"Chance")
plt.xlabel(u"Targets")
plt.gca().set_ylim([0, 1])
plt.legend(legend_handles)
plt.legend(loc="upper right")
plt.tight_layout()
plt.show()

print("Finished")
