"""Regression tests for the basic priority dashboard."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PACKAGE_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dashboard_logic import (  # noqa: E402
    BASE_HORIZON,
    BASE_RANKING_PATH,
    calculate_dashboard_priorities,
    dashboard_snapshot,
    export_dashboard_table,
    load_base_dashboard_inputs,
)


class DashboardLogicTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inputs = load_base_dashboard_inputs()

    def test_base_case_matches_authoritative_output(self) -> None:
        actual = calculate_dashboard_priorities(self.inputs).sort_values("asset_id")
        expected = pd.read_csv(BASE_RANKING_PATH).sort_values("asset_id")
        self.assertListEqual(
            actual["priority_rank"].tolist(), expected["priority_rank"].tolist()
        )
        self.assertTrue(
            np.allclose(actual["priority_score"], expected["priority_score"])
        )

    def test_shorter_input_can_change_the_leading_asset(self) -> None:
        changed = self.inputs.copy()
        changed.loc[changed["asset_id"] == "A2", "surrogate_rul_input"] = 0.0
        scored = calculate_dashboard_priorities(changed)
        snapshot = dashboard_snapshot(scored)
        self.assertEqual(snapshot["top_assets"], ["A2"])

    def test_input_at_horizon_has_zero_priority(self) -> None:
        changed = self.inputs.copy()
        changed.loc[changed["asset_id"] == "A1", "surrogate_rul_input"] = BASE_HORIZON
        scored = calculate_dashboard_priorities(changed)
        row = scored.loc[scored["asset_id"] == "A1"].iloc[0]
        self.assertEqual(row["rul_urgency"], 0.0)
        self.assertEqual(row["priority_score"], 0.0)

    def test_negative_surrogate_input_is_rejected(self) -> None:
        changed = self.inputs.copy()
        changed.loc[0, "surrogate_rul_input"] = -1.0
        with self.assertRaisesRegex(ValueError, "non-negative"):
            calculate_dashboard_priorities(changed)

    def test_export_contains_auditable_columns(self) -> None:
        scored = calculate_dashboard_priorities(self.inputs)
        exported = export_dashboard_table(scored)
        self.assertEqual(len(exported), 5)
        self.assertListEqual(exported["priority_rank"].tolist(), [1, 2, 3, 4, 5])


if __name__ == "__main__":
    unittest.main()
