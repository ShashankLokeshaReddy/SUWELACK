import concurrent.futures
import time

def worker(index):
    """Function that each thread will run."""
    print(f"Worker {index} is running.")

if __name__ == "__main__":
    num_threads = 30
    start_time = time.time()
    # Create a ThreadPoolExecutor with the desired number of threads.
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        # Submit tasks to the executor (in this case, the worker function).
        futures = [executor.submit(worker, i) for i in range(num_threads)]

        # Wait for all tasks to complete.
        concurrent.futures.wait(futures)

    end_time = time.time()
    print(f"All {num_threads} threads have finished.")
    print(f"Time Exe", end_time - start_time)