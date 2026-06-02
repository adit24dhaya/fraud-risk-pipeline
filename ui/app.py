import os
from html import escape
from typing import Any

import requests
import streamlit as st


DEFAULT_API_URL = os.getenv("FRAUD_API_URL", "http://localhost:8000")

SCENARIOS: dict[str, dict[str, Any]] = {
    "Low friction": {
        "TransactionAmt": 24.50,
        "TransactionDT": 3_600,
        "ProductCD": "W",
        "card1": 1_000,
        "hour": 1,
    },
    "Review edge": {
        "TransactionAmt": 250.00,
        "TransactionDT": 7_500_000,
        "ProductCD": "W",
        "card1": 12_345,
        "hour": 23,
    },
    "High value": {
        "TransactionAmt": 1_250.00,
        "TransactionDT": 12_345_678,
        "ProductCD": "C",
        "card1": 17_000,
        "hour": 3,
    },
}


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #eef2f7;
            --panel: #ffffff;
            --border: #d7dee8;
            --text: #18212f;
            --muted: #5e6b7d;
            --red: #b42318;
            --amber: #b45309;
            --green: #047857;
            --blue: #1d4ed8;
            --blue-hover: #1e40af;
        }

        .stApp {
            background: var(--bg);
            color: var(--text);
        }

        [data-testid="stHeader"] {
            background: rgba(238, 242, 247, 0.95);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
        }

        [data-testid="stSidebar"] * {
            color: #f1f5f9;
        }

        [data-testid="stSidebar"] input {
            background: #ffffff;
            color: #18212f;
            border-radius: 6px;
        }

        .sidebar-status {
            margin-top: 14px;
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 10px;
            padding: 14px 16px;
            background: rgba(255, 255, 255, 0.05);
        }

        .sidebar-status-label {
            color: #94a3b8;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .sidebar-status-value {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #ffffff;
            font-size: 1.05rem;
            font-weight: 700;
            margin-top: 6px;
        }

        .status-dot {
            width: 9px;
            height: 9px;
            border-radius: 50%;
            flex-shrink: 0;
        }

        .status-dot-online {
            background: #34d399;
            box-shadow: 0 0 0 3px rgba(52, 211, 153, 0.25);
        }

        .status-dot-offline {
            background: #f87171;
            box-shadow: 0 0 0 3px rgba(248, 113, 113, 0.25);
        }

        .block-container {
            padding-top: 1.6rem;
            padding-bottom: 2.5rem;
            max-width: 1320px;
        }

        .workbench-header {
            display: flex;
            align-items: end;
            justify-content: space-between;
            gap: 20px;
            margin-bottom: 18px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 16px;
        }

        .workbench-header h1 {
            margin: 0;
            color: var(--text);
            font-size: 2.1rem;
            line-height: 1.1;
            letter-spacing: -0.02em;
        }

        .workbench-subtitle {
            color: var(--muted);
            font-size: 0.95rem;
            margin-top: 8px;
            max-width: 42rem;
            line-height: 1.45;
        }

        .eyebrow {
            color: var(--blue);
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }

        .panel-heading {
            color: var(--text);
            font-size: 1rem;
            font-weight: 700;
            margin: 0 0 4px 0;
        }

        .panel-hint {
            color: var(--muted);
            font-size: 0.82rem;
            margin-bottom: 12px;
        }

        .status-strip {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
            margin-bottom: 18px;
        }

        .status-tile, .result-panel, .analyst-note {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 8px;
            box-shadow: 0 10px 24px rgba(24, 33, 47, 0.06);
        }

        .status-tile {
            padding: 14px 16px;
        }

        .status-label {
            color: var(--muted);
            font-size: 0.76rem;
            font-weight: 800;
            text-transform: uppercase;
        }

        .status-value {
            color: var(--text);
            font-size: 1.05rem;
            font-weight: 760;
            margin-top: 4px;
        }

        .result-panel {
            padding: 24px 26px;
            min-height: 200px;
        }

        .score-track {
            position: relative;
            height: 12px;
            border-radius: 999px;
            background: #e2e8f0;
            margin: 18px 0 6px;
            overflow: visible;
        }

        .score-fill {
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
            transition: width 0.35s ease;
        }

        .score-fill-flagged {
            background: linear-gradient(90deg, #f59e0b 0%, #d97706 100%);
        }

        .score-threshold {
            position: absolute;
            top: -5px;
            width: 3px;
            height: 22px;
            background: var(--text);
            border-radius: 2px;
            transform: translateX(-50%);
        }

        .score-threshold-label {
            position: absolute;
            top: 20px;
            transform: translateX(-50%);
            font-size: 0.68rem;
            font-weight: 700;
            color: var(--muted);
            white-space: nowrap;
        }

        .score-legend {
            display: flex;
            justify-content: space-between;
            font-size: 0.72rem;
            color: var(--muted);
            margin-bottom: 4px;
        }

        .empty-state {
            background: var(--panel);
            border: 1px dashed var(--border);
            border-radius: 10px;
            padding: 48px 24px;
            text-align: center;
            color: var(--muted);
        }

        .empty-state-title {
            color: var(--text);
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 8px;
        }

        .decision-badge {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 6px 11px;
            font-size: 0.78rem;
            font-weight: 850;
        }

        .decision-review {
            color: var(--amber);
            background: #fff3df;
        }

        .decision-approve {
            color: var(--green);
            background: #e8f6ee;
        }

        .score-number {
            color: var(--text);
            font-size: 4rem;
            font-weight: 820;
            line-height: 1;
            margin: 14px 0 4px;
        }

        .score-meta {
            color: var(--muted);
            font-weight: 650;
            margin-bottom: 16px;
        }

        .analyst-note {
            padding: 16px 18px;
            color: #263244;
            line-height: 1.5;
        }

        div[data-testid="stMetric"] {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 14px 16px;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid var(--border);
            border-radius: 8px;
        }

        [data-testid="stAppViewContainer"] [data-testid="stWidgetLabel"] p,
        [data-testid="stAppViewContainer"] label,
        [data-testid="stAppViewContainer"] .stRadio p {
            color: var(--text) !important;
            font-weight: 700;
        }

        [data-testid="stAppViewContainer"] [role="radiogroup"] label p {
            color: #334155 !important;
            font-weight: 650;
        }

        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stRadio p {
            color: #f8fafc !important;
        }

        .stButton > button[kind="primary"] {
            background: var(--blue) !important;
            border: none !important;
            color: #fff !important;
            border-radius: 8px !important;
            font-weight: 700 !important;
            padding: 0.65rem 1rem !important;
            box-shadow: 0 4px 14px rgba(29, 78, 216, 0.28);
        }

        .stButton > button[kind="primary"]:hover {
            background: var(--blue-hover) !important;
            box-shadow: 0 6px 18px rgba(29, 78, 216, 0.35);
        }

        [data-testid="stAppViewContainer"] [data-baseweb="radio"] {
            gap: 10px;
        }

        [data-testid="stAppViewContainer"] [data-baseweb="radio"] label {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 8px 14px !important;
            margin-right: 4px;
        }

        [data-testid="stAppViewContainer"] [data-baseweb="radio"] label:hover {
            border-color: #94a3b8;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 10px !important;
            padding: 8px 4px 4px 4px;
        }

        .driver-table {
            width: 100%;
            border-collapse: collapse;
            overflow: hidden;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: #ffffff;
            margin-top: 2px;
            box-shadow: 0 8px 18px rgba(24, 33, 47, 0.04);
        }

        .driver-table th {
            color: #5e6b7d;
            background: #eef2f7;
            font-size: 0.76rem;
            text-align: left;
            text-transform: uppercase;
            padding: 10px 12px;
        }

        .driver-table td {
            color: var(--text);
            border-top: 1px solid #e4e9f1;
            padding: 12px;
            font-weight: 600;
            vertical-align: middle;
        }

        .driver-bar-cell {
            min-width: 140px;
        }

        .driver-bar-wrap {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .driver-bar {
            flex: 1;
            height: 8px;
            border-radius: 999px;
            background: #e8edf4;
            max-width: 120px;
        }

        .driver-bar-fill-up {
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, #fcd34d, #f59e0b);
        }

        .driver-bar-fill-down {
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, #6ee7b7, #059669);
        }

        .driver-impact {
            font-variant-numeric: tabular-nums;
            min-width: 4.5rem;
            text-align: right;
        }

        .driver-up {
            color: var(--amber);
            font-weight: 650;
        }

        .driver-down {
            color: var(--green);
            font-weight: 650;
        }

        .drivers-heading {
            color: var(--text);
            font-size: 0.92rem;
            font-weight: 700;
            margin: 22px 0 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def health_status(api_url: str) -> str:
    try:
        response = requests.get(f"{api_url}/health", timeout=3)
        response.raise_for_status()
    except requests.RequestException:
        return "offline"
    return "online"


def score_transaction(
    api_url: str,
    payload: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any] | None, str | None]:
    try:
        response = requests.post(f"{api_url}/predict", json=payload, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        return None, str(exc)
    return response.json(), None


def render_status_tile(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="status-tile">
            <div class="status-label">{label}</div>
            <div class="status-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_score_bar(probability: float, threshold: float, flagged: bool) -> None:
    pct = min(max(probability * 100, 0), 100)
    threshold_pct = min(max(threshold * 100, 0), 100)
    fill_class = "score-fill-flagged" if flagged else "score-fill"
    st.markdown(
        f"""
        <div class="score-legend">
            <span>0%</span>
            <span>Fraud probability</span>
            <span>100%</span>
        </div>
        <div class="score-track">
            <div class="{fill_class} score-fill" style="width: {pct:.1f}%;"></div>
            <div class="score-threshold" style="left: {threshold_pct:.1f}%;"></div>
            <div class="score-threshold-label" style="left: {threshold_pct:.1f}%;">
                Threshold {threshold:.1%}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_driver_table(features: list[dict[str, Any]]) -> None:
    if not features:
        return

    max_abs = max(abs(float(item["shap_value"])) for item in features) or 1.0
    rows = []
    for item in features:
        shap_value = float(item["shap_value"])
        direction = str(item["direction"])
        increases = direction == "increases_risk"
        direction_class = "driver-up" if increases else "driver-down"
        bar_pct = min(int(abs(shap_value) / max_abs * 100), 100) or 4
        bar_class = "driver-bar-fill-up" if increases else "driver-bar-fill-down"
        rows.append(
            "<tr>"
            f"<td>{escape(str(item['feature']))}</td>"
            "<td class=\"driver-bar-cell\">"
            "<div class=\"driver-bar-wrap\">"
            f"<div class=\"driver-bar\"><div class=\"{bar_class}\" "
            f'style="width: {bar_pct}%;"></div></div>'
            f'<span class="driver-impact">{shap_value:+.4f}</span>'
            "</div></td>"
            f"<td class=\"{direction_class}\">{escape(direction.replace('_', ' '))}</td>"
            "</tr>"
        )

    st.markdown('<div class="drivers-heading">Top risk drivers (Tree SHAP)</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <table class="driver-table">
            <thead>
                <tr>
                    <th>Feature</th>
                    <th>SHAP impact</th>
                    <th>Direction</th>
                </tr>
            </thead>
            <tbody>
        """
        + "\n".join(rows)
        + """
            </tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )


def render_result(result: dict[str, Any], payload: dict[str, dict[str, Any]]) -> None:
    probability = float(result["fraud_probability"])
    threshold = float(result["threshold"])
    decision = str(result["decision"])
    flagged = decision == "flag_for_review"
    decision_class = "decision-review" if flagged else "decision-approve"
    decision_label = decision.replace("_", " ")
    gap = probability - threshold
    gap_label = f"{gap:+.1%} vs threshold" if flagged else f"{abs(gap):.1%} below threshold"

    st.markdown(
        f"""
        <div class="result-panel">
            <span class="decision-badge {decision_class}">{escape(decision_label)}</span>
            <div class="score-number">{probability:.1%}</div>
            <div class="score-meta">{escape(gap_label)} · cutoff {threshold:.1%}</div>
        """,
        unsafe_allow_html=True,
    )
    render_score_bar(probability, threshold, flagged)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="analyst-note">
            {escape(str(result["analyst_summary"]))}
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_driver_table(result["top_features"])

    payload_tab, response_tab = st.tabs(["Payload", "Response"])
    with payload_tab:
        st.json(payload)
    with response_tab:
        st.json(result)


st.set_page_config(page_title="Fraud Risk Review", layout="wide")
inject_css()

st.sidebar.header("Connection")
api_url = st.sidebar.text_input("API URL", DEFAULT_API_URL, help="FastAPI backend base URL")
api_status = health_status(api_url)
status_dot = "status-dot-online" if api_status == "online" else "status-dot-offline"
st.sidebar.markdown(
    f"""
    <div class="sidebar-status">
        <div class="sidebar-status-label">Backend</div>
        <div class="sidebar-status-value">
            <span class="status-dot {status_dot}"></span>
            {escape(api_status)}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="workbench-header">
        <div>
            <div class="eyebrow">Fraud operations</div>
            <h1>Transaction risk review</h1>
            <p class="workbench-subtitle">
                Score a transaction against the IEEE-CIS model, compare to the cost-based
                threshold, and inspect Tree SHAP drivers before approving or escalating.
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="panel-heading">Scenario presets</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="panel-hint">Pick a starting profile, then adjust fields before scoring.</p>',
    unsafe_allow_html=True,
)
selected_scenario = st.radio(
    "Scenario",
    list(SCENARIOS),
    index=1,
    horizontal=True,
    label_visibility="collapsed",
)
preset = SCENARIOS[selected_scenario]

left_col, right_col = st.columns([0.37, 0.63], gap="large")

with left_col:
    with st.container(border=True):
        st.markdown('<p class="panel-heading">Transaction inputs</p>', unsafe_allow_html=True)
        amount = st.number_input(
            "Transaction amount",
            min_value=0.0,
            value=float(preset["TransactionAmt"]),
            step=10.0,
            key=f"amount_{selected_scenario}",
        )
        transaction_dt = st.number_input(
            "Transaction time offset",
            min_value=0,
            value=int(preset["TransactionDT"]),
            step=3_600,
            key=f"transaction_dt_{selected_scenario}",
        )
        product_cd = st.selectbox(
            "Product code",
            ["W", "C", "R", "H", "S"],
            index=["W", "C", "R", "H", "S"].index(str(preset["ProductCD"])),
            key=f"product_cd_{selected_scenario}",
        )
        card1 = st.number_input(
            "Card1",
            min_value=0,
            value=int(preset["card1"]),
            step=1,
            key=f"card1_{selected_scenario}",
        )
        hour = st.slider(
            "Hour",
            0,
            23,
            int(preset["hour"]),
            key=f"hour_{selected_scenario}",
        )

        payload = {
            "transaction": {
                "TransactionAmt": amount,
                "TransactionDT": transaction_dt,
                "ProductCD": product_cd,
                "card1": card1,
                "hour": hour,
            }
        }

        score_clicked = st.button("Run risk score", type="primary", use_container_width=True)

with right_col:
    if score_clicked:
        with st.spinner("Scoring transaction…"):
            result, error = score_transaction(api_url, payload)
        st.session_state.result = result
        st.session_state.error = error
        st.session_state.payload = payload
        st.session_state.scored = True

    active_payload = st.session_state.get("payload", payload)
    active_result = st.session_state.get("result")
    active_error = st.session_state.get("error")
    has_scored = st.session_state.get("scored", False)

    status_cols = st.columns(4)
    with status_cols[0]:
        render_status_tile("API", api_status)
    with status_cols[1]:
        render_status_tile("Scenario", selected_scenario)
    with status_cols[2]:
        render_status_tile("Amount", f"${amount:,.2f}")
    with status_cols[3]:
        render_status_tile("Hour", str(hour).zfill(2))

    if active_error:
        st.error(f"Prediction request failed: {active_error}")
    elif active_result and has_scored:
        render_result(active_result, active_payload)
    else:
        st.markdown(
            """
            <div class="empty-state">
                <div class="empty-state-title">No score yet</div>
                <p>Adjust the transaction fields and click <strong>Run risk score</strong>
                to call the model and load SHAP drivers.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
