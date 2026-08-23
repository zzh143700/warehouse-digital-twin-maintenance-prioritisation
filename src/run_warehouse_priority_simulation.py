"""Run the digital-twin-inspired warehouse maintenance decision-support simulation.

C-MAPSS FD001 predictions are evaluated as turbofan RUL predictions in the
prognostic layer. In the warehouse layer their numerical values are used only
as surrogate degradation inputs. They are not presented as warehouse-asset RUL
predictions. Warehouse roles and 1-5 consequence scores are author-defined
scenario parameters documented in ``docs/warehouse_scenario_protocol.md``.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy


MASTER_SEED = 42
BASE_HORIZON = 125.0
ASSIGNMENT_REPETITIONS = 1_000
NOISE_REPETITIONS = 1_000
QUANTILE_LABELS = [
    "Q1_shortest_0_20pct",
    "Q2_20_40pct",
    "Q3_40_60pct",
    "Q4_60_80pct",
    "Q5_longest_80_100pct",
]
SCORE_DIMENSIONS = ("criticality", "throughput", "severity")

WORKSPACE = Path(__file__).resolve().parents[1]
RUN_DIR = WORKSPACE
MODEL_OUTPUT_DIR = WORKSPACE / "outputs" / "model_outputs"
OUTPUT_DIR = WORKSPACE / "outputs" / "ranking_outputs"

PREDICTION_PATH = MODEL_OUTPUT_DIR / "fd001_test_endpoint_predictions.csv"
OOF_PATH = MODEL_OUTPUT_DIR / "selected_model_oof_predictions.csv"
PROTOCOL_PATH = WORKSPACE / "docs" / "warehouse_scenario_protocol.md"
SOURCE_PREDICTION_COLUMN = "gradient_boosting_prediction_nonnegative"

BASE_WEIGHTS = {
    "criticality": 1.0 / 3.0,
    "throughput": 1.0 / 3.0,
    "severity": 1.0 / 3.0,
}

WEIGHT_SCHEMES = {
    "equal": BASE_WEIGHTS,
    "criticality_heavy": {"criticality": 0.50, "throughput": 0.25, "severity": 0.25},
    "throughput_heavy": {"criticality": 0.25, "throughput": 0.50, "severity": 0.25},
    "severity_heavy": {"criticality": 0.25, "throughput": 0.25, "severity": 0.50},
}

ABLATION_SCHEMES = {
    "no_criticality": {"criticality": 0.0, "throughput": 0.50, "severity": 0.50},
    "no_throughput": {"criticality": 0.50, "throughput": 0.0, "severity": 0.50},
    "no_severity": {"criticality": 0.50, "throughput": 0.50, "severity": 0.0},
}

ASSETS = pd.DataFrame(
    [
        {
            "asset_id": "A1",
            "asset_role": "Inbound conveyor motor",
            "criticality": 4,
            "capacity_loss_percent": 40,
            "throughput": 3,
            "severity": 3,
        },
        {
            "asset_id": "A2",
            "asset_role": "Sortation conveyor drive",
            "criticality": 5,
            "capacity_loss_percent": 80,
            "throughput": 5,
            "severity": 4,
        },
        {
            "asset_id": "A3",
            "asset_role": "Vertical lift motor",
            "criticality": 4,
            "capacity_loss_percent": 55,
            "throughput": 4,
            "severity": 4,
        },
        {
            "asset_id": "A4",
            "asset_role": "AGV/shuttle drive unit",
            "criticality": 2,
            "capacity_loss_percent": 15,
            "throughput": 2,
            "severity": 2,
        },
        {
            "asset_id": "A5",
            "asset_role": "Packing-station roller motor",
            "criticality": 3,
            "capacity_loss_percent": 35,
            "throughput": 3,
            "severity": 2,
        },
    ]
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_weights(weights: dict[str, float]) -> None:
    if set(weights) != set(SCORE_DIMENSIONS):
        raise AssertionError("Unexpected weight dimensions")
    if any(value < 0 for value in weights.values()):
        raise AssertionError("Weights must be non-negative")
    if not np.isclose(sum(weights.values()), 1.0):
        raise AssertionError("Weights must sum to one")


def prepare_prediction_pool(
    predictions: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, dict[str, float]]]:
    if len(predictions) != 100 or predictions["unit_id"].nunique() != 100:
        raise AssertionError("Expected 100 unique FD001 endpoint predictions")
    if predictions[SOURCE_PREDICTION_COLUMN].isna().any():
        raise AssertionError("C-MAPSS endpoint predictions contain missing values")
    if (predictions[SOURCE_PREDICTION_COLUMN] < 0).any():
        raise AssertionError("Surrogate inputs must be non-negative")

    pool = predictions.sort_values("unit_id").reset_index(drop=True).copy()
    pool["surrogate_rul_input"] = pool[SOURCE_PREDICTION_COLUMN]
    pool["surrogate_rul_quantile"] = pd.qcut(
        pool["surrogate_rul_input"],
        q=5,
        labels=QUANTILE_LABELS,
        duplicates="raise",
    )
    counts = pool["surrogate_rul_quantile"].value_counts().sort_index()
    if counts.tolist() != [20, 20, 20, 20, 20]:
        raise AssertionError(f"Unexpected quintile counts: {counts.to_dict()}")

    edges = np.quantile(pool["surrogate_rul_input"], [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    boundaries = {
        label: {"lower_inclusive": float(edges[i]), "upper_inclusive": float(edges[i + 1])}
        for i, label in enumerate(QUANTILE_LABELS)
    }
    return pool, boundaries


def build_assignment(
    pool: pd.DataFrame,
    seed: int,
    design: str = "quintile_stratified",
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    if design == "quintile_stratified":
        selected_rows = []
        for label in QUANTILE_LABELS:
            group = pool.loc[pool["surrogate_rul_quantile"] == label]
            selected_rows.append(group.loc[rng.choice(group.index)])
        sample = pd.DataFrame(selected_rows).reset_index(drop=True)
        sample = sample.iloc[rng.permutation(len(sample))].reset_index(drop=True)
    elif design == "unstratified_random":
        indices = rng.choice(len(pool), size=len(ASSETS), replace=False)
        sample = pool.iloc[indices].reset_index(drop=True)
    else:
        raise ValueError(f"Unknown assignment design: {design}")

    scenario = ASSETS.copy()
    scenario["assignment_seed"] = seed
    scenario["assignment_design"] = design
    scenario["source_cmapss_unit_id"] = sample["unit_id"].to_numpy()
    scenario["source_true_endpoint_rul_diagnostic_only"] = sample[
        "true_endpoint_rul"
    ].to_numpy()
    scenario["surrogate_rul_input"] = sample["surrogate_rul_input"].to_numpy()
    scenario["surrogate_rul_quantile"] = sample[
        "surrogate_rul_quantile"
    ].astype(str).to_numpy()
    return scenario


def score_assets(
    frame: pd.DataFrame,
    horizon: float = BASE_HORIZON,
    weights: dict[str, float] = BASE_WEIGHTS,
    rul_column: str = "surrogate_rul_input",
) -> pd.DataFrame:
    validate_weights(weights)
    if horizon <= 0:
        raise ValueError("Planning horizon must be positive")
    for dimension in SCORE_DIMENSIONS:
        if ((frame[dimension] < 1) | (frame[dimension] > 5)).any():
            raise AssertionError(f"{dimension} scores must be within 1-5")

    scored = frame.copy()
    scored["rul_urgency"] = np.clip(1.0 - scored[rul_column] / horizon, 0.0, 1.0)
    scored["combined_consequence"] = (
        weights["criticality"] * scored["criticality"] / 5.0
        + weights["throughput"] * scored["throughput"] / 5.0
        + weights["severity"] * scored["severity"] / 5.0
    )
    scored["priority_score"] = 100.0 * scored["rul_urgency"] * scored["combined_consequence"]
    scored["priority_rank"] = scored["priority_score"].rank(
        method="min", ascending=False
    ).astype(int)
    scored["rul_only_score"] = 100.0 * scored["rul_urgency"]
    scored["rul_only_rank"] = scored["rul_only_score"].rank(
        method="min", ascending=False
    ).astype(int)
    scored["criticality_only_score"] = 20.0 * scored["criticality"]
    scored["criticality_only_rank"] = scored["criticality_only_score"].rank(
        method="min", ascending=False
    ).astype(int)
    return scored


def rank_comparison(reference: pd.DataFrame, comparison: pd.DataFrame) -> dict:
    ref = reference.set_index("asset_id")["priority_rank"].sort_index()
    comp = comparison.set_index("asset_id")["priority_rank"].sort_index()
    if ref.nunique() < 2 or comp.nunique() < 2:
        rho = np.nan
        tau = np.nan
    else:
        # The inputs are already rank vectors, so Spearman rho is their Pearson
        # correlation. Computing the two five-element statistics directly is
        # much faster than repeated scipy object construction in 28,000 score
        # sensitivity comparisons.
        ref_values = ref.to_numpy(dtype=float)
        comp_values = comp.to_numpy(dtype=float)

        def average_tie_ranks(values: np.ndarray) -> np.ndarray:
            order = np.argsort(values, kind="stable")
            ranked = np.empty(len(values), dtype=float)
            start = 0
            while start < len(values):
                end = start + 1
                while end < len(values) and values[order[end]] == values[order[start]]:
                    end += 1
                ranked[order[start:end]] = ((start + 1) + end) / 2.0
                start = end
            return ranked

        rho = float(
            np.corrcoef(
                average_tie_ranks(ref_values), average_tie_ranks(comp_values)
            )[0, 1]
        )
        concordant = discordant = tied_ref_only = tied_comp_only = 0
        for left in range(len(ref_values) - 1):
            for right in range(left + 1, len(ref_values)):
                ref_sign = np.sign(ref_values[left] - ref_values[right])
                comp_sign = np.sign(comp_values[left] - comp_values[right])
                if ref_sign == 0 and comp_sign == 0:
                    continue
                if ref_sign == 0:
                    tied_ref_only += 1
                elif comp_sign == 0:
                    tied_comp_only += 1
                elif ref_sign == comp_sign:
                    concordant += 1
                else:
                    discordant += 1
        denominator = np.sqrt(
            (concordant + discordant + tied_ref_only)
            * (concordant + discordant + tied_comp_only)
        )
        tau = (
            (concordant - discordant) / denominator
            if denominator > 0
            else np.nan
        )
    reference_top = sorted(reference.loc[reference["priority_rank"] == 1, "asset_id"].tolist())
    comparison_top = sorted(comparison.loc[comparison["priority_rank"] == 1, "asset_id"].tolist())
    return {
        "spearman_rho": float(rho) if not np.isnan(rho) else None,
        "kendall_tau": float(tau) if not np.isnan(tau) else None,
        "exact_rank_agreement": int(np.array_equal(ref.to_numpy(), comp.to_numpy())),
        "top_rank_agreement": int(reference_top == comparison_top),
        "reference_top": ",".join(reference_top),
        "comparison_top": ",".join(comparison_top),
    }


def compare_with_baselines(
    scored: pd.DataFrame,
    repetition: int,
    seed: int,
    design: str,
) -> list[dict]:
    rows: list[dict] = []
    for baseline_name, rank_column in (
        ("rul_only", "rul_only_rank"),
        ("criticality_only", "criticality_only_rank"),
    ):
        baseline = scored.copy()
        baseline["priority_rank"] = baseline[rank_column]
        comparison = rank_comparison(scored, baseline)
        comparison.update(
            {
                "repetition": repetition,
                "assignment_seed": seed,
                "assignment_design": design,
                "baseline": baseline_name,
            }
        )
        rows.append(comparison)
    return rows


def adjacent_score_sensitivity(
    scenario: pd.DataFrame,
    reference: pd.DataFrame,
    repetition: int,
    include_rankings: bool = False,
) -> tuple[list[dict], list[pd.DataFrame]]:
    comparisons: list[dict] = []
    rankings: list[pd.DataFrame] = []
    seed = int(scenario["assignment_seed"].iloc[0])
    for asset_index, asset in scenario.iterrows():
        for dimension in SCORE_DIMENSIONS:
            base_value = int(asset[dimension])
            for delta in (-1, 1):
                alternative_value = base_value + delta
                if not 1 <= alternative_value <= 5:
                    continue
                alternative_scenario = scenario.copy()
                alternative_scenario.loc[asset_index, dimension] = alternative_value
                alternative = score_assets(alternative_scenario)
                scenario_id = (
                    f"{asset['asset_id']}_{dimension}_{base_value}_to_{alternative_value}"
                )
                comparison = rank_comparison(reference, alternative)
                comparison.update(
                    {
                        "repetition": repetition,
                        "assignment_seed": seed,
                        "scenario_id": scenario_id,
                        "asset_id_changed": asset["asset_id"],
                        "dimension_changed": dimension,
                        "base_score": base_value,
                        "alternative_score": alternative_value,
                        "delta": delta,
                    }
                )
                comparisons.append(comparison)
                if include_rankings:
                    ranked = alternative.copy()
                    ranked.insert(0, "scenario_id", scenario_id)
                    ranked.insert(1, "dimension_changed", dimension)
                    ranked.insert(2, "base_score", base_value)
                    ranked.insert(3, "alternative_score", alternative_value)
                    rankings.append(ranked)
    return comparisons, rankings


def controlled_checks() -> dict:
    rul_grid = np.array([0.0, 25.0, 50.0, 75.0, 100.0, 125.0, 150.0])
    urgency = np.clip(1.0 - rul_grid / BASE_HORIZON, 0.0, 1.0)
    monotonic_urgency = bool(np.all(np.diff(urgency) <= 1e-12))

    equal_rul = ASSETS.copy()
    equal_rul["surrogate_rul_input"] = 50.0
    equal_rul_scored = score_assets(equal_rul)
    consequence_rank = equal_rul_scored["combined_consequence"].rank(
        method="min", ascending=False
    ).astype(int)
    equal_rul_consequence_order = bool(
        np.array_equal(consequence_rank.to_numpy(), equal_rul_scored["priority_rank"].to_numpy())
    )

    equal_consequence = ASSETS.copy()
    equal_consequence[list(SCORE_DIMENSIONS)] = 3
    equal_consequence["surrogate_rul_input"] = [20.0, 40.0, 60.0, 80.0, 100.0]
    equal_consequence_scored = score_assets(equal_consequence)
    expected_rank = equal_consequence["surrogate_rul_input"].rank(
        method="min", ascending=True
    ).astype(int)
    equal_consequence_rul_order = bool(
        np.array_equal(expected_rank.to_numpy(), equal_consequence_scored["priority_rank"].to_numpy())
    )

    dominance = {}
    for dimension in SCORE_DIMENSIONS:
        test = pd.DataFrame(
            {
                "asset_id": [f"D{x}" for x in range(1, 6)],
                "surrogate_rul_input": [50.0] * 5,
                "criticality": [3] * 5,
                "throughput": [3] * 5,
                "severity": [3] * 5,
            }
        )
        test[dimension] = [1, 2, 3, 4, 5]
        values = score_assets(test)["priority_score"].to_numpy()
        dominance[dimension] = bool(np.all(np.diff(values) >= -1e-12))

    checks = {
        "weights_sum_to_one": bool(np.isclose(sum(BASE_WEIGHTS.values()), 1.0)),
        "urgency_nonincreasing_as_surrogate_rul_increases": monotonic_urgency,
        "equal_surrogate_rul_priority_follows_consequence": equal_rul_consequence_order,
        "equal_consequence_priority_follows_shorter_surrogate_rul": equal_consequence_rul_order,
        "component_dominance": dominance,
    }
    if not all(
        [
            checks["weights_sum_to_one"],
            monotonic_urgency,
            equal_rul_consequence_order,
            equal_consequence_rul_order,
            *dominance.values(),
        ]
    ):
        raise AssertionError(f"Controlled behavioural check failed: {checks}")
    return checks


def run_seeded_assignments(
    pool: pd.DataFrame,
    design: str,
    include_parameter_and_score_sensitivity: bool,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows: list[pd.DataFrame] = []
    baseline_comparisons: list[dict] = []
    parameter_comparisons: list[dict] = []
    score_comparisons: list[dict] = []

    for repetition in range(1, ASSIGNMENT_REPETITIONS + 1):
        seed = MASTER_SEED + repetition - 1
        scenario = build_assignment(pool, seed=seed, design=design)
        scored = score_assets(scenario)
        scored.insert(0, "repetition", repetition)
        rows.append(scored)
        baseline_comparisons.extend(
            compare_with_baselines(scored, repetition, seed, design)
        )

        if include_parameter_and_score_sensitivity:
            for horizon in (100.0, 125.0, 150.0):
                for scheme_name, weights in WEIGHT_SCHEMES.items():
                    alternative = score_assets(scenario, horizon=horizon, weights=weights)
                    sensitivity = rank_comparison(scored, alternative)
                    sensitivity.update(
                        {
                            "repetition": repetition,
                            "assignment_seed": seed,
                            "planning_horizon": horizon,
                            "weight_scheme": scheme_name,
                        }
                    )
                    parameter_comparisons.append(sensitivity)
            adjacent, _ = adjacent_score_sensitivity(
                scenario, scored, repetition=repetition, include_rankings=False
            )
            score_comparisons.extend(adjacent)

    all_rows = pd.concat(rows, ignore_index=True)
    summary = (
        all_rows.groupby(["asset_id", "asset_role"], as_index=False)
        .agg(
            mean_surrogate_rul_input=("surrogate_rul_input", "mean"),
            mean_priority=("priority_score", "mean"),
            sd_priority=("priority_score", "std"),
            mean_rank=("priority_rank", "mean"),
            sd_rank=("priority_rank", "std"),
            rank_1_probability=("priority_rank", lambda x: float(np.mean(x == 1))),
        )
        .sort_values("mean_rank", ignore_index=True)
    )
    return (
        all_rows,
        summary,
        pd.DataFrame(baseline_comparisons),
        pd.DataFrame(parameter_comparisons),
        pd.DataFrame(score_comparisons),
    )


def monte_carlo_noise(
    base_assignment: pd.DataFrame,
    centred_prediction_errors: np.ndarray,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    base_scored = score_assets(base_assignment)
    rows: list[pd.DataFrame] = []
    comparison_rows: list[dict] = []

    for repetition in range(1, NOISE_REPETITIONS + 1):
        seed = MASTER_SEED + 100_000 + repetition - 1
        rng = np.random.default_rng(seed)
        sampled_error = rng.choice(
            centred_prediction_errors, size=len(base_assignment), replace=True
        )
        scenario = base_assignment.copy()
        scenario["noise_seed"] = seed
        scenario["sampled_cmapss_prediction_error"] = sampled_error
        scenario["perturbed_surrogate_rul_input"] = np.maximum(
            scenario["surrogate_rul_input"] + sampled_error, 0.0
        )
        scored = score_assets(scenario, rul_column="perturbed_surrogate_rul_input")
        scored.insert(0, "repetition", repetition)
        rows.append(scored)
        comparison = rank_comparison(base_scored, scored)
        comparison.update({"repetition": repetition, "noise_seed": seed})
        comparison_rows.append(comparison)

    all_rows = pd.concat(rows, ignore_index=True)
    summary = (
        all_rows.groupby(["asset_id", "asset_role"], as_index=False)
        .agg(
            mean_perturbed_surrogate_rul=("perturbed_surrogate_rul_input", "mean"),
            mean_priority=("priority_score", "mean"),
            sd_priority=("priority_score", "std"),
            mean_rank=("priority_rank", "mean"),
            sd_rank=("priority_rank", "std"),
            rank_1_probability=("priority_rank", lambda x: float(np.mean(x == 1))),
        )
        .sort_values("mean_rank", ignore_index=True)
    )
    return all_rows, summary, pd.DataFrame(comparison_rows)


def aggregate_comparisons(frame: pd.DataFrame) -> dict:
    return {
        "mean_spearman_rho": float(frame["spearman_rho"].dropna().mean()),
        "mean_kendall_tau": float(frame["kendall_tau"].dropna().mean()),
        "exact_rank_agreement_probability": float(frame["exact_rank_agreement"].mean()),
        "top_rank_agreement_probability": float(frame["top_rank_agreement"].mean()),
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    predictions = pd.read_csv(PREDICTION_PATH)
    oof = pd.read_csv(OOF_PATH)
    pool, quantile_boundaries = prepare_prediction_pool(predictions)

    base_assignment = build_assignment(
        pool, seed=MASTER_SEED, design="quintile_stratified"
    )
    base_scored = score_assets(base_assignment).sort_values(
        "priority_rank", ignore_index=True
    )
    base_scored.to_csv(
        OUTPUT_DIR / "warehouse_base_mapping_and_ranking.csv", index=False
    )

    base_baseline_rows = compare_with_baselines(
        base_scored, repetition=1, seed=MASTER_SEED, design="quintile_stratified"
    )
    base_baselines = {row["baseline"]: row for row in base_baseline_rows}

    sensitivity_frames: list[pd.DataFrame] = []
    sensitivity_summary: list[dict] = []
    for horizon in (100.0, 125.0, 150.0):
        for scheme_name, weights in WEIGHT_SCHEMES.items():
            scored = score_assets(base_assignment, horizon=horizon, weights=weights)
            scored.insert(0, "weight_scheme", scheme_name)
            scored.insert(0, "planning_horizon", horizon)
            sensitivity_frames.append(scored)
            comparison = rank_comparison(base_scored, scored)
            comparison.update({"planning_horizon": horizon, "weight_scheme": scheme_name})
            sensitivity_summary.append(comparison)
    pd.concat(sensitivity_frames, ignore_index=True).to_csv(
        OUTPUT_DIR / "warehouse_sensitivity_rankings.csv", index=False
    )
    pd.DataFrame(sensitivity_summary).to_csv(
        OUTPUT_DIR / "warehouse_sensitivity_summary.csv", index=False
    )

    ablation_frames: list[pd.DataFrame] = []
    ablation_summary: list[dict] = []
    for scheme_name, weights in ABLATION_SCHEMES.items():
        scored = score_assets(base_assignment, weights=weights)
        scored.insert(0, "ablation_scheme", scheme_name)
        ablation_frames.append(scored)
        comparison = rank_comparison(base_scored, scored)
        comparison["ablation_scheme"] = scheme_name
        ablation_summary.append(comparison)
    pd.concat(ablation_frames, ignore_index=True).to_csv(
        OUTPUT_DIR / "warehouse_ablation_rankings.csv", index=False
    )
    pd.DataFrame(ablation_summary).to_csv(
        OUTPUT_DIR / "warehouse_ablation_summary.csv", index=False
    )

    base_score_comparisons, base_score_rankings = adjacent_score_sensitivity(
        base_assignment, base_scored, repetition=1, include_rankings=True
    )
    pd.concat(base_score_rankings, ignore_index=True).to_csv(
        OUTPUT_DIR / "warehouse_score_sensitivity_rankings.csv", index=False
    )
    pd.DataFrame(base_score_comparisons).to_csv(
        OUTPUT_DIR / "warehouse_score_sensitivity_summary.csv", index=False
    )

    (
        mapping_rows,
        mapping_summary,
        mapping_baseline_comparisons,
        mapping_parameter_comparisons,
        mapping_score_comparisons,
    ) = run_seeded_assignments(
        pool,
        design="quintile_stratified",
        include_parameter_and_score_sensitivity=True,
    )
    mapping_rows.to_csv(
        OUTPUT_DIR / "warehouse_mapping_monte_carlo_rows.csv", index=False
    )
    mapping_summary.to_csv(
        OUTPUT_DIR / "warehouse_mapping_monte_carlo_summary.csv", index=False
    )
    mapping_baseline_comparisons.loc[
        mapping_baseline_comparisons["baseline"] == "rul_only"
    ].to_csv(
        OUTPUT_DIR / "warehouse_mapping_vs_rul_only_stability.csv", index=False
    )
    mapping_baseline_comparisons.loc[
        mapping_baseline_comparisons["baseline"] == "criticality_only"
    ].to_csv(
        OUTPUT_DIR / "warehouse_mapping_vs_criticality_only_stability.csv", index=False
    )
    mapping_parameter_comparisons.to_csv(
        OUTPUT_DIR / "warehouse_mapping_sensitivity_stability.csv", index=False
    )
    mapping_parameter_aggregate = (
        mapping_parameter_comparisons.groupby(
            ["planning_horizon", "weight_scheme"], as_index=False
        )
        .agg(
            mean_spearman_rho=("spearman_rho", "mean"),
            mean_kendall_tau=("kendall_tau", "mean"),
            exact_rank_agreement_probability=("exact_rank_agreement", "mean"),
            top_rank_agreement_probability=("top_rank_agreement", "mean"),
        )
    )
    mapping_parameter_aggregate.to_csv(
        OUTPUT_DIR / "warehouse_mapping_sensitivity_summary.csv", index=False
    )
    mapping_score_comparisons.to_csv(
        OUTPUT_DIR / "warehouse_score_sensitivity_stability.csv", index=False
    )
    mapping_score_aggregate = (
        mapping_score_comparisons.groupby(
            ["dimension_changed", "delta"], as_index=False
        )
        .agg(
            comparisons=("scenario_id", "count"),
            mean_spearman_rho=("spearman_rho", "mean"),
            mean_kendall_tau=("kendall_tau", "mean"),
            exact_rank_agreement_probability=("exact_rank_agreement", "mean"),
            top_rank_agreement_probability=("top_rank_agreement", "mean"),
        )
    )
    mapping_score_aggregate.to_csv(
        OUTPUT_DIR / "warehouse_score_sensitivity_stability_summary.csv", index=False
    )

    (
        unstratified_rows,
        unstratified_summary,
        unstratified_baselines,
        _,
        _,
    ) = run_seeded_assignments(
        pool,
        design="unstratified_random",
        include_parameter_and_score_sensitivity=False,
    )
    unstratified_rows.to_csv(
        OUTPUT_DIR / "warehouse_unstratified_assignment_rows.csv", index=False
    )
    unstratified_summary.to_csv(
        OUTPUT_DIR / "warehouse_unstratified_assignment_summary.csv", index=False
    )
    all_design_baselines = pd.concat(
        [mapping_baseline_comparisons, unstratified_baselines], ignore_index=True
    )
    assignment_design_summary = (
        all_design_baselines.groupby(["assignment_design", "baseline"], as_index=False)
        .agg(
            mean_spearman_rho=("spearman_rho", "mean"),
            mean_kendall_tau=("kendall_tau", "mean"),
            exact_rank_agreement_probability=("exact_rank_agreement", "mean"),
            top_rank_agreement_probability=("top_rank_agreement", "mean"),
        )
    )
    assignment_design_summary.to_csv(
        OUTPUT_DIR / "warehouse_assignment_design_sensitivity_summary.csv", index=False
    )

    prediction_error = (
        oof["gradient_boosting_oof_prediction"].to_numpy()
        - oof["rul_target"].to_numpy()
    )
    centred_error = prediction_error - prediction_error.mean()
    noise_rows, noise_summary, noise_comparisons = monte_carlo_noise(
        base_assignment, centred_error
    )
    noise_rows.to_csv(
        OUTPUT_DIR / "warehouse_noise_monte_carlo_rows.csv", index=False
    )
    noise_summary.to_csv(
        OUTPUT_DIR / "warehouse_noise_monte_carlo_summary.csv", index=False
    )
    noise_comparisons.to_csv(
        OUTPUT_DIR / "warehouse_noise_rank_stability.csv", index=False
    )

    checks = controlled_checks()
    with (OUTPUT_DIR / "warehouse_controlled_checks.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(checks, handle, indent=2)

    stratified_rul = mapping_baseline_comparisons.loc[
        mapping_baseline_comparisons["baseline"] == "rul_only"
    ]
    stratified_criticality = mapping_baseline_comparisons.loc[
        mapping_baseline_comparisons["baseline"] == "criticality_only"
    ]
    score_sensitivity_overall = aggregate_comparisons(mapping_score_comparisons)
    noise_stability = aggregate_comparisons(noise_comparisons)
    base_top = base_scored.loc[base_scored["priority_rank"] == 1, "asset_id"].tolist()

    summary = {
        "run_timestamp_local": pd.Timestamp.now().isoformat(),
        "methodological_description": (
            "digital-twin-inspired maintenance decision-support simulation"
        ),
        "transfer_boundary": (
            "C-MAPSS predictions are surrogate degradation inputs only and are not "
            "warehouse-asset RUL predictions"
        ),
        "master_seed": MASTER_SEED,
        "assignment_seed_sequence": {
            "first": MASTER_SEED,
            "last": MASTER_SEED + ASSIGNMENT_REPETITIONS - 1,
            "repetitions": ASSIGNMENT_REPETITIONS,
        },
        "assignment_design": (
            "one C-MAPSS endpoint prediction sampled from each empirical quintile, "
            "then seeded permutation across five virtual assets"
        ),
        "surrogate_rul_quantile_boundaries": quantile_boundaries,
        "assignment_design_sensitivity": assignment_design_summary.to_dict("records"),
        "base_horizon": BASE_HORIZON,
        "base_weights": BASE_WEIGHTS,
        "base_weights_sum": float(sum(BASE_WEIGHTS.values())),
        "base_source_unit_ids_in_asset_order": {
            row.asset_id: int(row.source_cmapss_unit_id)
            for row in base_assignment.itertuples(index=False)
        },
        "base_top_ranked_assets": base_top,
        "base_baseline_comparisons": base_baselines,
        "seeded_assignment_rul_only_comparison": aggregate_comparisons(stratified_rul),
        "seeded_assignment_criticality_only_comparison": aggregate_comparisons(
            stratified_criticality
        ),
        "score_sensitivity_criterion": (
            "each author-assigned score is moved one adjacent anchor down or up, "
            "bounded to the 1-5 scale"
        ),
        "score_sensitivity_overall": score_sensitivity_overall,
        "noise_repetitions": NOISE_REPETITIONS,
        "noise_seed_sequence": {
            "first": MASTER_SEED + 100_000,
            "last": MASTER_SEED + 100_000 + NOISE_REPETITIONS - 1,
        },
        "noise_error_source": (
            "centred Gradient Boosting grouped out-of-fold C-MAPSS prediction errors"
        ),
        "noise_error_sd_cycles": float(np.std(centred_error, ddof=1)),
        "noise_rank_stability": noise_stability,
        "controlled_checks": checks,
        "software": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
        },
        "input_hashes": {
            str(PREDICTION_PATH.relative_to(WORKSPACE)): sha256(PREDICTION_PATH),
            str(OOF_PATH.relative_to(WORKSPACE)): sha256(OOF_PATH),
            str(PROTOCOL_PATH.relative_to(WORKSPACE)): sha256(PROTOCOL_PATH),
        },
        "script_sha256": sha256(Path(__file__)),
    }
    with (OUTPUT_DIR / "warehouse_ranking_summary.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    readable = [
        "# Digital-Twin-Inspired Warehouse Maintenance Decision-Support Simulation Results",
        "",
        (
            "Base specification: C-MAPSS predictions used only as surrogate degradation "
            "inputs; one value from each empirical quintile; assignment seed 42; "
            "H=125 abstract cycles; equal consequence weights."
        ),
        "",
        "## Base ranking",
        "",
        (
            "| Rank | Asset | C-MAPSS source unit | Surrogate RUL input | Quantile | "
            "Urgency | Consequence | Priority | RUL-only rank | Criticality-only rank |"
        ),
        "|---:|---|---:|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in base_scored.itertuples(index=False):
        readable.append(
            f"| {row.priority_rank} | {row.asset_id} {row.asset_role} | "
            f"{int(row.source_cmapss_unit_id)} | {row.surrogate_rul_input:.3f} | "
            f"{row.surrogate_rul_quantile} | {row.rul_urgency:.3f} | "
            f"{row.combined_consequence:.3f} | {row.priority_score:.3f} | "
            f"{row.rul_only_rank} | {row.criticality_only_rank} |"
        )
    rul_metrics = summary["seeded_assignment_rul_only_comparison"]
    criticality_metrics = summary["seeded_assignment_criticality_only_comparison"]
    readable.extend(
        [
            "",
            "## Behaviour and sensitivity summary",
            "",
            (
                "- Across 1,000 quintile-stratified seeded assignments, exact agreement "
                f"with RUL-only ranking: {rul_metrics['exact_rank_agreement_probability']:.3f}; "
                f"top-rank agreement: {rul_metrics['top_rank_agreement_probability']:.3f}."
            ),
            (
                "- Across the same assignments, exact agreement with criticality-only ranking: "
                f"{criticality_metrics['exact_rank_agreement_probability']:.3f}; top-rank "
                f"agreement: {criticality_metrics['top_rank_agreement_probability']:.3f}."
            ),
            (
                "- Adjacent-score sensitivity across all seeded assignments: exact-rank "
                f"agreement {score_sensitivity_overall['exact_rank_agreement_probability']:.3f}; "
                f"top-rank agreement {score_sensitivity_overall['top_rank_agreement_probability']:.3f}."
            ),
            (
                "- Prediction-noise robustness: mean Spearman rho "
                f"{noise_stability['mean_spearman_rho']:.3f}; top-rank agreement "
                f"{noise_stability['top_rank_agreement_probability']:.3f}."
            ),
            "- All controlled monotonicity, dominance and weight-sum checks: PASS.",
            "",
            (
                "These outputs evaluate C-MAPSS model performance and the internal behaviour of "
                "an assumption-based prioritisation method. They do not validate warehouse RUL, "
                "real-world warehouse risk or operational maintenance effectiveness."
            ),
        ]
    )
    (OUTPUT_DIR / "warehouse_results_summary.md").write_text(
        "\n".join(readable) + "\n", encoding="utf-8"
    )
    print("\n".join(readable))


if __name__ == "__main__":
    main()
