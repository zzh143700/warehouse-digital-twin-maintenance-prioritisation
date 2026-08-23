# Digital-Twin-Inspired Warehouse Maintenance Decision-Support Simulation Results

Base specification: C-MAPSS predictions used only as surrogate degradation inputs; one value from each empirical quintile; assignment seed 42; H=125 abstract cycles; equal consequence weights.

## Base ranking

| Rank | Asset | C-MAPSS source unit | Surrogate RUL input | Quantile | Urgency | Consequence | Priority | RUL-only rank | Criticality-only rank |
|---:|---|---:|---:|---|---:|---:|---:|---:|---:|
| 1 | A1 Inbound conveyor motor | 24 | 32.316 | Q1_shortest_0_20pct | 0.741 | 0.667 | 49.431 | 1 | 2 |
| 2 | A4 AGV/shuttle drive unit | 64 | 47.550 | Q2_20_40pct | 0.620 | 0.400 | 24.784 | 2 | 5 |
| 3 | A5 Packing-station roller motor | 74 | 94.814 | Q3_40_60pct | 0.241 | 0.533 | 12.879 | 3 | 4 |
| 4 | A2 Sortation conveyor drive | 47 | 121.816 | Q4_60_80pct | 0.025 | 0.933 | 2.377 | 4 | 1 |
| 5 | A3 Vertical lift motor | 39 | 172.984 | Q5_longest_80_100pct | 0.000 | 0.800 | 0.000 | 5 | 2 |

## Behaviour and sensitivity summary

- Across 1,000 quintile-stratified seeded assignments, exact agreement with RUL-only ranking: 0.557; top-rank agreement: 0.704.
- Across the same assignments, exact agreement with criticality-only ranking: 0.000; top-rank agreement: 0.320.
- Adjacent-score sensitivity across all seeded assignments: exact-rank agreement 0.936; top-rank agreement 0.964.
- Prediction-noise robustness: mean Spearman rho 0.807; top-rank agreement 0.802.
- All controlled monotonicity, dominance and weight-sum checks: PASS.

These outputs evaluate C-MAPSS model performance and the internal behaviour of an assumption-based prioritisation method. They do not validate warehouse RUL, real-world warehouse risk or operational maintenance effectiveness.
