# CPU Thread Scaling Evidence Package

Author: Mehmet Esad Onel. Single-author student research, 6 November 2026.

## Contents and provenance
- src/benchmark.py: exact recovered original script, including its startup known-answer assertion.
- data/original/results.csv: 135 original measured batches; globally shuffled order, seed 2026.
- src/pool_comparison.py: follow-up script.
- data/session_1/ and data/session_2/: 270 raw measured batches per session, metadata and exact executed source.
- src/analyze.py: regenerate all summary and paired-summary CSVs without new experiments.
- analysis/: generated descriptive summaries. All original observations are retained.
- METHOD_NOTES.txt: exact follow-up design, timing boundaries and limits.
- SOURCE_VERIFICATION.md: checked reference metadata and claim-to-source mapping.
- SHA256SUMS.txt: integrity hashes of package files (excluding this manifest).

## Dependencies
Benchmarking and analysis require CPython and its standard library only; there are no pip dependencies.
Recorded follow-up environment: CPython 3.14.7 64-bit, OpenSSL 3.5.7, GIL enabled, _hashlib backend, Windows 11.
Original machine model was reported as Intel Core i5-12500H. Both follow-ups were reported by the author
as connected to AC power in High performance mode. These power conditions were not instrumentally logged.
The original CSV contains no runtime metadata. Do not retroactively assign follow-up metadata to it.

## Reproduce the analysis (recommended first)
Extract the archive. From its root directory run:
    python src/analyze.py
This reads the included data and writes analysis/summary.csv and analysis/paired_summary.csv.
It does NOT execute benchmarks. Medians and ranges are calculated in milliseconds. Percent reduction is
100*(1 - median_prewarmed/median_fresh), not the median of per-pair percentage changes.
Paired differences are fresh_ms - prewarmed_ms, with pairing by condition and repeat within a session.
Formatting uses Python float formatting to three decimal places; last-digit rounding at exact decimal
halfways can differ from decimal-arithmetic rounding. Raw values are always preserved.

## Collect new measurements (optional; not needed to reproduce the tables)
Use the same interpreter, power mode and hardware, close CPU-heavy background programs and record
conditions and interruptions. Do not run multiple benchmarks concurrently.
Original study: make a NEW empty directory, change into it, and run the absolute path to src/benchmark.py.
The original script writes results.csv in its current directory and WILL overwrite that filename.
Follow-up study, from the extracted package root:
    python src/pool_comparison.py --output-dir new_runs
Each invocation creates a unique folder with 270 measured batches, metadata and an executed-source copy.
For an operational check only: add --smoke (four batches; never use these as research data).

## Checks and known limits
Analyze.py checks original ordering, factorial coverage, nine repeats per cell, positive finite times,
follow-up completion, recorded verification and recorded hashes. The original asserts count and key
length after each timed batch. Follow-up outputs match serial references from the same implementation;
this is not an independent PBKDF2 implementation check. The known-answer test is a separate startup check.
Follow-up sessions share seed 2026 and therefore the same pair/mode schedule. They are separate sessions,
not 18 independently randomized repeats, and are never pooled with the original dataset.
Fresh includes pool creation and shutdown. Prewarmed excludes them and adds an untimed warm-up. It has
one measured batch per pool, so this does not estimate isolated creation overhead or long-term reuse.
No core placement, utilization, temperature, frequency or power telemetry was collected. No significance
tests or confidence intervals are claimed. See the manuscript for interpretation and validity limits.

## Submission and disclosure
ChatGPT/Codex assisted experimental design discussion, follow-up and analysis code, source lookup,
calculations, drafting and formatting. The author ran the experiments and reported operating conditions.
The author must review the manuscript, independently check key sources and calculations, and be able to
defend all claims. No claim of completed independent author verification is made by this package.
Reviewer-accessible evidence repository:
https://github.com/lfl06/cpu-thread-scaling-2026
Use GitHub's Code > Download ZIP to obtain this directory structure, then run src/analyze.py.
The manuscript links to this repository. Local PDF attachments are an additional convenience.
The manuscript contains student identification; it is deliberately excluded from this evidence archive.
Only this code/data package is intended for the public repository; the manuscript is kept separately.
