"""Compare fresh-pool end-to-end timing with prewarmed-pool batch timing.

No third-party packages. Original benchmark.py and results.csv are never edited.
Run with the same Python executable used for the original experiment.
"""
import argparse
import csv
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import statistics
import sys
import sysconfig
import threading
import time
import uuid

WORKERS = (1, 2, 4, 8, 16)
ITERATIONS = (1000, 10000, 100000)
REPEATS = 9
TASKS = 128
SEED = 2026


def calculate(number, iterations):
    return hashlib.pbkdf2_hmac(
        'sha256', f'password{number}'.encode(), b'research_salt', iterations
    )


def make_schedule(smoke=False):
    levels = (1000,) if smoke else ITERATIONS
    workers = (1, 2) if smoke else WORKERS
    repeats = 1 if smoke else REPEATS
    pairs = [(i, w, r) for r in range(1, repeats + 1)
             for i in levels for w in workers]
    rng = random.Random(SEED)
    rng.shuffle(pairs)
    schedule = []
    for i, w, r in pairs:
        order = ['fresh', 'prewarmed']
        rng.shuffle(order)
        schedule.append((i, w, r, order))
    return schedule


def batch(pool, iterations):
    # Keep task preparation inside the timed map, as in the original script.
    return list(pool.map(lambda n: calculate(n, iterations), range(TASKS)))


def measure(mode, workers, iterations):
    if mode == 'fresh':
        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=workers) as pool:
            result = batch(pool, iterations)
        elapsed = time.perf_counter() - start
    elif mode == 'prewarmed':
        with ThreadPoolExecutor(max_workers=workers) as pool:
            # Force all workers to exist before timing; worker creation is lazy.
            gate = threading.Barrier(workers + 1, timeout=60)
            ready = [pool.submit(gate.wait) for _ in range(workers)]
            gate.wait()
            for future in ready:
                future.result()
            batch(pool, 1000)  # Untimed 128-task warm-up on this pool.
            start = time.perf_counter()
            result = batch(pool, iterations)
            elapsed = time.perf_counter() - start
        # Pool shutdown is intentionally outside the measured interval.
    else:
        raise ValueError(f'Unknown mode: {mode}')
    return elapsed, result


def run(output_root, smoke=False):
    expected_hex = ('120fb6cffcf8b32c43e7225256c4f837'
                    'a86548c92ccc35480805987cb70be17b')
    if hashlib.pbkdf2_hmac('sha256', b'password', b'salt', 1).hex() != expected_hex:
        raise RuntimeError('PBKDF2 known-answer test failed')
    schedule = make_schedule(smoke)
    # References are computed outside measured runs, one full batch per workload.
    reference = {i: [calculate(n, i) for n in range(TASKS)]
                 for i in sorted({p[0] for p in schedule})}
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    folder = Path(output_root) / f'{"SMOKE" if smoke else "experiment"}_{stamp}_{uuid.uuid4().hex[:8]}'
    folder.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).read_bytes()
    (folder / 'pool_comparison.py').write_bytes(source)
    meta = {
        'status': 'running', 'smoke_test_only': smoke,
        'started_utc': datetime.now(timezone.utc).isoformat(),
        'python': sys.version, 'executable': sys.executable,
        'implementation': platform.python_implementation(),
        'openssl': __import__('ssl').OPENSSL_VERSION,
        'gil_enabled': getattr(sys, '_is_gil_enabled', lambda: None)(),
        'free_threaded_build': sysconfig.get_config_var('Py_GIL_DISABLED'),
        'pbkdf2_backend': hashlib.pbkdf2_hmac.__module__,
        'os': platform.platform(), 'processor_reported_by_os': platform.processor(),
        'logical_cpus': os.cpu_count(), 'seed': SEED, 'tasks_per_batch': TASKS,
        'expected_pairs': len(schedule), 'expected_measured_runs': len(schedule)*2,
        'known_answer_test': 'PASS', 'script_sha256': hashlib.sha256(source).hexdigest(),
        'timer': vars(time.get_clock_info('perf_counter')),
        'method': 'Globally shuffled configuration/repeat pairs; randomized mode order within each pair.',
        'fresh_timing': 'New executor creation, map/list batch and shutdown included.',
        'prewarmed_timing': 'All workers started using a barrier; 128-task 1000-iteration warm-up; only map/list batch timed. Pool lives for one measurement.',
        'verification': 'All 128 outputs compared to untimed serial references after both members of each pair. Same implementation; not an independent PBKDF2 implementation.',
        'limitations': 'Compares lifecycle plus warm-state strategies; does not isolate pure creation cost. No core affinity, power/frequency control or CPU telemetry. CPU model must be independently confirmed.',
    }
    meta_path = folder / 'metadata.json'
    def save_metadata():
        meta_path.write_text(json.dumps(meta, indent=2), encoding='utf-8')
    save_metadata()
    print(f'Output folder: {folder.resolve()}', flush=True)
    print(f'{len(schedule)} pairs / {len(schedule)*2} measured runs', flush=True)
    print('SMOKE TEST ONLY - not research measurements' if smoke else 'Keep power settings and background activity stable.', flush=True)
    recorded = []
    try:
        # Match the original preliminary warm-up, using separate fresh pools.
        for w in sorted({p[1] for p in schedule}):
            _, results = measure('fresh', w, 1000)
            if results != reference[1000]:
                raise RuntimeError('Initial warm-up validation failed')
        with (folder / 'timings.csv').open('x', newline='', encoding='utf-8') as file:
            fields = ['pair_index', 'iterations', 'workers', 'repeat', 'position',
                      'mode', 'duration_seconds', 'verified']
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            for index, (i, w, repeat, order) in enumerate(schedule, 1):
                pair = []
                for position, mode in enumerate(order, 1):
                    duration, result = measure(mode, w, i)
                    pair.append((position, mode, duration, result))
                # Validation, writing and printing are outside both timed calls.
                for position, mode, duration, result in pair:
                    verified = result == reference[i]
                    row = dict(pair_index=index, iterations=i, workers=w,
                               repeat=repeat, position=position, mode=mode,
                               duration_seconds=format(duration, '.9f'), verified=verified)
                    writer.writerow(row)
                    file.flush()
                    if not verified:
                        raise RuntimeError(f'Output mismatch: pair {index}, {mode}')
                    recorded.append(row)
                print(f'[{index}/{len(schedule)} pairs] iterations={i}, workers={w}, '
                      + ', '.join(f'{mode}={duration:.6f}s' for _, mode, duration, _ in pair), flush=True)
        meta['status'] = 'complete'
        meta['actual_measured_runs'] = len(recorded)
        meta['timings_sha256'] = hashlib.sha256((folder/'timings.csv').read_bytes()).hexdigest()
        print('\nMEDIAN TIMES (milliseconds) - fresh / prewarmed', flush=True)
        for i in sorted({p[0] for p in schedule}):
            for w in sorted({p[1] for p in schedule}):
                times = {mode: statistics.median(float(r['duration_seconds']) for r in recorded
                         if r['iterations']==i and r['workers']==w and r['mode']==mode)*1000
                         for mode in ('fresh','prewarmed')}
                print(f'{i:6} iterations | {w:2} workers | {times["fresh"]:.3f} / {times["prewarmed"]:.3f} ms')
        print(f'\nCOMPLETED: {folder.resolve()}', flush=True)
    except BaseException as exc:
        meta['status'] = 'incomplete'
        meta['error'] = repr(exc)
        meta['recorded_valid_runs'] = len(recorded)
        raise
    finally:
        meta['finished_utc'] = datetime.now(timezone.utc).isoformat()
        save_metadata()
    return folder


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--smoke', action='store_true', help='Four-run operational check; not research data')
    parser.add_argument('--output-dir', type=Path, default=Path(__file__).resolve().parent/'pool_comparison_runs')
    args = parser.parse_args()
    run(args.output_dir, args.smoke)
