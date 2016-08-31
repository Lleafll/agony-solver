# -*- coding: utf-8 -*-

#==============================================================================
#  Modules
#==============================================================================
cimport cython
import configparser
import itertools
from libc.stdlib cimport rand, RAND_MAX
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
    int SAVE_EVERY = Config.getint("Iteration Settings", "SAVE_EVERY")
PRINT_OUTPUT = Config.getboolean("Iteration Settings", "PRINT_OUTPUT")
DEBUG = Config.getboolean("Iteration Settings", "DEBUG")

#==============================================================================
#  Constants
#==============================================================================
FILE_NAME = u"%.2f_%.2f_%.2f_%.2f_results.pickle" % (RESET_MIN, RESET_MAX, RESET_MAX, INCREMENT_MAX)

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
cdef void addTickResult(int* failure, int* success, int currentMax, tuple targetHistory, tuple currentTargets):
    global iteratedTicks
    cdef int targetIndex
    
    for targetIndex in range(0, currentMax):
        key = targetHistory + (currentTargets[targetIndex],)
        
        try:
            iteratedTicks[key][0] += failure[targetIndex]
            iteratedTicks[key][1] += success[targetIndex]
        except KeyError:
            iteratedTicks[key] = [0, 0]
            iteratedTicks[key][0] += failure[targetIndex]
            iteratedTicks[key][1] += success[targetIndex]

cdef float rngResetFactor = RESET_MAX / RAND_MAX
@cython.profile(False)
@cython.cdivision(True)
cdef inline float rng_reset():
    return rand() * rngResetFactor

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

@cython.profile(False)
cdef inline float rng_increment_history(int targetIndex):
    return rand() * squareRootsFactorHistory[targetIndex]

@cython.profile(False)
cdef inline float rng_increment_current(int targetIndex):
    return rand() * squareRootsFactorCurrent[targetIndex]    

cdef void accumulate_core(int* failure, int* success, int historyMax, int currentMax):
    cdef:
        float accumulator
        float accumulatorCurrent
        int iterationCounter
        int currentTargets
        int targetIndex
    
    for iterationCounter in range(0, ITERATIONS):
        accumulator = rng_reset()
        
        for targetIndex in range(0, historyMax):
            accumulator += rng_increment_history(targetIndex)
            if accumulator > 1:
                break

        if accumulator <= 1:
            for targetIndex in range(0, currentMax):
                accumulatorCurrent = accumulator + rng_increment_current(targetIndex)
                if accumulator > 1:
                    success[targetIndex] += 1
                else:
                    failure[targetIndex] += 1

cdef void increment_core(tuple targetHistory, tuple currentTargets):
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
    
    accumulate_core(failure, success, historyMax, currentMax)
    addTickResult(failure, success, currentMax, targetHistory, currentTargets)

#==============================================================================
#  Wrappers
#==============================================================================
def tuple_to_string(tpl):
    return " ".join("{:>2d}".format(i) for i in tpl)

def calculate_path_chance(targetHistory):
    pathChance = 1
    
    for targetsSliceIndex in range(1, len(targetHistory)+1):
        try:
            tick = iteratedTicks[targetHistory[:targetsSliceIndex]]
            failure = tick[0]
            success = tick[1]
            iterations = failure + success
            if iterations < ITERATION_AIM:
                return True, targetsSliceIndex
            else:
                pathChance *= failure / iterations
                if pathChance < CHANCE_LIMIT:
                    #print("Skipping path {} (less than {} chance to reach)".format(tuple_to_string(targetHistory), pathChance))
                    return False, None
        except KeyError:
            return True, None
    
    return pathChance, targetsSliceIndex

cdef tuple targets
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
                    pathChance, targetsSliceIndex = calculate_path_chance(targetHistory)
                    
                    if pathChance:
                        currentTargets = () 
                        currentTargetOutputString = ""                       
                        
                        for lastTarget in range(MIN_TARGETS, MAX_TARGETS+1):
                            targets = targetHistory + (lastTarget,)
                            
                            try:
                                iteratedTick = iteratedTicks[targets]
                                iterationSum = iteratedTick[0] + iteratedTick[1]
                            except KeyError:
                                iterationSum = 0
                            
                            if iterationSum < ITERATION_AIM:
                                currentTargets += (lastTarget,)
                                currentTargetOutputString = "{} ({}:{})".format(currentTargetOutputString, lastTarget, iterationSum)
                        
                        if len(currentTargets) > 0:
                            iterationCounterSave += ITERATIONS
                            iterationsTotal += 1
                            
                            if PRINT_OUTPUT and iterationsTotal >= PRINT_OUTPUT_EVERY:
                                outputString = "{}".format(tuple_to_string(targetHistory))
                                outputString = "{} ({}) ({})".format(outputString, pathChance is True and "-" or pathChance, targetsSliceIndex and targetsSliceIndex or "")
                                print(outputString)
                                print(currentTargetOutputString)
                                iterationsTotal = 0
                            
                            increment_core(targetHistory, currentTargets)
                            
                            furtherIterationsNeeded = True
                            
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

# Only calculate 
def fill_same():
    def combination_same(tickCounter):
        tickCounter -= 1
        for base in range(MIN_TARGETS, MAX_TARGETS+1):
            yield (base,) * tickCounter

    incrementation_base(combination_same)