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
import cProfile
from random import uniform

#==============================================================================
#  Load settings
#==============================================================================
Config = configparser.ConfigParser()
Config.read("settings.ini")
cdef:
    int ITERATIONS = Config.getint("Iteration Settings", "ITERATIONS")
    float RESET_MIN = Config.getfloat("Iteration Settings", "RESET_MIN")
    float RESET_MAX = Config.getfloat("Iteration Settings", "RESET_MAX")
    float INCREMENT_MIN = Config.getfloat("Iteration Settings", "INCREMENT_MIN")
    float INCREMENT_MAX = Config.getfloat("Iteration Settings", "INCREMENT_MAX")
    int MIN_TARGETS = Config.getint("Iteration Settings", "MIN_TARGETS")
    int MAX_TARGETS = Config.getint("Iteration Settings", "MAX_TARGETS")
    int MAX_TICKS = Config.getint("Iteration Settings", "MAX_TICKS")
    int PRINT_OUTPUT_EVERY = Config.getboolean("Iteration Settings", "PRINT_OUTPUT_EVERY")
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
cdef void addTickResult(tuple key, int isSuccess):
    global iteratedTicks
    try:
        iteratedTicks[key][isSuccess] += 1
    except KeyError:
        iteratedTicks[key] = [0, 0]
        iteratedTicks[key][isSuccess] += 1

@cython.profile(False)
@cython.cdivision(True)
cdef inline float rng_reset():
    return rand() * RESET_MAX / RAND_MAX - RESET_MIN

@cython.profile(False)
@cython.cdivision(True)
cdef inline float rng_increment():
    return rand() * INCREMENT_MAX / RAND_MAX - INCREMENT_MIN
cpdef tuple full_intersection(TypeOfSelf self not None, Ray ray not None)
cdef void increment_core(tuple targets, int iteration_sets):
    cdef float accumulator
    cdef int iteration_counter = 0
    cdef int currentTargets
    cdef int targetIndex
    cdef int targetMax = len(targets)
    for iteration_counter in xrange(0, iteration_sets):
        accumulator = rng_reset()
        for targetIndex in xrange(1, targetMax+1):
            accumulator += rng_increment()
            if accumulator > 1:
                addTickResult(targets[0:targetIndex], 1)
                break
            else:
                addTickResult(targets[0:targetIndex], 0)

#==============================================================================
#  Wrappers
#==============================================================================
# Fill holes in permuted values
cdef tuple targets
def fill_permuted_incrementation(iteration_aim):
    try:
        iteration_needed = True
        iterations_total = 0
        while iteration_needed:
            iteration_needed = False
            for tick_count in range(MAX_TICKS, 0, -1):
                print("Filling %i ticks" % tick_count)
                for target_history in itertools.combinations_with_replacement(range(MIN_TARGETS, MAX_TARGETS+1), tick_count-1):
                    for last_target in range(MIN_TARGETS, MAX_TARGETS+1):
                        targets = target_history + (last_target,)
                        try:
                            iteratedTick = iteratedTicks[targets]
                            iteration_sum = iteratedTick[0] + iteratedTick[1]
                        except KeyError:
                            iteration_sum = 0
                        if iteration_sum < iteration_aim:
                            iteration_needed = True
                            increment_core(targets, ITERATIONS)
                            iterations_total += ITERATIONS
                            if PRINT_OUTPUT and iterations_total > PRINT_OUTPUT_EVERY:
                                print("Iterating %s (currently %i iterations)" % (" ".join(str(i) for i in targets), iteration_sum))
                                iterations_total = 0

            save_results()
    except KeyboardInterrupt:
        print("\nInterrupted, saving results...\n")
        save_results()