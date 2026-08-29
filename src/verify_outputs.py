"""Verify that the portable package produced the expected result structure."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = PACKAGE_ROOT / "outputs" / "model_outputs"
RANKING_DIR = PACKAGE_ROOT / "outputs" / "ranking_outputs"
SCENARIO_CONFIG_PATH = PACKAGE_ROOT / "config" / "warehouse_scenario.json"


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing required output: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def all_boolean_checks_pass(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, dict):
        return all(all_boolean_checks_pass(item) for item in value.values())
    return True


def main() -> None:
    model = load_json(MODEL_DIR / "model_run_summary.json")
    ranking = load_json(RANKING_DIR / "warehouse_ranking_summary.json")
    scenario = load_json(SCENARIO_CONFIG_PATH)
    scenario_key = str(SCENARIO_CONFIG_PATH.relative_to(PACKAGE_ROOT))

    mapping = pd.read_csv(RANKING_DIR / "warehouse_mapping_monte_carlo_rows.csv")
    score_sensitivity = pd.read_csv(
        RANKING_DIR / "warehouse_score_sensitivity_stability.csv"
    )
    rul_baseline = pd.read_csv(
        RANKING_DIR / "warehouse_mapping_vs_rul_only_stability.csv"
    )
    criticality_baseline = pd.read_csv(
        RANKING_DIR / "warehouse_mapping_vs_criticality_only_stability.csv"
    )

    checks = {
        "100 training engines": model["training_engines"] == 100,
        "100 test engines": model["test_endpoint_engines"] == 100,
        "5,000 seeded asset rows": len(mapping) == 5_000,
        "1,000 assignment repetitions": mapping["repetition"].nunique() == 1_000,
        "five assets in every assignment": bool(
            (mapping.groupby("repetition")["asset_id"].nunique() == 5).all()
        ),
        "five quintiles in every assignment": bool(
            (mapping.groupby("repetition")["surrogate_rul_quantile"].nunique() == 5).all()
        ),
        "28,000 adjacent-score comparisons": len(score_sensitivity) == 28_000,
        "1,000 RUL-only comparisons": len(rul_baseline) == 1_000,
        "1,000 criticality-only comparisons": len(criticality_baseline) == 1_000,
        "base weights sum to one": abs(ranking["base_weights_sum"] - 1.0) < 1e-12,
        "controlled mathematical checks": all_boolean_checks_pass(
            ranking["controlled_checks"]
        ),
        "surrogate-only transfer boundary recorded": (
            "surrogate degradation inputs" in ranking["transfer_boundary"]
        ),
        "machine-readable scenario has five assets": (
            len(scenario["assets"]) == 5
            and len({asset["asset_id"] for asset in scenario["assets"]}) == 5
        ),
        "scenario configuration hash recorded": (
            ranking["input_hashes"].get(scenario_key) == sha256(SCENARIO_CONFIG_PATH)
        ),
    }

    failures = [name for name, passed in checks.items() if not passed]
    print("\nVerification checks")
    for name, passed in checks.items():
        print(f"[{'PASS' if passed else 'FAIL'}] {name}")

    gb = model["models"]["gradient_boosting"]
    score = ranking["score_sensitivity_overall"]
    noise = ranking["noise_rank_stability"]
    print("\nKey reproducible results")
    print(f"Gradient Boosting endpoint MAE: {gb['test_endpoint_mae_nonnegative']:.6f}")
    print(f"Gradient Boosting endpoint RMSE: {gb['test_endpoint_rmse_nonnegative']:.6f}")
    print(f"Adjacent-score exact-order agreement: {score['exact_rank_agreement_probability']:.6f}")
    print(f"Adjacent-score top-rank agreement: {score['top_rank_agreement_probability']:.6f}")
    print(f"Prediction-noise top-rank agreement: {noise['top_rank_agreement_probability']:.6f}")

    if failures:
        print("\nVerification failed: " + "; ".join(failures), file=sys.stderr)
        raise SystemExit(1)
    print("\nAll required checks passed.")


if __name__ == "__main__":
    main()
