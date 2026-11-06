# Upgrade A: multi-seed ablation study

A0: README clone URLs fixed and pushed in commit bbe5597 (Fix clone URL).

A1/A2: 15 runs (three conditions, five seeds each); co_evolution is reused for A1 and A2. Seeds: 42–46. Population 60, generations 40, 5 s per evaluation, all 10 CPU cores. Original 100×60 showcase media and checkpoints are preserved.

| Condition | Final best distance, mean ± sample SD (m) | Seeds |
|---|---:|---:|
| co_evolution | 13.026 ± 4.337 | 5 |
| body_only | 6.981 ± 1.749 | 5 |
| control_only | 13.525 ± 0.241 | 5 |

Values are mean ± sample standard deviation (ddof=1), over five independent seed runs per condition. Plot bands use ±1 sample SD, not confidence intervals.

Total study wall time: **760.718 seconds** (12.679 minutes), including all simulations, 120 preview GIFs, 15 final active/passive audits and aggregation. Independent integrity checks and repeated audits were performed afterward.

## Statistical comparison

Exact paired, two-sided sign-flip tests of mean final-distance differences, with seeds as blocks and Holm adjustment for two planned comparisons. Assumes exchangeable labels within pairs under the null, or independent symmetric paired differences around zero. All 32 sign patterns are enumerated using NumPy.

[
  {
    "comparison": "co_evolution vs body_only",
    "mean_paired_difference_m": 6.0450543297264785,
    "p_value": 0.0625,
    "permutations": 32,
    "method": "exact paired two-sided sign-flip test",
    "holm_adjusted_p_value": 0.125,
    "significant_after_holm": false
  },
  {
    "comparison": "co_evolution vs control_only",
    "mean_paired_difference_m": -0.4989627548466064,
    "p_value": 0.8125,
    "permutations": 32,
    "method": "exact paired two-sided sign-flip test",
    "holm_adjusted_p_value": 0.8125,
    "significant_after_holm": false
  }
]

Neither comparison is significant at alpha=0.05. With only five pairs the smallest attainable raw two-sided p-value is 0.0625, so no significance claim is possible under this planned test. Control-only has the largest observed mean and smallest spread; co-evolution has the best individual (20.768 m), but not the largest mean. A single showcase does not establish general superiority.

Method reference: [SciPy paired permutation-test documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html). SciPy is not a runtime dependency.

## Per-seed final audits

| Condition | Seed | Eligible distance (m) | Passive raw distance (m) | Passive fell | Max active tilt (deg) | Grounded (%) |
|---|---:|---:|---:|---|---:|---:|
| co_evolution | 42 | 11.274723 | 0.011780 | False | 15.866 | 55.52 |
| co_evolution | 43 | 11.312039 | 0.005866 | False | 15.745 | 54.04 |
| co_evolution | 44 | 20.768061 | 0.016220 | False | 14.968 | 71.44 |
| co_evolution | 45 | 10.610449 | 0.005669 | False | 14.512 | 56.40 |
| co_evolution | 46 | 11.167172 | 0.011572 | False | 12.584 | 54.84 |
| body_only | 42 | 6.022497 | 1.146348 | False | 25.322 | 87.56 |
| body_only | 43 | 6.387497 | 0.673003 | False | 24.788 | 97.72 |
| body_only | 44 | 6.524831 | 3.246714 | True | 26.640 | 98.16 |
| body_only | 45 | 5.896223 | 0.456379 | False | 24.434 | 84.16 |
| body_only | 46 | 10.076124 | 0.969558 | False | 24.432 | 79.28 |
| control_only | 42 | 13.677110 | 0.000000 | False | 13.942 | 68.68 |
| control_only | 43 | 13.629753 | 0.000000 | False | 13.548 | 65.08 |
| control_only | 44 | 13.725420 | 0.000000 | False | 13.575 | 70.08 |
| control_only | 45 | 13.133251 | 0.000000 | False | 12.188 | 71.24 |
| control_only | 46 | 13.461725 | 0.000000 | False | 14.276 | 69.76 |

Passive audits are control measurements, not subtracted fitness. Body-only passive drift (0.456–3.247 m) is appreciable. One passive body-only control topples while its actively controlled counterpart passes the tilt rule; its passive value remains raw displacement, not eligible fitness. This limits a simple interpretation of body-only scores as powered movement. No post-hoc exclusions or objective changes were applied.

## Validation

{
  "evaluations": 36000,
  "unstable": 0,
  "tilt_disqualified": 1549,
  "saved_genomes": 600,
  "audits_repeated": 15,
  "all_fixed_genes_verified": true,
  "all_best_histories_monotonic": true,
  "all_frequencies_in_bounds": true,
  "all_tilt_counts_match": true
}

All 15 unit tests passed, including frozen-gene invariants and known exact-test/adjustment cases. Independent audit checked all 36,000 per-candidate rows, all 600 saved best genomes, every generation disqualification count and elite monotonicity, and exactly repeated the final active/passive audit for all 15 runs. Plot was visually inspected. Both READMEs have valid local links. No numerical physics parameters were changed.

## Reproduction

Inside the repository, with its requirements installed:

```sh
python -m unittest -v test_sim test_evolve test_experiments
python experiments.py
python experiments.py --analyze results/experiments/run_20261107_0503
```

Actual study command, from this repository directory:

```sh
PYTHONPATH=../../work/release_deps MPLCONFIGDIR=../../work/matplotlib /Users/mayuhao/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 experiments.py > ../../work/upgrade_a_console.log 2>&1
```

Run data are in results/experiments/run_20261107_0503/ (ignored by Git). Summary outputs are duplicated into that study directory and assets/. File ablation_environment.json records dependency versions and source SHA-256 hashes. All original experiment folders remain intact.
