"""Train and evaluate the locked FD001 RUL models.

This portable version reads the three processed FD001 input files from the
package-level ``input_data`` directory and writes all artefacts to
``outputs/model_outputs``.

It performs grouped cross-validation on training engines only, selects one
Ridge and one Gradient Boosting configuration, then evaluates each fitted
pipeline once on the official FD001 test endpoints.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
import time
from itertools import product
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


SEED = 42
N_SPLITS = 5

WORKSPACE = Path(__file__).resolve().parents[1]
DATA_DIR = WORKSPACE / "input_data"
OUTPUT_DIR = WORKSPACE / "outputs" / "model_outputs"
MODEL_DIR = OUTPUT_DIR / "models"

TRAIN_PATH = DATA_DIR / "train_FD001_with_headers_and_rul.csv"
TEST_PATH = DATA_DIR / "test_FD001_with_headers.csv"
TRUTH_PATH = DATA_DIR / "RUL_FD001_with_unit_id.csv"

EXCLUDED_CONSTANT = [
    "operational_setting_3",
    "sensor_01",
    "sensor_05",
    "sensor_10",
    "sensor_16",
    "sensor_18",
    "sensor_19",
]

FEATURES = [
    "cycle",
    "operational_setting_1",
    "operational_setting_2",
    "sensor_02",
    "sensor_03",
    "sensor_04",
    "sensor_06",
    "sensor_07",
    "sensor_08",
    "sensor_09",
    "sensor_11",
    "sensor_12",
    "sensor_13",
    "sensor_14",
    "sensor_15",
    "sensor_17",
    "sensor_20",
    "sensor_21",
]


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ridge_candidates() -> list[dict]:
    return [{"alpha": value} for value in (0.1, 1.0, 10.0, 100.0)]


def gradient_boosting_candidates() -> list[dict]:
    keys = ("n_estimators", "learning_rate", "max_depth", "min_samples_leaf")
    values = product((100, 200), (0.03, 0.05), (2, 3), (5, 10))
    return [dict(zip(keys, candidate)) for candidate in values]


def make_model(model_name: str, params: dict):
    if model_name == "ridge":
        return Pipeline(
            [
                ("scale", StandardScaler()),
                ("model", Ridge(alpha=params["alpha"])),
            ]
        )
    if model_name == "gradient_boosting":
        return GradientBoostingRegressor(
            loss="squared_error",
            random_state=SEED,
            subsample=1.0,
            **params,
        )
    raise ValueError(f"Unknown model: {model_name}")


def grouped_cv_search(
    model_name: str,
    candidates: list[dict],
    X: pd.DataFrame,
    y: pd.Series,
    groups: pd.Series,
) -> tuple[pd.DataFrame, pd.DataFrame, dict, np.ndarray]:
    splitter = GroupKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED)
    splits = list(splitter.split(X, y, groups))

    for train_idx, valid_idx in splits:
        train_groups = set(groups.iloc[train_idx])
        valid_groups = set(groups.iloc[valid_idx])
        if train_groups.intersection(valid_groups):
            raise AssertionError("Engine leakage detected between grouped folds")

    candidate_rows: list[dict] = []
    fold_rows: list[dict] = []
    candidate_oof: dict[int, np.ndarray] = {}

    for candidate_id, params in enumerate(candidates, start=1):
        oof = np.full(len(X), np.nan, dtype=float)
        per_fold: list[dict] = []

        for fold_id, (train_idx, valid_idx) in enumerate(splits, start=1):
            model = make_model(model_name, params)
            model.fit(X.iloc[train_idx], y.iloc[train_idx])
            pred = model.predict(X.iloc[valid_idx])
            oof[valid_idx] = pred

            fold_record = {
                "model": model_name,
                "candidate_id": candidate_id,
                "fold": fold_id,
                "train_engines": int(groups.iloc[train_idx].nunique()),
                "validation_engines": int(groups.iloc[valid_idx].nunique()),
                "validation_rows": int(len(valid_idx)),
                "mae": float(mean_absolute_error(y.iloc[valid_idx], pred)),
                "rmse": rmse(y.iloc[valid_idx].to_numpy(), pred),
            }
            fold_record.update(params)
            per_fold.append(fold_record)
            fold_rows.append(fold_record)

        if np.isnan(oof).any():
            raise AssertionError("Out-of-fold prediction vector is incomplete")

        candidate_record = {
            "model": model_name,
            "candidate_id": candidate_id,
            "mean_fold_mae": float(np.mean([row["mae"] for row in per_fold])),
            "sd_fold_mae": float(np.std([row["mae"] for row in per_fold], ddof=1)),
            "mean_fold_rmse": float(np.mean([row["rmse"] for row in per_fold])),
            "sd_fold_rmse": float(np.std([row["rmse"] for row in per_fold], ddof=1)),
            "pooled_oof_mae": float(mean_absolute_error(y, oof)),
            "pooled_oof_rmse": rmse(y.to_numpy(), oof),
        }
        candidate_record.update(params)
        candidate_rows.append(candidate_record)
        candidate_oof[candidate_id] = oof

    results = pd.DataFrame(candidate_rows).sort_values(
        ["mean_fold_rmse", "mean_fold_mae", "candidate_id"],
        ignore_index=True,
    )
    selected_id = int(results.iloc[0]["candidate_id"])
    selected_params = candidates[selected_id - 1]
    selected_oof = candidate_oof[selected_id]
    fold_metrics = pd.DataFrame(fold_rows)
    fold_metrics["selected"] = fold_metrics["candidate_id"].eq(selected_id)
    return results, fold_metrics, selected_params, selected_oof


def endpoint_rows(test: pd.DataFrame) -> pd.DataFrame:
    indices = test.groupby("unit_id", sort=True)["cycle"].idxmax()
    endpoints = test.loc[indices].sort_values("unit_id").reset_index(drop=True)
    if len(endpoints) != 100 or endpoints["unit_id"].nunique() != 100:
        raise AssertionError("Expected 100 unique FD001 test endpoints")
    return endpoints


def timed_predict(model, X: pd.DataFrame, repeats: int = 200) -> tuple[np.ndarray, float]:
    prediction = model.predict(X)
    start = time.perf_counter()
    for _ in range(repeats):
        model.predict(X)
    elapsed_ms = (time.perf_counter() - start) * 1000 / repeats
    return prediction, float(elapsed_ms)


def serialisable(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Cannot serialise {type(value)}")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # Only training data are loaded during feature/parameter selection.
    train = pd.read_csv(TRAIN_PATH)
    if train["unit_id"].nunique() != 100 or len(train) != 20_631:
        raise AssertionError("FD001 training counts do not match the audited protocol")
    if train[FEATURES + ["rul_target"]].isna().any().any():
        raise AssertionError("Unexpected missing model input")

    X = train[FEATURES]
    y = train["rul_target"]
    groups = train["unit_id"]

    searches = {
        "ridge": ridge_candidates(),
        "gradient_boosting": gradient_boosting_candidates(),
    }
    selected: dict[str, dict] = {}
    selected_oof: dict[str, np.ndarray] = {}
    all_search_results: list[pd.DataFrame] = []
    all_fold_results: list[pd.DataFrame] = []

    for model_name, candidates in searches.items():
        search_results, fold_results, params, oof = grouped_cv_search(
            model_name, candidates, X, y, groups
        )
        all_search_results.append(search_results)
        all_fold_results.append(fold_results)
        selected[model_name] = params
        selected_oof[model_name] = oof

    search_table = pd.concat(all_search_results, ignore_index=True)
    fold_table = pd.concat(all_fold_results, ignore_index=True)
    search_table.to_csv(OUTPUT_DIR / "model_cv_search_results.csv", index=False)
    fold_table.to_csv(OUTPUT_DIR / "model_cv_fold_metrics.csv", index=False)

    oof_table = train[["unit_id", "cycle", "rul_target"]].copy()
    for model_name, oof in selected_oof.items():
        oof_table[f"{model_name}_oof_prediction"] = oof
        oof_table[f"{model_name}_oof_residual"] = y.to_numpy() - oof
    oof_table.to_csv(OUTPUT_DIR / "selected_model_oof_predictions.csv", index=False)

    # Official test data and endpoint truth are first used after model selection.
    test = pd.read_csv(TEST_PATH)
    truth = pd.read_csv(TRUTH_PATH).sort_values("unit_id").reset_index(drop=True)
    endpoints = endpoint_rows(test)
    if not np.array_equal(endpoints["unit_id"].to_numpy(), truth["unit_id"].to_numpy()):
        raise AssertionError("Official endpoint truth is misaligned with test engines")

    endpoint_output = endpoints[["unit_id", "cycle"]].copy()
    endpoint_output["true_endpoint_rul"] = truth["endpoint_rul"]
    model_summaries: dict[str, dict] = {}

    for model_name, params in selected.items():
        model = make_model(model_name, params)
        fit_start = time.perf_counter()
        model.fit(X, y)
        fit_seconds = float(time.perf_counter() - fit_start)

        raw_pred, inference_ms = timed_predict(model, endpoints[FEATURES])
        clipped_pred = np.maximum(raw_pred, 0.0)
        endpoint_output[f"{model_name}_prediction_raw"] = raw_pred
        endpoint_output[f"{model_name}_prediction_nonnegative"] = clipped_pred
        endpoint_output[f"{model_name}_error_raw"] = truth["endpoint_rul"] - raw_pred

        model_path = MODEL_DIR / f"{model_name}_fd001.joblib"
        joblib.dump(model, model_path, compress=3)

        cv_selected = search_table[
            (search_table["model"] == model_name)
            & (search_table["candidate_id"] == search_table[search_table["model"] == model_name]
               .sort_values(["mean_fold_rmse", "mean_fold_mae", "candidate_id"])
               .iloc[0]["candidate_id"])
        ].iloc[0]

        model_summaries[model_name] = {
            "selected_parameters": params,
            "cv_mean_fold_mae": float(cv_selected["mean_fold_mae"]),
            "cv_sd_fold_mae": float(cv_selected["sd_fold_mae"]),
            "cv_mean_fold_rmse": float(cv_selected["mean_fold_rmse"]),
            "cv_sd_fold_rmse": float(cv_selected["sd_fold_rmse"]),
            "cv_pooled_oof_mae": float(cv_selected["pooled_oof_mae"]),
            "cv_pooled_oof_rmse": float(cv_selected["pooled_oof_rmse"]),
            "test_endpoint_mae_raw": float(mean_absolute_error(truth["endpoint_rul"], raw_pred)),
            "test_endpoint_rmse_raw": rmse(truth["endpoint_rul"].to_numpy(), raw_pred),
            "test_endpoint_mae_nonnegative": float(
                mean_absolute_error(truth["endpoint_rul"], clipped_pred)
            ),
            "test_endpoint_rmse_nonnegative": rmse(
                truth["endpoint_rul"].to_numpy(), clipped_pred
            ),
            "negative_endpoint_predictions": int(np.sum(raw_pred < 0)),
            "fit_seconds_full_training": fit_seconds,
            "mean_endpoint_inference_ms_for_100_rows": inference_ms,
            "model_file": str(model_path.relative_to(WORKSPACE)),
            "model_file_bytes": int(model_path.stat().st_size),
            "model_file_sha256": sha256(model_path),
        }

        if model_name == "gradient_boosting":
            importance = pd.DataFrame(
                {"feature": FEATURES, "importance": model.feature_importances_}
            ).sort_values("importance", ascending=False, ignore_index=True)
            importance.to_csv(OUTPUT_DIR / "gradient_boosting_feature_importance.csv", index=False)

    endpoint_output.to_csv(OUTPUT_DIR / "fd001_test_endpoint_predictions.csv", index=False)

    summary = {
        "run_timestamp_local": pd.Timestamp.now().isoformat(),
        "random_seed": SEED,
        "grouped_cv_folds": N_SPLITS,
        "target": "uncapped RUL = maximum training cycle by engine - current cycle",
        "retained_features": FEATURES,
        "excluded_exact_constant_features": EXCLUDED_CONSTANT,
        "training_rows": int(len(train)),
        "training_engines": int(train["unit_id"].nunique()),
        "test_endpoint_engines": int(len(endpoints)),
        "selection_rule": "lowest mean grouped-fold RMSE; mean MAE and candidate ID as tie-breakers",
        "software": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
        "input_hashes": {
            str(TRAIN_PATH.relative_to(WORKSPACE)): sha256(TRAIN_PATH),
            str(TEST_PATH.relative_to(WORKSPACE)): sha256(TEST_PATH),
            str(TRUTH_PATH.relative_to(WORKSPACE)): sha256(TRUTH_PATH),
        },
        "models": model_summaries,
    }
    with (OUTPUT_DIR / "model_run_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False, default=serialisable)

    readable = [
        "# FD001 RUL Model Results",
        "",
        f"Run timestamp: {summary['run_timestamp_local']}",
        f"Software: Python {platform.python_version()}, scikit-learn {sklearn.__version__}",
        f"Grouped cross-validation: {N_SPLITS} folds by engine ID; seed {SEED}",
        "",
        "| Model | Selected parameters | CV mean MAE | CV mean RMSE | Test MAE | Test RMSE | Negative endpoints |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for model_name, values in model_summaries.items():
        readable.append(
            "| {name} | `{params}` | {cv_mae:.3f} | {cv_rmse:.3f} | {test_mae:.3f} | "
            "{test_rmse:.3f} | {negative} |".format(
                name=model_name.replace("_", " ").title(),
                params=json.dumps(values["selected_parameters"], sort_keys=True),
                cv_mae=values["cv_mean_fold_mae"],
                cv_rmse=values["cv_mean_fold_rmse"],
                test_mae=values["test_endpoint_mae_nonnegative"],
                test_rmse=values["test_endpoint_rmse_nonnegative"],
                negative=values["negative_endpoint_predictions"],
            )
        )
    readable.extend(
        [
            "",
            "The endpoint metrics evaluate C-MAPSS FD001 only. They do not validate warehouse prognostics or maintenance decisions.",
        ]
    )
    (OUTPUT_DIR / "model_results_summary.md").write_text(
        "\n".join(readable) + "\n", encoding="utf-8"
    )
    print("\n".join(readable))


if __name__ == "__main__":
    main()
