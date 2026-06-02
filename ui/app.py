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
            --bg: #f4f6f9;
            --panel: #ffffff;
            --border: #d7dee8;
            --text: #18212f;
            --muted: #5e6b7d;
            --red: #b42318;
            --amber: #a15c07;
            --green: #167146;
            --blue: #255a9b;
        }

        .stApp {
            background: var(--bg);
            color: var(--text);
        }

        [data-testid="stHeader"] {
            background: rgba(244, 246, 249, 0.92);
        }

        [data-testid="stSidebar"] {
            background: #18212f;
        }

        [data-testid="stSidebar"] * {
            color: #f8fafc;
        }

        [data-testid="stSidebar"] input {
            background: #ffffff;
            color: #18212f;
        }

        .sidebar-status {
            margin-top: 14px;
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 8px;
            padding: 14px;
            background: rgba(255, 255, 255, 0.06);
        }

        .sidebar-status-label {
            color: #bcc7d6;
            font-size: 0.74rem;
            font-weight: 800;
            text-transform: uppercase;
        }

        .sidebar-status-value {
            color: #ffffff;
            font-size: 1.15rem;
            font-weight: 800;
            margin-top: 4px;
        }

        .block-container {
            padding-top: 2.2rem;
            max-width: 1280px;
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
            font-size: 2.35rem;
            line-height: 1.05;
            letter-spacing: 0;
        }

        .eyebrow {
            color: var(--blue);
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0;
            text-transform: uppercase;
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
            padding: 22px;
            min-height: 244px;
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

        .stButton > button {
            border-radius: 6px;
            font-weight: 800;
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
            padding: 11px 12px;
            font-weight: 650;
        }

        .driver-up {
            color: var(--amber);
        }

        .driver-down {
            color: var(--green);
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


def render_driver_table(features: list[dict[str, Any]]) -> None:
    rows = []
    for item in features:
        direction = str(item["direction"])
        direction_class = "driver-up" if direction == "increases_risk" else "driver-down"
        rows.append(
            "<tr>"
            f"<td>{escape(str(item['feature']))}</td>"
            f"<td>{float(item['shap_value']):+.4f}</td>"
            f"<td class=\"{direction_class}\">{escape(direction.replace('_', ' '))}</td>"
            "</tr>"
        )

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
    decision_class = "decision-review" if decision == "flag_for_review" else "decision-approve"
    decision_label = decision.replace("_", " ")

    st.markdown(
        f"""
        <div class="result-panel">
            <span class="decision-badge {decision_class}">{decision_label}</span>
            <div class="score-number">{probability:.1%}</div>
            <div class="score-meta">Threshold {threshold:.1%}</div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(min(int(probability * 100), 100))
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="analyst-note">
            {result["analyst_summary"]}
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

st.sidebar.header("Runtime")
api_url = st.sidebar.text_input("API URL", DEFAULT_API_URL)
api_status = health_status(api_url)
st.sidebar.markdown(
    f"""
    <div class="sidebar-status">
        <div class="sidebar-status-label">API</div>
        <div class="sidebar-status-value">{api_status}</div>
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
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

selected_scenario = st.radio(
    "Scenario",
    list(SCENARIOS),
    index=1,
    horizontal=True,
)
preset = SCENARIOS[selected_scenario]

left_col, right_col = st.columns([0.37, 0.63], gap="large")

with left_col:
    with st.container(border=True):
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
    if "result" not in st.session_state or score_clicked:
        result, error = score_transaction(api_url, payload)
        st.session_state.result = result
        st.session_state.error = error
        st.session_state.payload = payload

    active_payload = st.session_state.get("payload", payload)
    active_result = st.session_state.get("result")
    active_error = st.session_state.get("error")

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
    elif active_result:
        render_result(active_result, active_payload)
