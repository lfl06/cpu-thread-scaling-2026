"""Exploratory analysis for Section 4.4 and Figure 1 (post hoc, descriptive only).

Reads the preserved CSV files; collects no new measurements.

Usage (from the repository root):
    python src/regime_analysis.py
Defaults read data/original/results.csv and data/session_*/timings.csv and write
analysis/figure1_regimes.png/.pdf. Other locations can be given with
--original, --runs and --out.

Numbers are printed with the standard library only. Figure 1 requires matplotlib
(optional; not needed for the printed numbers).
"""
import argparse
import csv
import statistics
from pathlib import Path

SPLIT = 119  # last original batch before the visible shift (chosen by inspection; post hoc)


def load_original(path):
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        for idx, r in enumerate(csv.DictReader(f), 1):
            rows.append(dict(idx=idx, it=int(r['iterations']), w=int(r['workers']),
                             ms=float(r['duration_seconds']) * 1000))
    return rows


def load_followups(folder):
    sessions = []
    for k, f in enumerate(sorted(Path(folder).glob('session_*/timings.csv')) or sorted(Path(folder).glob('*/timings.csv')), 1):
        with open(f, newline='', encoding='utf-8') as fh:
            rows = [dict(session=k, it=int(r['iterations']), w=int(r['workers']),
                         mode=r['mode'], ms=float(r['duration_seconds']) * 1000)
                    for r in csv.DictReader(fh)]
        sessions.append(rows)
    return sessions


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--original', default='data/original/results.csv')
    ap.add_argument('--runs', default='data')
    ap.add_argument('--out', default='analysis')
    a = ap.parse_args()
    orig = load_original(a.original)
    fups = load_followups(a.runs)
    cells = sorted({(r['it'], r['w']) for r in orig})
    ref = {c: statistics.median(r['ms'] for r in orig if r['idx'] <= SPLIT and (r['it'], r['w']) == c)
           for c in cells}
    for r in orig:
        r['ratio'] = r['ms'] / ref[(r['it'], r['w'])]
    early = [r['ratio'] for r in orig if r['idx'] <= SPLIT]
    tail = [r['ratio'] for r in orig if r['idx'] > SPLIT]
    print(f'Original batches 1-{SPLIT}: ratio to own cell median, median {statistics.median(early):.3f}, '
          f'IQR {statistics.quantiles(early, n=4)[0]:.3f}-{statistics.quantiles(early, n=4)[2]:.3f}')
    print(f'Original batches {SPLIT + 1}-{len(orig)} (n={len(tail)}): median ratio {statistics.median(tail):.3f}, '
          f'range {min(tail):.3f}-{max(tail):.3f}; all > 1: {all(t > 1 for t in tail)}')
    for s in fups:
        rr = [r['ms'] / ref[(r['it'], r['w'])] for r in s]
        print(f'Follow-up session {s[0]["session"]}: median ratio to original batches 1-{SPLIT} '
              f'= {statistics.median(rr):.3f} (n={len(rr)})')
    print('\n100,000 iterations, all sessions, sorted batch times (ms):')
    allrows = [dict(r, session=0) for r in orig] + [r for s in fups for r in s]
    for w in (1, 8, 16):
        v = sorted(r['ms'] for r in allrows if r['it'] == 100000 and r['w'] == w)
        gaps = [(v[i + 1] - v[i], v[i], v[i + 1]) for i in range(len(v) - 1)]
        g = max(gaps)
        print(f'  {w:2d} workers n={len(v)}: min {v[0]:.1f}, max {v[-1]:.1f}; '
              f'largest gap {g[0]:.1f} ms between {g[1]:.1f} and {g[2]:.1f}; '
              f'below gap {sum(x <= g[1] for x in v)}, above gap {sum(x >= g[2] for x in v)}')
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print('\nmatplotlib not installed; figure skipped.')
        return
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False})
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 3.7), gridspec_kw={'width_ratios': [1.35, 1]})
    colors = {1000: '#7FB3C8', 10000: '#2E7D9A', 100000: '#0B2545'}
    for it in (1000, 10000, 100000):
        xs = [r['idx'] for r in orig if r['it'] == it]
        ys = [r['ratio'] for r in orig if r['it'] == it]
        ax1.scatter(xs, ys, s=18, color=colors[it], label=f'{it:,} it.', zorder=3, linewidths=0)
    ax1.axvline(SPLIT + 0.5, color='#C0504D', lw=0.9, ls='--')
    ax1.axhline(1, color='#888', lw=0.6)
    ax1.set_yscale('log')
    ax1.set_yticks([0.8, 1, 1.5, 2, 2.5])
    ax1.set_yticklabels(['0.8', '1.0', '1.5', '2.0', '2.5'])
    ax1.minorticks_off()
    ax1.set_xlabel('Measurement order in original session')
    ax1.set_ylabel(f'Time / cell median of batches 1–{SPLIT}')
    ax1.set_title('(a) Original session: shift after batch 119', loc='left', fontsize=10.5)
    ax1.legend(frameon=False, fontsize=9, loc='upper left')
    labels = ['Original', 'Follow-up 1', 'Follow-up 2']
    for j, w in enumerate((8, 16)):
        for k in range(3):
            v = [r['ms'] for r in allrows if r['it'] == 100000 and r['w'] == w and r['session'] == k]
            x0 = j * 4 + k
            jit = [x0 + ((i * 37) % 11 - 5) * 0.035 for i in range(len(v))]
            ax2.scatter(jit, v, s=18, color=['#0B2545', '#2E7D9A', '#7FB3C8'][k],
                        label=labels[k] if j == 0 else None, zorder=3, linewidths=0)
    ax2.set_xticks([1, 5])
    ax2.set_xticklabels(['8 workers', '16 workers'])
    ax2.set_ylabel('Batch time (ms), 100,000 iterations')
    ax2.set_ylim(200, 660)
    ax2.set_title('(b) Two clusters at 16 workers', loc='left', fontsize=10.5)
    ax2.legend(frameon=False, fontsize=9, loc='upper left', ncol=1, handletextpad=0.2)
    fig.tight_layout()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / 'figure1_regimes.png', dpi=300)
    fig.savefig(out / 'figure1_regimes.pdf')
    print(f'\nWrote {out / "figure1_regimes.png"} and {out / "figure1_regimes.pdf"}')


if __name__ == '__main__':
    main()
