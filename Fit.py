# -*- coding: utf-8 -*-

# Modules
import matplotlib.pyplot as plt
import numpy as np
from tkFileDialog import askopenfilename

# Constants
TICKS = 7
TARGET_HISTORY = (1, 1, 1, 1, 1, 1)

# Ask file name
filetypes = [("Numpy Files", "*.npy"), ("All", "*")]
filepath = askopenfilename(filetypes=filetypes)

# Load
iteratedTicks = np.load(filepath)
MAX_TICKS = len(iteratedTicks.shape) - 1

# Core
def calculate_result(key):
    result = iteratedTicks[key]
    noGain = result[0]
    gain = result[1]
    gainSum = noGain + gain
    if gainSum > 0:
        chance = gain / gainSum
        print(key, gainSum, chance)
        return chance
    else:
        print(key, "noGain + gain == 0")

# Plot
plt.figure()
legend_handles = []
for ticks_to_plot in range(1, MAX_TICKS+1):
    x = []
    y = []
    for current_tick in range(1, iteratedTicks.shape[0]):
        keys = (current_tick,) * ticks_to_plot
        keys += (0,) * (MAX_TICKS - ticks_to_plot)
        x.append(current_tick)
        y.append(calculate_result(keys))
    plt.plot(x, y, label=ticks_to_plot)
    legend_handles.append(ticks_to_plot)
plt.legend(legend_handles)
plt.legend(loc="upper right")
plt.tight_layout()
plt.show()

print("Finished")
