"""Shared calculation and validation logic for the priority dashboard.

The dashboard reuses the dissertation's author-developed priority equation.
C-MAPSS RUL predictions are treated as surrogate degradation inputs after
transfer to the conceptual warehouse scenario. Nothing in this module claims
live sensor connectivity or warehouse-asset RUL validity.
"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd

from run_warehouse_priority_simulation import (
    BASE_HORIZON,
    BASE_WEIGHTS,
    SCORE_DIMENSIONS,
    score_assets,
)


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
BASE_RANKING_PATH = (
    PACKAGE_ROOT
    / "outputs"
    / "ranking_outputs"
    / "warehouse_base_mapping_and_ranking.csv"
)

EXPECTED_ASSET_IDS = {"A1", "A2", "A3", "A4", "A5"}
INPUT_COLUMNS = [
    "asset_id",
    "asset_role",
    "criticality",
    "capacity_loss_percent",
    "throughput",
    "severity",
    "surrogate_rul_input",
]
OUTPUT_COLUMNS = [
    "priority_rank",
    "asset_id",
    "asset_role",
    "surrogate_rul_input",
    "rul_urgency",
    "combined_consequence",
    "priority_score",
]


def load_base_dashboard_inputs(path: Path = BASE_RANKING_PATH) -> pd.DataFrame:
    """Load the fixed seed-42 base case used in the dissertation."""

    if not path.exists():
        raise FileNotFoundError(f"Base ranking file was not found: {path}")
    frame = pd.read_csv(path)
    missing = sorted(set(INPUT_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"Base ranking file is missing columns: {missing}")
    return validate_dashboard_inputs(frame[INPUT_COLUMNS])


def validate_dashboard_inputs(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate and return a clean five-asset dashboard input table."""

    missing = sorted(set(INPUT_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"Dashboard input is missing columns: {missing}")

    clean = frame[INPUT_COLUMNS].copy()
    if len(clean) != len(EXPECTED_ASSET_IDS):
        raise ValueError("Dashboard input must contain exactly five assets")
    if clean["asset_id"].duplicated().any():
        raise ValueError("Dashboard asset IDs must be unique")
    if set(clean["asset_id"].astype(str)) != EXPECTED_ASSET_IDS:
        raise ValueError("Dashboard input must contain assets A1 to A5")

    if clean["asset_role"].isna().any() or clean["asset_role"].astype(str).str.strip().eq("").any():
        raise ValueError("Every dashboard asset must have a role")

    numeric_columns = [
        "criticality",
        "capacity_loss_percent",
        "throughput",
        "severity",
        "surrogate_rul_input",
    ]
    for column in numeric_columns:
        clean[column] = pd.to_numeric(clean[column], errors="coerce")
    if clean[numeric_columns].isna().any().any():
        raise ValueError("Dashboard scores and surrogate inputs must be numeric")
    if (clean["surrogate_rul_input"] < 0).any():
        raise ValueError("Surrogate degradation inputs must be non-negative")
    for dimension in SCORE_DIMENSIONS:
        if ((clean[dimension] < 1) | (clean[dimension] > 5)).any():
            raise ValueError(f"{dimension} scores must remain within 1-5")

    return clean.sort_values("asset_id").reset_index(drop=True)


def calculate_dashboard_priorities(
    frame: pd.DataFrame,
    horizon: float = BASE_HORIZON,
    weights: Mapping[str, float] = BASE_WEIGHTS,
) -> pd.DataFrame:
    """Recalculate and rank current dashboard inputs."""

    if not np.isfinite(horizon) or horizon <= 0:
        raise ValueError("Planning horizon must be a positive number")
    clean = validate_dashboard_inputs(frame)
    scored = score_assets(clean, horizon=float(horizon), weights=dict(weights))
    return scored.sort_values(["priority_rank", "asset_id"]).reset_index(drop=True)


def dashboard_snapshot(scored: pd.DataFrame) -> dict[str, object]:
    """Return the small set of headline values displayed by the dashboard."""

    if scored.empty:
        raise ValueError("The scored dashboard table is empty")
    top_score = float(scored["priority_score"].max())
    top_assets = scored.loc[
        np.isclose(scored["priority_score"], top_score), "asset_id"
    ].astype(str).tolist()
    return {
        "top_assets": top_assets,
        "top_score": top_score,
        "active_assets": int((scored["rul_urgency"] > 0).sum()),
        "total_assets": int(len(scored)),
    }


def export_dashboard_table(scored: pd.DataFrame) -> pd.DataFrame:
    """Select and round the auditable dashboard output columns."""

    export = scored[OUTPUT_COLUMNS].copy()
    for column in [
        "surrogate_rul_input",
        "rul_urgency",
        "combined_consequence",
        "priority_score",
    ]:
        export[column] = export[column].astype(float).round(6)
    return export
