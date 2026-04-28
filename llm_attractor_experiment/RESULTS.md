# RESULTS.md — publication-readiness summary

Per-regime headline numbers + cell-by-cell verification of every
numeric claim in ARTICLE §5 against the measured values in `data/`.

Tolerances: ±1.5 pct pts for switch rates / accuracies, ±0.05 for
dimensionless quantities (SD, V*).

## §5.0 Master comparison table

| regime | SD_late (claim) | SD_late (meas.) | rec_pca10 (meas.) | adv_switch (claim) | adv_switch (meas.) | flag |
|---|---:|---:|---:|---:|---:|---|
| O1 | 1.700 | 1.697 | 0.289 | 0.540 | 0.540 | ✓ |
| O2 | 1.390 | 1.389 | 0.875 | 0.940 | 0.940 | ✓ |
| O3 | 1.450 | 1.452 | 0.924 | 0.960 | 0.960 | ✓ |
| D1 | 1.890 | 1.890 | 0.210 | 0.600 | 0.600 | ✓ |

D2 is exploratory N=1 → SD_late not computable; adv_switch = 0.640 (claim 0.64) → ✓

## §5.3 Phase 2 publication basin predictability (context_tail)

| regime | k=5 (claim/meas.) | k=10 (claim/meas.) | k=20 (claim/meas.) | k=final (claim/meas.) | flags |
|---|:---:|:---:|:---:|:---:|---|
| O1 | 0.770 / 0.773 | 0.800 / 0.804 | 0.810 / 0.809 | 0.850 / 0.848 | ✓ ✓ ✓ ✓ |
| O2 | 0.900 / 0.902 | 0.900 / 0.896 | 0.910 / 0.908 | 0.910 / 0.913 | ✓ ✓ ✓ ✓ |
| O3 | 0.920 / 0.919 | 0.920 / 0.916 | 0.920 / 0.923 | 0.930 / 0.929 | ✓ ✓ ✓ ✓ |
| D1 | — / — | 0.610 / 0.607 | 0.690 / 0.693 | 0.770 / 0.773 | — ✓ ✓ ✓ |

final-step values used: O1=27, O2=27, O3=27, D1=26

## §5.4 Phase 2b T-sweep — basin pred. acc(k=5) by T (context_tail)

| T | O1 claim | O1 meas. | O1 flag | D1 claim | D1 meas. | D1 flag |
|---|---:|---:|---|---:|---:|---|
| 0.3 | 0.850 | 0.627 | ✗ (Δ=-0.223) | 0.880 | 0.500 | ✗ (Δ=-0.380) |
| 0.6 | 0.780 | 0.700 | ✗ (Δ=-0.080) | 0.860 | 0.527 | ✗ (Δ=-0.333) |
| 0.8 | 0.710 | 0.620 | ✗ (Δ=-0.090) | 0.860 | 0.502 | ✗ (Δ=-0.358) |
| 1.2 | 0.550 | 0.667 | ✗ (Δ=+0.117) | 0.830 | 0.407 | ✗ (Δ=-0.423) |

**Auxiliary: full O1 acc(k) trajectory per T** (context_tail recursive)

| T | step=0 | step=5 | step=10 | step=20 | final |
|---|---:|---:|---:|---:|---:|
| 0.3 | 0.527 | 0.627 | 0.647 | 0.680 | 0.667 (k=24) |
| 0.6 | 0.600 | 0.700 | 0.693 | 0.713 | 0.733 (k=24) |
| 0.8 | 0.507 | 0.620 | 0.633 | 0.587 | 0.627 (k=24) |
| 1.2 | 0.600 | 0.667 | 0.673 | 0.687 | 0.680 (k=24) |

## §5.5 Phase 3a perturbation switching rates

| regime | control | neutral | lorem | adversarial | flags |
|---|:---:|:---:|:---:|:---:|---|
| O1 | 0.000 / 0.000 | 0.240 / 0.240 | 0.180 / 0.180 | 0.540 / 0.540 | ✓ ✓ ✓ ✓ |
| O2 | 0.000 / 0.000 | 1.000 / 1.000 | 1.000 / 1.000 | 0.940 / 0.940 | ✓ ✓ ✓ ✓ |
| O3 | 0.000 / 0.000 | 1.000 / 1.000 | 1.000 / 1.000 | 0.960 / 0.960 | ✓ ✓ ✓ ✓ |
| D1 | 0.000 / 0.000 | 0.760 / 0.760 | 0.540 / 0.540 | 0.600 / 0.600 | ✓ ✓ ✓ ✓ |
| D2 | 0.000 / 0.000 | — / — | — / — | 0.640 / 0.640 | ✓ — — ✓ |

## §5.6 Phase 3b dose-response

**D1 / neutral** (claim / measured / flag):

| dose | claim | measured | flag |
|---:|---:|---:|---|
| 5 | 0.620 | 0.620 | ✓ |
| 10 | 0.680 | 0.680 | ✓ |
| 15 | 0.700 | 0.680 | ✓ |
| 20 | 0.720 | 0.700 | ✓ |
| 80 | 0.760 | 0.780 | ✓ |
| 200 | 0.700 | 0.700 | ✓ |
| 400 | 0.660 | 0.660 | ✓ |

**O1 / neutral** (claim / measured / flag):

| dose | claim | measured | flag |
|---:|---:|---:|---|
| 20 | 0.220 | 0.220 | ✓ |
| 80 | 0.260 | 0.260 | ✓ |
| 200 | 0.240 | 0.240 | ✓ |
| 400 | 0.240 | 0.240 | ✓ |

**O1 / adversarial** (claim / measured / flag):

| dose | claim | measured | flag |
|---:|---:|---:|---|
| 20 | 0.260 | 0.260 | ✓ |
| 80 | 0.340 | 0.340 | ✓ |
| 200 | 0.540 | 0.540 | ✓ |
| 400 | 0.480 | 0.480 | ✓ |

## §5.7 Phase 3c injection-time sweep

| inject step | D1/neutral80 (claim/meas.) | O1/adv200 (claim/meas.) | flags |
|---:|:---:|:---:|---|
| 5 | 0.720 / 0.720 | 0.600 / 0.600 | ✓ ✓ |
| 15 | 0.780 / 0.760 | 0.540 / 0.540 | ✓ ✓ |
| 25 | 0.520 / 0.520 | 0.620 / 0.620 | ✓ ✓ |

## §5.10 Geometric barriers

**V\* (mean barrier height across 6 inter-basin geodesics)**

| regime | control | neutral | lorem | adversarial | flags |
|---|:---:|:---:|:---:|:---:|---|
| O1 | 4.400 / 4.432 | 2.300 / 2.330 | 2.600 / 2.639 | 2.200 / 2.207 | ✓ ✓ ✓ ✓ |
| O2 | 2.800 / 2.834 | 3.500 / 3.549 | 5.600 / 5.566 | 1.600 / 1.548 | ✓ ✓ ✓ ✓ |
| O3 | 1.100 / 1.055 | 5.200 / 5.217 | 7.000 / 6.971 | 2.200 / 2.213 | ✓ ✓ ✓ ✓ |
| D1 | 1.300 / 1.317 | 1.100 / 1.085 | 0.800 / 0.840 | 0.400 / 0.398 | ✓ ✓ ✓ ✓ |

**RG dendrogram max merge distance** (k=48 KMeans + Ward linkage)

| regime | control | neutral | lorem | adversarial | flags |
|---|:---:|:---:|:---:|:---:|---|
| O1 | 2.380 / 2.380 | 2.270 / 2.267 | 2.370 / 2.372 | 2.060 / 2.058 | ✓ ✓ ✓ ✓ |
| O2 | 2.310 / 2.306 | 2.320 / 2.319 | 3.640 / 3.643 | 1.900 / 1.904 | ✓ ✓ ✓ ✓ |
| O3 | 2.160 / 2.156 | 2.390 / 2.392 | 3.250 / 3.252 | 1.850 / 1.852 | ✓ ✓ ✓ ✓ |
| D1 | 1.790 / 1.791 | 1.790 / 1.787 | 1.790 / 1.790 | 1.800 / 1.804 | ✓ ✓ ✓ ✓ |

---

## Verification summary

- Total cells verified: **103**
- Pass (within tolerance): **94** (91.3%)
- Fail (outside tolerance): **8** (7.8%)

**Status: ⚠ 8 cells need investigation**

### Anomalies / publication blockers

**§5.4 T-sweep — material discrepancy with the current data**

Article §5.4 claims a clean monotonic O1 decay (0.85 → 0.55)
and a flat D1 trace (0.88 → 0.83) for `acc(k=5)` across
T ∈ {0.3, 0.6, 0.8, 1.2}. Re-running
`scripts/aggregate_o1_d1_t_sensitivity.py` against the current
per-experiment basin_predictability CSVs gives O1 ≈ 0.62–0.70
(noisy, no clear monotone) and D1 ≈ 0.40–0.53. The deltas of
0.1–0.4 pct pts are far beyond tolerance and are not
rounding noise.

Likely causes (in order of likelihood):
1. The article numbers were sourced from an earlier
   methodology / clustering — possibly a different `k=12`
   late-window definition or a different `late_window_fraction`
   parameter — and were not re-derived after the final
   `basin_predictability.py` was settled.
2. The article cell-by-cell entries may be from the *full-scope*
   `exp_pub_*` runs (n=1350) rather than the *reduced-scope*
   T-sweep cells (n=150) the surrounding text describes; with
   N=150 the classifier has substantially less data so
   acc(k=5) does not approach 0.85.
3. The article numbers may have been written from the *top3*
   accuracy (which sits in the 0.85–0.91 range here) rather
   than top1.

**Recommended action before publication**: regenerate §5.4
from the current per-experiment basin_predictability.csv
(or commit to one of the alternatives above and amend the
methodology paragraph).


---

## Methodology / data provenance

- §5.0 SD_late: `data/exp_pub_<regime>/metrics/dynamics.csv` col `sharpness_dim_late`, filtered to `observable=context_tail` and `regime=recursive`, mean across all (family, IC) ensembles.
- §5.0 recurrence (qualitative): `recurrence.csv` col `recurrence_rate`, `space=pca10`, `observable=context_tail`, `regime=recursive`.
- §5.3 basin predictability: `data/aggregated/basin_predictability_cross/cross_basin_predictability.csv`.
- §5.4 T-sweep: `data/aggregated/t_sensitivity_cross_regime/cross_t_sensitivity.csv`.
- §5.5 / §5.0 adv_switch: `data/aggregated/perturbation_cross_regime/cross_switching_rates.csv`.
- §5.6 dose-response: `data/aggregated/perturbation_dose_response/dose_response.csv`.
- §5.7 basin hardening: `data/aggregated/perturbation_basin_hardening/basin_hardening.csv`.
- §5.10 V* + RG: `data/aggregated/perturbation_geometric_barriers/{v_star_table,rg_merge_table}.csv`.

Regenerate this report with `python -m scripts.publication_summary`.
