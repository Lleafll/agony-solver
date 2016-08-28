# -*- coding: utf-8 -*-

#=======================================
# Modules
#=======================================
import itertools
import matplotlib.pyplot as plt
import numpy as np
from operator import mul
from scipy.optimize import curve_fit
from tkFileDialog import askopenfilename
import Tkinter

#=======================================
# Settings
#=======================================
OUTPUT_AS_LUA_TABLE = True

#=======================================
# Load
#=======================================
# Ask file name
filetypes = [("Numpy Files", "*.npy"), ("All", "*")]
filepath = askopenfilename(filetypes=filetypes)

# Load
iteratedTicks = np.load(filepath)
MAX_TICKS = iteratedTicks.ndim - 1
MAX_TARGETS = iteratedTicks.shape[0] - 1
print("%s loaded" % filepath)
total_iterations = 0
for i in range(1, iteratedTicks.shape[0]):
    key = (i,) + (0,) * (MAX_TICKS - 1)
    result = iteratedTicks[key]
    total_iterations += result[0] + result[1]
print("Total iterations: %i" % total_iterations)
root = Tkinter.Tk()
root.withdraw()

#=======================================
# Core
#=======================================
def calculate_result(key):
    result = iteratedTicks[key]
    noGain = result[0]
    gain = result[1]
    gainSum = noGain + gain    
    if gainSum > 0:        
        chance = 1.0*gain / gainSum
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
CONDENSE_INTERVAL = 0.05
def condense_arrays(x, y):
    x_condensed = np.array([])
    y_condensed = np.array([])    
    
    x_chunk = np.array([])
    y_chunk = np.array([])
    condenseStart = None
    for index in range(0, x.size):
        condenseStart = condenseStart or x[index]
        if x[index] - condenseStart > CONDENSE_INTERVAL:
            x_condensed = np.append(x_condensed, np.average(x_chunk))
            y_condensed = np.append(y_condensed, np.average(y_chunk))
            x_chunk = np.array([])
            y_chunk = np.array([])
            condenseStart = None
        else:
            x_chunk = np.append(x_chunk, x[index])
            y_chunk = np.append(y_chunk, y[index])
    
    return x_condensed, y_condensed

def iterate_targets(current_targets, isPlotEnabled):
    opt_return = {}
    
    if isPlotEnabled:
        legend_handles = []
    for history_targets in range(0, MAX_TICKS):
        x = np.array([])
        y = np.array([])
        if not OUTPUT_AS_LUA_TABLE:
            print("Fitting %i ticks" % (history_targets))    
        for targets in itertools.product(range(1, MAX_TARGETS+1), repeat=history_targets):  # Different from Increment.py but ensures that all combinations get used
            # Target factor calculation
            if len(targets) > 0:
                target_factor = reduce(mul, targets)  # Product of all targets
                target_factor = pow(1.0*target_factor, 1.0/history_targets)
            else:
                target_factor = 0
            
            targets += (current_targets,)
            targets += (0,) * (MAX_TICKS - history_targets - 1)
               
            chance = calculate_result(targets)
            
            if not chance is None:
                x = np.append(x, target_factor)
                y = np.append(y, chance)
        
        x, y = condense_arrays(x, y)
        
        if x.any() and y.any() and x.shape[0] > 2 and y.shape[0] > 2:
            opt, cov = curve_fit(fit_func, x, y, maxfev=100000)
            opt_return[history_targets] = opt
            if isPlotEnabled:
                plt.plot(x, y, "+", label=history_targets, clip_on=False)
                plt.plot(plot_range, fit_func(plot_range, *opt))        
                legend_handles.append("%i Ticks" % (history_targets))
                legend_handles.append("%i Ticks Fit. c=%f, d=%f, e=%f" % (history_targets, opt[0], opt[1], opt[2]))
        else:
            opt = None
        
        if OUTPUT_AS_LUA_TABLE:
            if opt == None:
                print("  [%i] = {0, 0, 0}," % (history_targets))
            else:
                print("  [%i] = {%f, %f, %f}," % (history_targets, opt[0], opt[1], opt[2]))
            
    return opt_return, legend_handles

plot_range = np.arange(1, MAX_TARGETS, 0.01)
opt_results = {}
for current_targets in range(1, MAX_TARGETS+1):
    if OUTPUT_AS_LUA_TABLE:
        print("[%i] = {" % current_targets)
    else:
        print("%i current targets" % current_targets)
    opt_results[current_targets] = [{"x":[], "y":[]}, {"x":[], "y":[]}, {"x":[], "y":[]}]
    plt.figure()
    opt, legend_handles = iterate_targets(current_targets, True)
    if opt:
        for i in range(0, len(opt_results[current_targets])):
            for k, v in opt.iteritems():
                opt_results[current_targets][i]["x"].append(k)
                opt_results[current_targets][i]["y"].append(v[i])
        plt.title(u"%i Current Targets" % current_targets)
        plt.ylabel(u"Chance")
        plt.xlabel(u"Targets")
        plt.gca().set_ylim([0, 1])
        #plt.legend(legend_handles, loc="upper right")
        plt.tight_layout()
    if OUTPUT_AS_LUA_TABLE:
        print("},")

##for parameter in range(0, 3):
##    plt.figure()
##    plt.title(u"Parameter %i" % parameter)
##   for current_targets, v in opt_results.iteritems():
##        dict = v[parameter]
##        print(dict)
##        plt.plot(dict["x"], dict["y"], label=current_targets)
##    plt.legend()
##plt.show()

#=======================================
# Finishing
#=======================================
print("Finished")
