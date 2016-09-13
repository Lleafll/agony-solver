# -*- coding: utf-8 -*-

#==============================================================================
#  Modules
#==============================================================================
import configparser
import itertools
from math import log10, floor
import numpy as np
import os.path as path
import pickle

#==============================================================================
#  Load settings
#==============================================================================
Config = configparser.ConfigParser()
Config.read("settings.ini")
ITERATIONS = Config.getint("Iteration Settings", "ITERATIONS")
ITERATION_AIM = Config.getint("Iteration Settings", "ITERATION_AIM")
CHANCE_LIMIT = Config.getfloat("Iteration Settings", "CHANCE_LIMIT")
RESET_MIN = 0
RESET_MAX = Config.getfloat("Iteration Settings", "RESET_MAX")
INCREMENT_MIN = 0
INCREMENT_MAX = Config.getfloat("Iteration Settings", "INCREMENT_MAX")
MIN_TARGETS = Config.getint("Iteration Settings", "MIN_TARGETS")
MAX_TARGETS = Config.getint("Iteration Settings", "MAX_TARGETS")
MAX_TICKS = Config.getint("Iteration Settings", "MAX_TICKS")
PRINT_OUTPUT_EVERY = Config.getint("Iteration Settings", "PRINT_OUTPUT_EVERY")
SAVE_EVERY = Config.getint("Iteration Settings", "SAVE_EVERY")
PRINT_OUTPUT = Config.getboolean("Iteration Settings", "PRINT_OUTPUT")
DEBUG = Config.getboolean("Iteration Settings", "DEBUG")

#==============================================================================
#  Constants
#==============================================================================
FILE_NAME = u"%.2f_%.2f_%.2f_%.2f_results.pickle" % (RESET_MIN, RESET_MAX, INCREMENT_MIN, INCREMENT_MAX)

#==============================================================================
#  Load or initialize
#==============================================================================
def initialize_iteratedTicks():
  global iteratedTicks
  iteratedTicks = {}

if not DEBUG and path.isfile(FILE_NAME):
    try:
        with open(FILE_NAME, "rb") as f:
            iteratedTicks = pickle.load(f)
    except EOFError:
        print("File is empty")
        initialize_iteratedTicks()
else:
    print("Import file not found.")
    initialize_iteratedTicks()

#==============================================================================
#  Save results
#==============================================================================
def save_results():
    if DEBUG:
        return
    print("Saving results...")
    
    with open(FILE_NAME, "wb") as f:
        pickle.dump(iteratedTicks, f)
    
    print("Results saved to %s" % FILE_NAME)

#==============================================================================
#  Core - Incrementation
#==============================================================================
def get_gain_list_from_iteratedTicks(key):
    level = iteratedTicks
    for i in key:
        try:
            level = level[i]
        except KeyError:
            
            level[i] = {0 : [0, 0]}
            level = level[i]
    
    return level[0]

def add_tick_result(targetHistory, currentTarget, failure, success):
    global iteratedTicks
    
    key = targetHistory + (currentTarget,)
    gainList = get_gain_list_from_iteratedTicks(key)        
    gainList[0] += failure
    gainList[1] += success

def accumulate_core(targetHistory, currentTargets, iterations):
    depth = 1 + len(targetHistory)
    random_iterations = np.random.random((depth, iterations))
    
    factor_array = np.zeros((depth, 1))
    factor_array[0][0] = RESET_MAX
    dimension = 1
    for target in targetHistory:
        factor_array[dimension][0] = INCREMENT_MAX * target**0.5
        dimension += 1
    
    random_iterations *= factor_array
    
    iterations_history = random_iterations[0]
    dimension = 1
    for target in targetHistory:
        iterations_history += random_iterations[dimension]
        dimension += 1
    
    
    iterations_history = iterations_history[iterations_history <= 1]
    depth = len(currentTargets)
    random_iterations = np.random.random((depth, len(iterations_history)))
    dimension = 0
    factor_array = np.zeros((depth, 1))
    for target in currentTargets:
        factor_array[dimension][0] = INCREMENT_MAX * target**0.5
        dimension += 1
        
    random_iterations *= factor_array
    
    dimension = 0
    for target in currentTargets:
        iteration_target = iterations_history + random_iterations[dimension]
        success = (iteration_target > 1).sum()
        failure = iterations - success
        add_tick_result(targetHistory, target, failure, success)
        dimension += 1

def increment_core(targetHistory, currentTargets, iterations):
    accumulate_core(targetHistory, currentTargets, iterations)

#==============================================================================
#  Wrappers
#==============================================================================
def tuple_to_string(tpl):
    return " ".join("{:>2d}".format(i) for i in tpl)

def calculate_path_chance(targetHistory):
    if len(targetHistory) == 0:
        return 1, None
    
    pathChance = 1
    
    for targetsSliceIndex in range(1, len(targetHistory)+1):
        tick = get_gain_list_from_iteratedTicks(targetHistory[:targetsSliceIndex])
        failure = tick[0]
        success = tick[1]
        iterations = failure + success
        if iterations < ITERATION_AIM:
            return False, targetsSliceIndex
        else:
            pathChance *= failure / iterations
            
            if pathChance < CHANCE_LIMIT:
                #print("Skipping path {} (less than {} chance to reach)".format(tuple_to_string(targetHistory), pathChance))
                return False, None
    
    return pathChance, targetsSliceIndex

# Base function to be used by wrappers
def incrementation_base(iterator):
    try:
        furtherIterationsNeeded = True
        
        while furtherIterationsNeeded:
            iterationsTotal = float("inf")
            furtherIterationsNeeded = False
            iterationCounterSave = 0
            
            for tickCounter in range(MAX_TICKS, 0, -1):
                print("Filling %i ticks" % tickCounter)
                
                for targetHistory in iterator(tickCounter):                    
                    pathChance, abortIndex = calculate_path_chance(targetHistory)
                    
                    if pathChance:
                        currentTargets = () 
                        minIterationSum = ITERATION_AIM  # float("inf") could be clearer?
                        
                        for lastTarget in range(MIN_TARGETS, MAX_TARGETS+1):
                            try:
                                iteratedTick = get_gain_list_from_iteratedTicks(targetHistory + (lastTarget,))
                                iterationSum = iteratedTick[0] + iteratedTick[1]
                            except KeyError:
                                iterationSum = 0
                            
                            if iterationSum < ITERATION_AIM:
                                currentTargets += (lastTarget,)
                            
                            if iterationSum < minIterationSum:
                                minIterationSum = iterationSum
                            
                        if len(currentTargets) > 0:
                            minimumIterations = (ITERATION_AIM - minIterationSum) / pathChance * 2
                            if minimumIterations < ITERATIONS:
                                iterationsLimit = int(minimumIterations)
                            else:
                                iterationsLimit = int(ITERATIONS)
                            
                            iterationCounterSave += iterationsLimit
                            iterationsTotal += 1
                            furtherIterationsNeeded = True
                            
                            if PRINT_OUTPUT and iterationsTotal >= PRINT_OUTPUT_EVERY:
                                outputString = "{}".format(tuple_to_string(targetHistory))
                                outputString = "{} ({}) ({}) ({} iterations | {} done)".format(outputString, pathChance is True and "-" or round(pathChance, -int(floor(log10(abs(CHANCE_LIMIT)))) + 1), abortIndex and abortIndex or "-", iterationsLimit, minIterationSum)
                                print(outputString)
                                iterationsTotal = 0
                            
                            increment_core(targetHistory, currentTargets, iterationsLimit)
                            
                            if iterationCounterSave >= SAVE_EVERY:
                                save_results()
                                iterationCounterSave = 0
                            
            save_results()
            
    except KeyboardInterrupt:
        print("\nInterrupted, saving results...\n")
        save_results()


# Fill holes in permuted values
def fill_permuted():
    def combinations_with_replacement(tickCounter):
        return itertools.combinations_with_replacement(range(MIN_TARGETS, MAX_TARGETS+1), tickCounter-1)
    
    incrementation_base(combinations_with_replacement)

# Only calculate rows of the same number
def fill_same():
    def combination_same(tickCounter):
        tickCounter -= 1
        if tickCounter == 0:
            yield ()
        else:
            for base in range(MIN_TARGETS, MAX_TARGETS+1):
                yield (base,) * tickCounter

    incrementation_base(combination_same)
    
# Calculate small subset of possible combinations
def fill_permuted_small():
    def combinations_with_replacement_small(tickCounter):
        for base in range(MIN_TARGETS, MAX_TARGETS+1):  # Modification of https://docs.python.org/2/library/itertools.html#itertools.combinations_with_replacement
            for tpl in itertools.combinations_with_replacement((MIN_TARGETS, base, MAX_TARGETS), tickCounter-1):
                if not tpl is None:
                    yield tpl
    
    incrementation_base(combinations_with_replacement_small)

#import cProfile
#cProfile.run("fill_permuted_small()", "fill_permuted_small.profile")
#import pstats
#pstats.Stats("fill_permuted_small.profile").sort_stats("time").strip_dirs().sort_stats("time").print_stats()
