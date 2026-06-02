import os
from html import escape
from pathlib import Path
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
    css_path = Path(__file__).with_name("styles.css")
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


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
            <div class="status-label">{escape(label)}</div>
            <div class="status-value">{escape(value)}</div>
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
            <span>0%</span><span>Fraud probability</span><span>100%</span>
        </div>
        <div class="score-track">
            <div class="{fill_class} score-fill" style="width:{pct:.1f}%"></div>
            <div class="score-threshold" style="left:{threshold_pct:.1f}%"></div>
            <div class="score-threshold-label" style="left:{threshold_pct:.1f}%">
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
    rows: list[str] = []
    for item in features:
        shap_value = float(item["shap_value"])
        direction = str(item["direction"])
        increases = direction == "increases_risk"
        direction_class = "driver-up" if increases else "driver-down"
        bar_pct = min(int(abs(shap_value) / max_abs * 100), 100) or 6
        bar_class = "driver-bar-fill-up" if increases else "driver-bar-fill-down"
        rows.append(
            "<tr>"
            f"<td><strong>{escape(str(item['feature']))}</strong></td>"
            f"<td><span class=\"driver-bar\"><span class=\"{bar_class}\" "
            f'style="width:{bar_pct}%;display:block"></span></span>'
            f"{shap_value:+.3f}</td>"
            f"<td class=\"{direction_class}\">"
            f"{escape(direction.replace('_', ' '))}</td>"
            "</tr>"
        )

    st.markdown('<p class="drivers-heading">Top risk drivers</p>', unsafe_allow_html=True)
    st.markdown(
        "<table class=\"driver-table\"><thead><tr>"
        "<th>Feature</th><th>Impact</th><th>Direction</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>",
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

    st.markdown('<div class="results-shell">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="result-hero">
            <div>
                <span class="decision-badge {decision_class}">{escape(decision_label)}</span>
                <div class="score-number">{probability:.1%}</div>
                <div class="score-meta">{escape(gap_label)} · cutoff {threshold:.1%}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_score_bar(probability, threshold, flagged)
    st.markdown(
        f'<div class="analyst-note">{escape(str(result["analyst_summary"]))}</div>',
        unsafe_allow_html=True,
    )
    render_driver_table(result["top_features"])
    st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("API request & response", expanded=False):
        col_a, col_b = st.columns(2)
        with col_a:
            st.caption("Request payload")
            st.json(payload)
        with col_b:
            st.caption("Model response")
            st.json(result)


st.set_page_config(
    page_title="Fraud Risk Review",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

with st.sidebar:
    st.markdown('<p class="section-label">Connection</p>', unsafe_allow_html=True)
    api_url = st.text_input(
        "API URL",
        DEFAULT_API_URL,
        label_visibility="collapsed",
        help="FastAPI backend base URL",
    )
    api_status = health_status(api_url)
    status_dot = "status-dot-online" if api_status == "online" else "status-dot-offline"
    st.markdown(
        f"""
        <div class="sidebar-status">
            <div class="sidebar-status-label">Backend</div>
            <div class="sidebar-status-value">
                <span class="status-dot {status_dot}"></span>{escape(api_status)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class="workbench-header">
        <div class="eyebrow">Fraud operations</div>
        <h1>Transaction risk review</h1>
        <p class="workbench-subtitle">
            Score a transaction with the IEEE-CIS model, compare to the cost-based
            threshold, and review Tree SHAP drivers.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

left_col, right_col = st.columns([0.38, 0.62], gap="large")

with left_col:
    st.markdown('<p class="section-title">Scenario</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="section-hint">Start from a preset, then fine-tune fields.</p>',
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

    with st.container(border=True):
        st.markdown('<p class="section-title">Transaction</p>', unsafe_allow_html=True)
        amount = st.number_input(
            "Amount (USD)",
            min_value=0.0,
            value=float(preset["TransactionAmt"]),
            step=10.0,
            format="%.2f",
            key=f"amount_{selected_scenario}",
        )
        transaction_dt = st.number_input(
            "Time offset (seconds)",
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
            "Card identifier",
            min_value=0,
            value=int(preset["card1"]),
            step=1,
            key=f"card1_{selected_scenario}",
        )
        hour = st.slider(
            "Hour of day",
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
    should_score = score_clicked or "result" not in st.session_state
    if should_score:
        with st.spinner("Scoring…"):
            result, error = score_transaction(api_url, payload)
        st.session_state.result = result
        st.session_state.error = error
        st.session_state.payload = payload
        st.session_state.scored = True

    active_payload = st.session_state.get("payload", payload)
    active_result = st.session_state.get("result")
    active_error = st.session_state.get("error")
    has_scored = st.session_state.get("scored", False)

    tiles_html = "".join(
        f'<div class="status-tile"><div class="status-label">{escape(lbl)}</div>'
        f'<div class="status-value">{escape(val)}</div></div>'
        for lbl, val in [
            ("API", api_status),
            ("Scenario", selected_scenario),
            ("Amount", f"${amount:,.2f}"),
            ("Hour", f"{hour:02d}:00"),
        ]
    )
    st.markdown(f'<div class="status-grid">{tiles_html}</div>', unsafe_allow_html=True)

    if active_error:
        st.error(f"Could not reach the API: {active_error}")
    elif active_result and has_scored:
        render_result(active_result, active_payload)
    else:
        st.markdown(
            """
            <div class="empty-state">
                <div class="empty-icon">◎</div>
                <div class="empty-state-title">Ready to score</div>
                <p>Choose a scenario, adjust the transaction, then run the model.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
