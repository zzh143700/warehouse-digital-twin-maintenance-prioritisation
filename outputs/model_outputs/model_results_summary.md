# FD001 RUL Model Results

Run timestamp: 2026-08-23T19:24:04.968056
Software: Python 3.13.9, scikit-learn 1.9.0
Grouped cross-validation: 5 folds by engine ID; seed 42

| Model | Selected parameters | CV mean MAE | CV mean RMSE | Test MAE | Test RMSE | Negative endpoints |
|---|---|---:|---:|---:|---:|---:|
| Ridge | `{"alpha": 100.0}` | 31.321 | 40.640 | 25.668 | 30.944 | 2 |
| Gradient Boosting | `{"learning_rate": 0.05, "max_depth": 3, "min_samples_leaf": 5, "n_estimators": 100}` | 26.569 | 37.001 | 18.158 | 24.868 | 0 |

The endpoint metrics evaluate C-MAPSS FD001 only. They do not validate warehouse prognostics or maintenance decisions.
