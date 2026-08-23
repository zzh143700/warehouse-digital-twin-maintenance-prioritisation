"""Basic interactive dashboard for the conceptual warehouse digital twin."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PACKAGE_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dashboard_logic import (  # noqa: E402
    BASE_HORIZON,
    calculate_dashboard_priorities,
    dashboard_snapshot,
    export_dashboard_table,
    load_base_dashboard_inputs,
)


RANK_LABELS = {
    1: "Top 1",
    2: "Rank 2",
    3: "Rank 3",
    4: "Rank 4",
    5: "Rank 5",
}
RANK_COLORS = {
    1: "#c62828",  # red: highest current priority
    2: "#ef6c00",  # orange
    3: "#f9a825",  # amber
    4: "#2f80ed",  # blue
    5: "#78909c",  # grey
}
RANK_MARKERS = {
    1: "🔴 Top 1",
    2: "🟠 Rank 2",
    3: "🟡 Rank 3",
    4: "🔵 Rank 4",
    5: "⚪ Rank 5",
}


st.set_page_config(
    page_title="Warehouse Maintenance Priority Dashboard",
    page_icon="🏭",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {max-width: 1180px; padding-top: 2rem; padding-bottom: 3rem;}
    [data-testid="stMetric"] {
        border-top: 3px solid #0f766e;
        padding: 0.8rem 0.9rem 0.45rem 0.9rem;
        background: rgba(15, 118, 110, 0.06);
    }
    [data-testid="stMetricLabel"] {font-weight: 600;}
    .dashboard-kicker {
        color: #0f766e;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.25rem;
    }
    .dashboard-caption {color: #52606d; margin-top: -0.35rem; margin-bottom: 1.25rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def get_base_inputs() -> pd.DataFrame:
    return load_base_dashboard_inputs()


def reset_dashboard() -> None:
    st.session_state["editor_generation"] = st.session_state.get(
        "editor_generation", 0
    ) + 1
    st.session_state["planning_horizon"] = int(BASE_HORIZON)


base_inputs = get_base_inputs()
st.session_state.setdefault("editor_generation", 0)
st.session_state.setdefault("planning_horizon", int(BASE_HORIZON))

st.markdown('<div class="dashboard-kicker">Conceptual warehouse digital twin</div>', unsafe_allow_html=True)
st.title("Warehouse Maintenance Priority Dashboard")
st.markdown(
    '<div class="dashboard-caption">Interactive decision-support prototype using the dissertation base scenario.</div>',
    unsafe_allow_html=True,
)

st.info(
    "C-MAPSS model outputs are used here only as surrogate degradation inputs. "
    "The dashboard recalculates priorities immediately after an input change, "
    "but it is not connected to live warehouse sensors and does not issue "
    "operational maintenance instructions."
)

with st.sidebar:
    st.header("Scenario controls")
    horizon = st.slider(
        "Planning horizon, H (abstract cycles)",
        min_value=50,
        max_value=200,
        step=5,
        key="planning_horizon",
        help="Inputs at or above H receive zero urgency for the current window.",
    )
    st.caption("Consequence weights remain equal, as in the base specification.")
    st.button("Reset base case", on_click=reset_dashboard, use_container_width=True)

st.subheader("Current surrogate degradation inputs")
st.caption(
    "Edit the surrogate RUL input column. The priority ranking refreshes "
    "immediately; consequence scores remain fixed author-defined scenario inputs."
)

editor_key = f"asset_input_editor_{st.session_state['editor_generation']}"
edited_inputs = st.data_editor(
    base_inputs,
    key=editor_key,
    use_container_width=True,
    height=245,
    hide_index=True,
    num_rows="fixed",
    disabled=[
        "asset_id",
        "asset_role",
        "criticality",
        "capacity_loss_percent",
        "throughput",
        "severity",
    ],
    column_order=[
        "asset_id",
        "asset_role",
        "surrogate_rul_input",
        "criticality",
        "throughput",
        "severity",
    ],
    column_config={
        "asset_id": st.column_config.TextColumn("Asset", width="small"),
        "asset_role": st.column_config.TextColumn("Warehouse role", width="medium"),
        "surrogate_rul_input": st.column_config.NumberColumn(
            "Surrogate RUL input",
            help="Non-negative C-MAPSS-derived scenario input, in abstract cycles.",
            min_value=0.0,
            step=1.0,
            format="%.1f",
            width="medium",
        ),
        "criticality": st.column_config.NumberColumn(
            "Criticality", format="%d", width="small"
        ),
        "throughput": st.column_config.NumberColumn(
            "Throughput", format="%d", width="small"
        ),
        "severity": st.column_config.NumberColumn(
            "Severity", format="%d", width="small"
        ),
    },
)

try:
    scored = calculate_dashboard_priorities(edited_inputs, horizon=float(horizon))
except (ValueError, FileNotFoundError) as exc:
    st.error(str(exc))
    st.stop()

snapshot = dashboard_snapshot(scored)
top_rows = scored.loc[scored["asset_id"].isin(snapshot["top_assets"])]
top_label = ", ".join(
    f"{row.asset_id} — {row.asset_role}" for row in top_rows.itertuples(index=False)
)
updated_at = datetime.now().astimezone().strftime("%d %b %Y, %H:%M:%S %Z")

metric_columns = st.columns(3)
metric_columns[0].metric("Current top-priority asset", ", ".join(snapshot["top_assets"]))
metric_columns[1].metric("Priority score", f"{snapshot['top_score']:.2f}")
metric_columns[2].metric(
    "Active assets",
    f"{snapshot['active_assets']} of {snapshot['total_assets']}",
)
st.caption(f"Top-ranked role: {top_label} · Last recalculated: {updated_at}")

chart_column, table_column = st.columns([0.9, 1.4], gap="large")

with chart_column:
    st.subheader("Priority by asset")
    chart_data = scored[
        ["asset_id", "asset_role", "priority_rank", "priority_score"]
    ].copy()
    chart_data["rank_label"] = (
        chart_data["priority_rank"].astype(int).map(RANK_LABELS)
    )
    base_chart = (
        alt.Chart(chart_data)
        .mark_bar()
        .encode(
            x=alt.X(
                "priority_score:Q",
                title="Priority score",
                scale=alt.Scale(domain=[0, 100]),
            ),
            y=alt.Y(
                "asset_id:N",
                title="Asset",
                sort=alt.EncodingSortField(
                    field="priority_rank", order="ascending"
                ),
            ),
            color=alt.Color(
                "rank_label:N",
                title="Priority rank",
                scale=alt.Scale(
                    domain=list(RANK_LABELS.values()),
                    range=list(RANK_COLORS.values()),
                ),
                legend=alt.Legend(
                    orient="bottom",
                    direction="horizontal",
                    columns=3,
                    title=None,
                ),
            ),
            tooltip=[
                alt.Tooltip("asset_id:N", title="Asset"),
                alt.Tooltip("asset_role:N", title="Warehouse role"),
                alt.Tooltip("priority_rank:Q", title="Rank", format=".0f"),
                alt.Tooltip("priority_score:Q", title="Priority score", format=".3f"),
            ],
        )
    )
    value_labels = (
        alt.Chart(chart_data)
        .mark_text(align="left", baseline="middle", dx=4, color="#172033")
        .encode(
            x=alt.X("priority_score:Q"),
            y=alt.Y(
                "asset_id:N",
                sort=alt.EncodingSortField(
                    field="priority_rank", order="ascending"
                ),
            ),
            text=alt.Text("priority_score:Q", format=".1f"),
        )
    )
    st.altair_chart(
        (base_chart + value_labels).properties(height=315),
        use_container_width=True,
    )
    st.caption(
        "Red marks the current Top 1 asset; colour and rank labels are both "
        "provided so that priority is not communicated by colour alone."
    )

with table_column:
    st.subheader("Current priority ranking")
    display_table = export_dashboard_table(scored)[
        [
            "priority_rank",
            "asset_id",
            "priority_score",
            "surrogate_rul_input",
        ]
    ].rename(
        columns={
            "priority_rank": "Rank",
            "asset_id": "Asset",
            "surrogate_rul_input": "Surrogate input",
            "priority_score": "Priority score",
        }
    )
    display_table.insert(
        0,
        "Priority level",
        display_table["Rank"].astype(int).map(RANK_MARKERS),
    )
    display_table = display_table.drop(columns="Rank")
    st.dataframe(
        display_table,
        use_container_width=True,
        height=260,
        hide_index=True,
        column_config={
            "Priority level": st.column_config.TextColumn(width="medium"),
            "Asset": st.column_config.TextColumn(width="small"),
            "Priority score": st.column_config.NumberColumn(
                width="small", format="%.3f"
            ),
            "Surrogate input": st.column_config.NumberColumn(
                width="small", format="%.1f"
            ),
        },
    )
    st.caption("Urgency, consequence and role fields are retained in the CSV export.")

csv_bytes = export_dashboard_table(scored).to_csv(index=False).encode("utf-8")
st.download_button(
    "Download current ranking (CSV)",
    data=csv_bytes,
    file_name="current_warehouse_priority_ranking.csv",
    mime="text/csv",
)

with st.expander("How the priority is calculated"):
    st.markdown(
        r"""
        The dashboard applies the dissertation's author-developed equation:

        $$U_i = \max\left(0, 1 - \frac{R_i}{H}\right)$$

        $$K_i = \frac{1}{3}\frac{C_i}{5} + \frac{1}{3}\frac{T_i}{5} + \frac{1}{3}\frac{S_i}{5}$$

        $$P_i = 100 \times U_i \times K_i$$

        $R_i$ is the surrogate degradation input, $H$ is the selected planning
        horizon, and $C_i$, $T_i$ and $S_i$ are the author-assigned criticality,
        throughput and severity scores. $P_i$ is a relative priority index, not
        a calibrated failure probability or a standard risk-priority number.
        """
    )

st.caption(
    "Author's own interactive implementation. Base data: seed-42 conceptual "
    "warehouse scenario derived from C-MAPSS FD001 predictions."
)
