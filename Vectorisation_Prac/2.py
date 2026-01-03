import numpy as np
import time

start_time = time.time()
vectorized_sum = np.sum(np.arange(15000))
time_taken = time.time() - start_time
print (f"Vectorized sum:{vectorized_sum}")
print (f"Vectorized sum time taken:{time_taken}")

iter_time = time.time()
iterative_sum = sum(range(15000))
iter_end_time = time.time()-iter_time
print(f"Iterative sum:{iterative_sum}")
print(f"Iterative sum time:{iter_end_time}")