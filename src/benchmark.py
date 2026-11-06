
import hashlib

assert hashlib.pbkdf2_hmac(
    "sha256", b"password", b"salt", 1
).hex() == (
    "120fb6cffcf8b32c43e7225256c4f837"
    "a86548c92ccc35480805987cb70be17b"
)

print("PBKDF2 verification: PASS")
import csv
import hashlib
import random
import statistics
import time
from concurrent.futures import ThreadPoolExecutor

WORKERS = [1, 2, 4, 8, 16]
ITERATIONS = [1000, 10000, 100000]
REPEATS = 9
TASKS = 128

def calculate(number, iterations):
    return hashlib.pbkdf2_hmac(
        "sha256",
        f"password{number}".encode(),
        b"research_salt",
        iterations
    )

def benchmark(workers, iterations):
    start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(
            lambda n: calculate(n, iterations),
            range(TASKS)
        ))

    elapsed = time.perf_counter() - start

    assert len(results) == TASKS
    assert all(len(result) == 32 for result in results)
    return elapsed

# Warm-up
print("Warming up...")
for workers in WORKERS:
    benchmark(workers, 1000)

# Randomized experiment order
experiments = [
    (iterations, workers, repeat)
    for repeat in range(1, REPEATS + 1)
    for iterations in ITERATIONS
    for workers in WORKERS
]

random.seed(2026)
random.shuffle(experiments)

results = []

with open("results.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow([
        "iterations", "workers", "repeat",
        "duration_seconds"
    ])

    for index, (iterations, workers, repeat) in enumerate(
        experiments, start=1
    ):
        duration = benchmark(workers, iterations)

        writer.writerow([
            iterations, workers, repeat,
            round(duration, 6)
        ])
        file.flush()

        results.append((iterations, workers, duration))

        print(
            f"[{index}/{len(experiments)}] "
            f"Iterations={iterations}, "
            f"Workers={workers}, "
            f"Time={duration:.4f}s",
            flush=True
        )

print("\nMEDIAN RESULTS")
print("-" * 45)

for iterations in ITERATIONS:
    for workers in WORKERS:
        times = [
            duration
            for i, w, duration in results
            if i == iterations and w == workers
        ]

        print(
            f"{iterations:6} iterations | "
            f"{workers:2} workers | "
            f"Median: {statistics.median(times):.4f}s"
        )

print("\nExperiment completed. Saved to results.csv")
