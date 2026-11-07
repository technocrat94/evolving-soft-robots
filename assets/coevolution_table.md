| Condition | Environment | Distance (m), mean ± SD | Success (%), mean ± SD | Cells, mean | Actuators, mean |
|---|---|---:|---:|---:|---:|
| coevo_sine | all | 11.785 ± 4.009 | 98.41 ± 2.46 | 19.83 | 14.00 |
| coevo_sine | flat | 13.181 ± 3.970 | 100.00 ± 0.00 | 19.83 | 14.00 |
| coevo_sine | rough | 12.028 ± 4.134 | 98.33 ± 4.08 | 19.83 | 14.00 |
| coevo_sine | push | 11.401 ± 3.947 | 98.33 ± 4.08 | 19.83 | 14.00 |
| coevo_feedback | all | 10.193 ± 1.054 | 99.21 ± 1.94 | 18.17 | 12.00 |
| coevo_feedback | flat | 12.210 ± 1.474 | 100.00 ± 0.00 | 18.17 | 12.00 |
| coevo_feedback | rough | 10.024 ± 1.637 | 98.33 ± 4.08 | 18.17 | 12.00 |
| coevo_feedback | push | 10.161 ± 1.271 | 100.00 ± 0.00 | 18.17 | 12.00 |

Exact paired two-sided sign-flip tests (feedback − sine; 6 seed pairs, 64 sign patterns):

| Metric | Mean paired difference | Exact p | Holm p (2 outcomes) |
|---|---:|---:|---:|
| distance_m | -1.591531 | 0.43750 | 0.87500 |
| success_rate | 0.007937 | 1.00000 | 1.00000 |

Distances include tilt-disqualified episodes as zero; success means no tilt disqualification. SD is across seeds, not across episodes. All = 1 flat + 10 rough + 10 push episodes.

| Condition | Passive held-out raw distance (m), mean ± SD |
|---|---:|
| coevo_sine | 0.018 ± 0.094 |
| coevo_feedback | 0.259 ± 0.370 |
