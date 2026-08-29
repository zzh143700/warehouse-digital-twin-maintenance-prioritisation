"""Prepare and audit the packaged C-MAPSS FD001 text files.

The script preserves ``source_data`` and writes reproducible, header-labelled
CSV inputs to ``input_data``. The training target is the uncapped,
dataset-specific RUL definition: final observed cycle minus current cycle.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PACKAGE_ROOT / "source_data"
PROCESSED_DIR = PACKAGE_ROOT / "input_data"
AUDIT_DIR = PACKAGE_ROOT / "outputs" / "data_audit"

COLUMNS = (
    ["unit_id", "cycle"]
    + [f"operational_setting_{i}" for i in range(1, 4)]
    + [f"sensor_{i:02d}" for i in range(1, 22)]
)

TRAIN_SOURCE = SOURCE_DIR / "train_FD001.txt"
TEST_SOURCE = SOURCE_DIR / "test_FD001.txt"
TRUTH_SOURCE = SOURCE_DIR / "RUL_FD001.txt"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assert_continuous_cycles(frame: pd.DataFrame, label: str) -> None:
    for unit_id, group in frame.groupby("unit_id", sort=True):
        cycles = group["cycle"].tolist()
        expected = list(range(1, int(group["cycle"].max()) + 1))
        if cycles != expected:
            raise AssertionError(f"{label} unit {unit_id} has non-continuous cycles")


def main() -> None:
    for path in (TRAIN_SOURCE, TEST_SOURCE, TRUTH_SOURCE):
        if not path.exists():
            raise FileNotFoundError(f"Required source file is missing: {path}")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    train = pd.read_csv(TRAIN_SOURCE, sep=r"\s+", header=None, names=COLUMNS)
    test = pd.read_csv(TEST_SOURCE, sep=r"\s+", header=None, names=COLUMNS)
    endpoint_rul = pd.read_csv(
        TRUTH_SOURCE, sep=r"\s+", header=None, names=["endpoint_rul"]
    )["endpoint_rul"]

    if train.isna().any().any() or test.isna().any().any() or endpoint_rul.isna().any():
        raise AssertionError("Missing values detected in packaged FD001 source data")
    if train.duplicated().any() or test.duplicated().any():
        raise AssertionError("Exact duplicate rows detected in packaged FD001 source data")
    if train["unit_id"].nunique() != 100 or test["unit_id"].nunique() != 100:
        raise AssertionError("FD001 should contain 100 training and 100 test engines")
    if len(endpoint_rul) != test["unit_id"].nunique():
        raise AssertionError("Endpoint-RUL vector does not align with test-engine count")

    assert_continuous_cycles(train, "training")
    assert_continuous_cycles(test, "test")

    train["rul_target"] = (
        train.groupby("unit_id")["cycle"].transform("max") - train["cycle"]
    )
    if not (train.groupby("unit_id").tail(1)["rul_target"] == 0).all():
        raise AssertionError("The final training row for every engine must have RUL zero")

    truth = pd.DataFrame(
        {
            "unit_id": sorted(test["unit_id"].unique()),
            "endpoint_rul": endpoint_rul.to_numpy(),
        }
    )

    train_output = PROCESSED_DIR / "train_FD001_with_headers_and_rul.csv"
    test_output = PROCESSED_DIR / "test_FD001_with_headers.csv"
    truth_output = PROCESSED_DIR / "RUL_FD001_with_unit_id.csv"
    train.to_csv(train_output, index=False)
    test.to_csv(test_output, index=False)
    truth.to_csv(truth_output, index=False)

    constant_columns = [
        column for column in COLUMNS[2:] if train[column].nunique(dropna=False) == 1
    ]
    summary = {
        "run_timestamp_local": datetime.now().isoformat(),
        "scope": "C-MAPSS FD001 data preparation and structural audit only",
        "target_definition": "uncapped RUL = final training cycle by engine - current cycle",
        "training_rows": int(len(train)),
        "training_engines": int(train["unit_id"].nunique()),
        "test_rows": int(len(test)),
        "test_engines": int(test["unit_id"].nunique()),
        "endpoint_labels": int(len(truth)),
        "missing_cells": int(
            train.isna().sum().sum() + test.isna().sum().sum() + truth.isna().sum().sum()
        ),
        "exact_duplicate_rows": int(train.duplicated().sum() + test.duplicated().sum()),
        "continuous_cycles": True,
        "constant_training_predictors": constant_columns,
        "source_hashes": {
            path.name: sha256(path)
            for path in (TRAIN_SOURCE, TEST_SOURCE, TRUTH_SOURCE)
        },
        "processed_hashes": {
            path.name: sha256(path)
            for path in (train_output, test_output, truth_output)
        },
        "software": {
            "python": sys.version,
            "platform": platform.platform(),
            "pandas": pd.__version__,
        },
        "interpretation_boundary": (
            "These data describe simulated turbofan degradation and do not measure "
            "warehouse equipment."
        ),
    }

    (AUDIT_DIR / "fd001_data_preparation_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
