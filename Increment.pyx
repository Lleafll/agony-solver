# -*- coding: utf-8 -*-
# cython: profile=False

#==============================================================================
#  Modules
#==============================================================================
cimport cython
import configparser
import itertools
from libc.stdlib cimport RAND_MAX
import os.path as path
import pickle

#==============================================================================
#  Load settings
#==============================================================================
Config = configparser.ConfigParser()
Config.read("settings.ini")
cdef:
    int ITERATIONS = Config.getint("Iteration Settings", "ITERATIONS")
    int ITERATION_AIM = Config.getint("Iteration Settings", "ITERATION_AIM")
    float CHANCE_LIMIT = Config.getfloat("Iteration Settings", "CHANCE_LIMIT")
    float RESET_MIN = 0
    float RESET_MAX = Config.getfloat("Iteration Settings", "RESET_MAX")
    float INCREMENT_MIN = 0
    float INCREMENT_MAX = Config.getfloat("Iteration Settings", "INCREMENT_MAX")
    int MIN_TARGETS = Config.getint("Iteration Settings", "MIN_TARGETS")
    int MAX_TARGETS = Config.getint("Iteration Settings", "MAX_TARGETS")
    int MAX_TICKS = Config.getint("Iteration Settings", "MAX_TICKS")
    int PRINT_OUTPUT_EVERY = Config.getint("Iteration Settings", "PRINT_OUTPUT_EVERY")
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
cdef dict iteratedTicks
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

cdef void add_tick_result(int* failure, int* success, int currentMax, tuple targetHistory, tuple currentTargets):
    global iteratedTicks
    cdef int targetIndex
    
    for targetIndex in range(0, currentMax):
        key = targetHistory + (currentTargets[targetIndex],)
        gainList = get_gain_list_from_iteratedTicks(key)        
        gainList[0] += failure[targetIndex]
        gainList[1] += success[targetIndex]

cdef:
    float squareRootsFactorHistory[100]  # Used to store pre-calculated square roots, indices corresponding to indices in targets tuple
    float squareRootsFactorCurrent[100]
@cython.cdivision(True)
cdef inline void pre_calculate_square_roots_factors(float* factorArray, tuple targets):
    cdef int target
    cdef int targetIndex = 0
    for target in targets:
        factorArray[targetIndex] = INCREMENT_MAX / RAND_MAX / target**0.5
        targetIndex += 1

cdef int g_seed = 36
@cython.profile(False)
cdef inline int fast_rand():  # http://stackoverflow.com/questions/1640258/need-a-fast-random-generator-for-c
    global g_seed
    g_seed = (214013 * g_seed + 2531011)
    return (g_seed >> 16) & 0x7FFF

cdef float rngResetFactor = RESET_MAX / RAND_MAX
@cython.profile(False)
@cython.cdivision(True)
cdef inline float rng_reset():
    return fast_rand() * rngResetFactor

@cython.profile(False)
cdef inline float rng_increment_history(int targetIndex):
    return fast_rand() * squareRootsFactorHistory[targetIndex]

@cython.profile(False)
cdef inline float rng_increment_current(int targetIndex):
    return fast_rand() * squareRootsFactorCurrent[targetIndex]    

cdef void accumulate_core(int* failure, int* success, int historyMax, int currentMax, int iterations):
    cdef:
        float accumulator
        float accumulatorCurrent
        int iterationCounter
        int currentTargets
        int targetIndex
    
    for iterationCounter in range(0, iterations):
        accumulator = rng_reset()
        
        for targetIndex in range(0, historyMax):
            accumulator += rng_increment_history(targetIndex)
            if accumulator > 1:
                break

        if accumulator <= 1:
            for targetIndex in range(0, currentMax):
                accumulatorCurrent = accumulator + rng_increment_current(targetIndex)
                if accumulatorCurrent > 1:
                    success[targetIndex] += 1
                else:
                    failure[targetIndex] += 1

cdef void increment_core(tuple targetHistory, tuple currentTargets, int iterations):
    cdef:
        int historyMax = len(targetHistory)
        int currentMax = len(currentTargets)
        int failure[100]
        int success[100]
        int resultIndex
    
    pre_calculate_square_roots_factors(squareRootsFactorHistory, targetHistory)
    pre_calculate_square_roots_factors(squareRootsFactorCurrent, currentTargets)
    
    for resultIndex in range(0, currentMax):
        failure[resultIndex] = 0
        success[resultIndex] = 0
    
    accumulate_core(failure, success, historyMax, currentMax, iterations)
    add_tick_result(failure, success, currentMax, targetHistory, currentTargets)

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

cdef int iterationsLimit
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
                        currentTargetOutputString = ""
                        minIterationSum = ITERATION_AIM  # float("inf") could be clearer?
                        
                        for lastTarget in range(MIN_TARGETS, MAX_TARGETS+1):
                            try:
                                iteratedTick = get_gain_list_from_iteratedTicks(targetHistory + (lastTarget,))
                                iterationSum = iteratedTick[0] + iteratedTick[1]
                            except KeyError:
                                iterationSum = 0
                            
                            if iterationSum < ITERATION_AIM:
                                currentTargets += (lastTarget,)
                                currentTargetOutputString = "{} ({}:{})".format(currentTargetOutputString, lastTarget, iterationSum)
                            
                            minIterationSum = iterationSum < minIterationSum and iterationSum or minIterationSum
                            
                        if len(currentTargets) > 0:                            
                            minimumIterations = (ITERATION_AIM - minIterationSum) / pathChance * 2
                            iterationsLimit = int(minimumIterations < ITERATIONS and minimumIterations or ITERATIONS)
                            iterationCounterSave += iterationsLimit
                            iterationsTotal += 1
                            furtherIterationsNeeded = True
                            
                            if PRINT_OUTPUT and iterationsTotal >= PRINT_OUTPUT_EVERY:
                                outputString = "{}".format(tuple_to_string(targetHistory))
                                outputString = "{} ({}) ({}) ({} iterations)".format(outputString, pathChance is True and "-" or pathChance, abortIndex and abortIndex or "-", iterationsLimit)
                                print(outputString)
                                print(currentTargetOutputString)
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
