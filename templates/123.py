import os
import multiprocessing

print("CPU cores (os.cpu_count):", os.cpu_count())
print("CPU cores (multiprocessing):", multiprocessing.cpu_count())