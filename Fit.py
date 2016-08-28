# -*- coding: utf-8 -*-

#==============================================================================
# Modules
#==============================================================================
import ConfigParser
import fnmatch
import itertools
import matplotlib.pyplot as plt
import numpy as np
import os
from operator import mul
import pickle
import re
from scipy.optimize import curve_fit
from tkFileDialog import askopenfilename
import Tkinter

#==============================================================================
# Load Setting
#==============================================================================
Config = ConfigParser.ConfigParser()
Config.read("settings.ini")
LOAD_CACHE = Config.getboolean("Fit Settings", "LOAD_CACHE")
SELECT_FILES_MANUALLY = Config.getboolean("Fit Settings", "SELECT_FILES_MANUALLY")
RESET_MIN = Config.getfloat("Fit Settings", "RESET_MIN")
RESET_MAX = Config.getfloat("Fit Settings", "RESET_MAX")
INCREMENT_MIN = Config.getfloat("Fit Settings", "INCREMENT_MIN")
INCREMENT_MAX = Config.getfloat("Fit Settings", "INCREMENT_MAX")
OUTPUT_AS_LUA_TABLE = Config.getboolean("Fit Settings", "OUTPUT_AS_LUA_TABLE")
CACHE_FILE_NAME = Config.get("Fit Settings", "CACHE_FILE_NAME")

#==============================================================================
# Load from multiple files and build array
#==============================================================================
if not LOAD_CACHE:
    # Ask file name
    if SELECT_FILES_MANUALLY:
        filetypes = [("Numpy Files", "*.npy"), ("All", "*")]
        files = [askopenfilename(filetypes=filetypes)]
        root = Tkinter.Tk()
        root.withdraw()
    else:
        pattern = u"*_*_*_%.2f_%.2f_%.2f_%.2f_results.npy" % (RESET_MIN, RESET_MAX, INCREMENT_MIN, INCREMENT_MAX)
        files = fnmatch.filter(os.listdir("."), pattern)
    
    # Build Single Array From All Files
    target_tuple_to_key_memo = {}
    def targetTupleToKey(target_tuple, min_targets, max_targets, max_ticks):
        memo_key = (target_tuple, max_ticks)
        if memo_key in target_tuple_to_key_memo:
            return target_tuple_to_key_memo[memo_key]
        else:
            key = tuple(i - min_targets + 1 for i in target_tuple)
            key += (max_ticks - len(target_tuple)) * (0,)
            target_tuple_to_key_memo[memo_key] = key
            return key
    
    buildTargetFactorMemo = {}
    def buildTargetFactor(targetHistory, tickSinceShard):
        if targetHistory in buildTargetFactorMemo:  # tickSinceShard is only passed to avoid len(targetHistory)
            return buildTargetFactorMemo[targetHistory]
        else:
            if tickSinceShard > 0:
                targetFactor = reduce(mul, targetHistory)  # Product of all targets
                targetFactor = pow(1.0*targetFactor, 1.0/tickSinceShard)
            else:
                targetFactor = 0
            buildTargetFactorMemo[targetHistory] = targetFactor
            return targetFactor 
    
    iteratedData = {}
    def addToIteratedData(nparray, minTargets, maxTargets, maxTicks):
        for tickIndex in range(0, maxTicks):
            for tickTuple in itertools.product(range(minTargets, maxTargets+1), repeat=tickIndex):
                iteratedResult = nparray[targetTupleToKey(tickTuple, minTargets, maxTargets, maxTicks)]
                noGain = iteratedResult[0]
                gain = iteratedResult[1]
                gainSum = noGain + gain
                if gainSum > 0:
                    currentTargets = tickTuple[-1]
                    targetHistory = tickTuple[0:-1]
                    tickSinceShard = len(targetHistory)
                    try:
                        iteratedData_tickSinceShard = iteratedData[tickSinceShard]
                    except KeyError:
                        iteratedData[tickSinceShard] = {}
                        iteratedData_tickSinceShard = iteratedData[tickSinceShard]
                    try:
                        iteratedData_tickSinceShard_currentTargets = iteratedData_tickSinceShard[currentTargets]
                    except KeyError:
                        iteratedData_tickSinceShard[currentTargets] = {}
                        iteratedData_tickSinceShard_currentTargets = iteratedData_tickSinceShard[currentTargets]
                    targetFactor = buildTargetFactor(targetHistory, tickSinceShard)
                    try:
                        iteratedData_tickSinceShard_currentTargets_targetFactor = iteratedData_tickSinceShard_currentTargets[targetFactor]
                    except:
                        iteratedData_tickSinceShard_currentTargets[targetFactor] = [0, 0]
                        iteratedData_tickSinceShard_currentTargets_targetFactor = iteratedData_tickSinceShard_currentTargets[targetFactor]
                    iteratedData_tickSinceShard_currentTargets_targetFactor[0] += noGain
                    iteratedData_tickSinceShard_currentTargets_targetFactor[1] += gain
                    
    for fileName in files:
        nparray = np.load(fileName)
        print("%s loaded" % fileName)
        min_targets_match = re.search("^(\d+)_" , fileName)
        min_targets = int(min_targets_match.group(1))
        max_targets_match = re.search("^\d+_(\d+)_" , fileName)
        max_targets = int(max_targets_match.group(1))
        max_ticks = nparray.ndim - 1
        total_iterations = 0
        for i in range(0, nparray.shape[0]):
            key = (i,) + (0,) * (max_ticks - 1)
            result = nparray[key]
            total_iterations += result[0] + result[1]
        addToIteratedData(nparray, min_targets, max_targets, max_ticks)
        print("%i min targets, %i max targets, %i max ticks, total iterations: %i" % (min_targets, min_targets, max_ticks, total_iterations))
    
    with open(CACHE_FILE_NAME, "wb") as f:
        pickle.dump(iteratedData, f)
    print("Iterated Data saved to %s" % CACHE_FILE_NAME)

#==============================================================================
# Cache
#==============================================================================
if LOAD_CACHE:
    with open(CACHE_FILE_NAME, "rb") as f:
        iteratedData = pickle.load(f)
    print("Loaded iterated data from %s" % CACHE_FILE_NAME)

#==============================================================================
# Fit
#==============================================================================
def fit_func(x, c, d, e):
    #return c*np.exp(d/x) + e
    return c / (1 + np.exp(d * x)) + e

#==============================================================================
# Iteration & Plot
#==============================================================================
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

for ticksSinceShard, currentTargetsDict in iteratedData.iteritems():
    plt.figure()
    legend_handles = []
    for currentTargets, targetFactorDict in currentTargetsDict.iteritems():
        x = np.array([])
        y = np.array([])
        
        for targetFactor, gainList in targetFactorDict.iteritems():
            x = np.append(x, targetFactor)
            y = np.append(y, 1.0 * gainList[1] / (gainList[0] + gainList[1]))
        
        if x.any() and y.any() and x.size > 2 and y.size > 2:
            try:
                opt, cov = curve_fit(fit_func, x, y, maxfev=100000)
            except RuntimeError:
                opt = [0, 0,  0]
            plt.plot(x, y, "o", label=currentTargets, clip_on=False)
            plotRange = np.arange(1, np.amax(x), 0.1)
            plt.plot(plotRange, fit_func(plotRange, *opt))        
            legend_handles.append("%i Targets" % (currentTargets))
            legend_handles.append("%i Targets Fit. c=%f, d=%f, e=%f" % (currentTargets, opt[0], opt[1], opt[2]))


    plt.title(u"%i Ticks since last Shard" % ticksSinceShard)
    plt.ylabel(u"Chance")
    plt.xlabel(u"Target Factor")
    plt.gca().set_ylim([0, 1])
    plt.legend(legend_handles, loc="upper right")
    plt.tight_layout()
