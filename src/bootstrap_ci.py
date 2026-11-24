"""Percentile bootstrap intervals for the key comparisons (descriptive, within-session).

Reads the preserved CSV files; collects no new measurements. Standard library only.

Usage (from the repository root):
    python src/bootstrap_ci.py
Defaults read data/original/results.csv and data/session_*/timings.csv.

Intervals describe sampling variability of medians within one session (n = 9 per
condition). They are not tests across sessions and are not corrected for multiple
comparisons. Resampling: 10,000 draws, seed 2026.
"""
import argparse
import csv
import random
import statistics
from pathlib import Path

B = 10_000
SEED = 2026


def pct(v, q):
    v = sorted(v)
    k = (len(v) - 1) * q
    f = int(k)
    c = min(f + 1, len(v) - 1)
    return v[f] + (v[c] - v[f]) * (k - f)


def ci(vals):
    return pct(vals, 0.025), pct(vals, 0.975)


def load(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--original', default='data/original/results.csv')
    ap.add_argument('--runs', default='data')
    a = ap.parse_args()
    rng = random.Random(SEED)
    files = sorted(Path(a.runs).glob('session_*/timings.csv')) or sorted(Path(a.runs).glob('*/timings.csv'))

    print('Prewarming reduction at 1,000 iterations: 100*(1 - median(P)/median(F)), pairs resampled jointly')
    for k, f in enumerate(files, 1):
        rows = load(f)
        for w in (8, 16):
            pairs = {}
            for r in rows:
                if int(r['iterations']) == 1000 and int(r['workers']) == w:
                    pairs.setdefault(r['repeat'], {})[r['mode']] = float(r['duration_seconds']) * 1000
            pr = [(p['fresh'], p['prewarmed']) for p in pairs.values()]
            est = 100 * (1 - statistics.median(x[1] for x in pr) / statistics.median(x[0] for x in pr))
            boot = []
            for _ in range(B):
                s = [rng.choice(pr) for _ in pr]
                boot.append(100 * (1 - statistics.median(x[1] for x in s) / statistics.median(x[0] for x in s)))
            lo, hi = ci(boot)
            print(f'  session {k}, {w:2d} workers: {est:.1f}% (95% CI {lo:.1f} to {hi:.1f})')

    def diff_ci(a8, a16):
        est = statistics.median(a8) - statistics.median(a16)
        boot = [statistics.median([rng.choice(a8) for _ in a8]) - statistics.median([rng.choice(a16) for _ in a16])
                for _ in range(B)]
        return est, ci(boot)

    print('\n100,000 iterations: median(8 workers) - median(16 workers) in ms; groups resampled independently')
    orig = load(a.original)
    g = {w: [float(r['duration_seconds']) * 1000 for r in orig
             if int(r['iterations']) == 100000 and int(r['workers']) == w] for w in (8, 16)}
    est, (lo, hi) = diff_ci(g[8], g[16])
    print(f'  original session: {est:+.1f} ms (95% CI {lo:+.1f} to {hi:+.1f})')
    for k, f in enumerate(files, 1):
        rows = load(f)
        for mode in ('fresh', 'prewarmed'):
            g = {w: [float(r['duration_seconds']) * 1000 for r in rows
                     if int(r['iterations']) == 100000 and int(r['workers']) == w and r['mode'] == mode]
                 for w in (8, 16)}
            est, (lo, hi) = diff_ci(g[8], g[16])
            print(f'  session {k}, {mode:9s}: {est:+.1f} ms (95% CI {lo:+.1f} to {hi:+.1f})')


if __name__ == '__main__':
    main()
