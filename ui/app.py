import os
from html import escape
from pathlib import Path
from typing import Any

import requests
import streamlit as st

DEFAULT_API_URL = os.getenv("FRAUD_API_URL", "http://localhost:8000")

MODEL_META = {
    "dataset": "IEEE-CIS Fraud Detection",
    "pr_auc": "0.44",
    "precision": "0.31",
    "recall": "0.54",
    "features": "175",
}

SCENARIOS: dict[str, dict[str, Any]] = {
    "Low friction": {
        "TransactionAmt": 24.50,
        "TransactionDT": 3_600,
        "ProductCD": "W",
        "card1": 1_000,
        "hour": 1,
        "blurb": "Small daytime purchase — typically low risk.",
    },
    "Review edge": {
        "TransactionAmt": 250.00,
        "TransactionDT": 7_500_000,
        "ProductCD": "W",
        "card1": 12_345,
        "hour": 23,
        "blurb": "Late-night mid-ticket charge — often near the decision boundary.",
    },
    "High value": {
        "TransactionAmt": 1_250.00,
        "TransactionDT": 12_345_678,
        "ProductCD": "C",
        "card1": 17_000,
        "hour": 3,
        "blurb": "High amount, unusual timing — elevated fraud signals.",
    },
}


def inject_css() -> None:
    css_path = Path(__file__).with_name("styles.css")
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def health_status(api_url: str) -> bool:
    try:
        response = requests.get(f"{api_url}/health", timeout=3)
        response.raise_for_status()
    except requests.RequestException:
        return False
    return True


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


def parse_insights(summary: str, features: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    """Turn template summary + SHAP into recruiter-friendly bullet lists."""
    increases = [
        f"{item['feature']} ({float(item['shap_value']):+.2f})"
        for item in features
        if item.get("direction") == "increases_risk"
    ][:3]
    decreases = [
        f"{item['feature']} ({float(item['shap_value']):+.2f})"
        for item in features
        if item.get("direction") == "decreases_risk"
    ][:3]

    if not increases and "increasing risk" in summary.lower():
        part = summary.lower().split("increasing risk:")[-1].split(".")[0]
        increases = [p.strip() for p in part.split(",") if p.strip()][:3]
    if not decreases and "offsetting" in summary.lower():
        part = summary.lower().split("offsetting signals:")[-1].split(".")[0]
        decreases = [p.strip() for p in part.split(",") if p.strip()][:3]

    verdict = summary.split(".")[0].strip() if summary else "Score computed."
    if verdict and not verdict.endswith("."):
        verdict += "."
    return [verdict], increases or ["No strong risk amplifiers in top features."]


def render_hero(api_online: bool) -> None:
    dot_class = "" if api_online else "offline"
    live_label = "API connected" if api_online else "API unreachable"
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-inner">
                <div class="hero-top">
                    <span class="hero-eyebrow">Production-style ML demo</span>
                    <span class="live-pill">
                        <span class="live-dot {dot_class}"></span>{live_label}
                    </span>
                </div>
                <h1>Real-time fraud risk scoring</h1>
                <p class="hero-sub">
                    IEEE-CIS XGBoost model with cost-based thresholding, Tree SHAP
                    explainability, and analyst-ready summaries — served via FastAPI.
                </p>
                <div class="tech-stack">
                    <span class="tech-pill">FastAPI</span>
                    <span class="tech-pill">XGBoost</span>
                    <span class="tech-pill">Tree SHAP</span>
                    <span class="tech-pill">IEEE-CIS</span>
                    <span class="tech-pill">Heroku</span>
                </div>
                <div class="model-stats">
                    <span class="model-stat">PR-AUC<strong>{MODEL_META["pr_auc"]}</strong></span>
                    <span class="model-stat">Precision<strong>{MODEL_META["precision"]}</strong></span>
                    <span class="model-stat">Recall<strong>{MODEL_META["recall"]}</strong></span>
                    <span class="model-stat">Features<strong>{MODEL_META["features"]}</strong></span>
                </div>
            </div>
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
        <div class="score-track">
            <div class="{fill_class} score-fill" style="width:{pct:.1f}%"></div>
            <div class="score-threshold" style="left:{threshold_pct:.1f}%"></div>
            <div class="score-threshold-label" style="left:{threshold_pct:.1f}%">
                Cutoff {threshold:.1%}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_driver_cards(features: list[dict[str, Any]]) -> None:
    if not features:
        return
    max_abs = max(abs(float(item["shap_value"])) for item in features) or 1.0
    rows: list[str] = []
    for item in features:
        shap_value = float(item["shap_value"])
        increases = item.get("direction") == "increases_risk"
        bar_pct = min(int(abs(shap_value) / max_abs * 100), 100) or 8
        fill_class = "up" if increases else "down"
        tag_class = "up" if increases else "down"
        tag_label = "↑ Risk" if increases else "↓ Risk"
        rows.append(
            f'<div class="driver-row">'
            f'<span class="driver-name">{escape(str(item["feature"]))}</span>'
            f'<div class="driver-meter"><div class="driver-meter-fill {fill_class}" '
            f'style="width:{bar_pct}%"></div></div>'
            f'<span class="driver-tag {tag_class}">{tag_label} {shap_value:+.3f}</span>'
            f"</div>"
        )
    st.markdown(
        '<p class="drivers-section-title">Explainability · Tree SHAP (top 5)</p>'
        f'<div class="driver-cards">{"".join(rows)}</div>',
        unsafe_allow_html=True,
    )


def render_result(
    result: dict[str, Any],
    payload: dict[str, dict[str, Any]],
) -> None:
    probability = float(result["fraud_probability"])
    threshold = float(result["threshold"])
    decision = str(result["decision"])
    flagged = decision == "flag_for_review"
    card_class = "review" if flagged else "approve"
    score_class = "review" if flagged else "approve"

    if flagged:
        title = "Flag for analyst review"
        desc = (
            f"Fraud probability {probability:.1%} exceeds the cost-optimized "
            f"threshold of {threshold:.1%}. Queue for manual review before approving."
        )
    else:
        title = "Approve transaction"
        desc = (
            f"Score {probability:.1%} stays below the {threshold:.1%} threshold. "
            "No escalation required under the current policy."
        )

    verdict_lines, risk_signals = parse_insights(
        str(result.get("analyst_summary", "")), result.get("top_features", [])
    )
    offsetting = [
        f"{item['feature']} ({float(item['shap_value']):+.2f})"
        for item in result.get("top_features", [])
        if item.get("direction") == "decreases_risk"
    ][:3]

    st.markdown(
        f"""
        <div class="decision-card {card_class}">
            <div class="decision-layout">
                <div class="score-block {score_class}">
                    <div class="label">Fraud probability</div>
                    <div class="value">{probability:.1%}</div>
                </div>
                <div>
                    <h2 class="decision-title">{escape(title)}</h2>
                    <p class="decision-desc">{escape(desc)}</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_score_bar(probability, threshold, flagged)

    risk_items = "".join(f"<li>{escape(s)}</li>" for s in risk_signals)
    offset_items = "".join(
        f"<li>{escape(s)}</li>"
        for s in (offsetting or ["No strong offsetting signals in top features."])
    )
    verdict_html = "".join(f"<li>{escape(v)}</li>" for v in verdict_lines)

    st.markdown(
        f"""
        <div class="insight-grid">
            <div class="insight-card">
                <h3>Analyst summary</h3>
                <ul>{verdict_html}</ul>
            </div>
            <div class="insight-card">
                <h3>Risk amplifiers</h3>
                <ul>{risk_items}</ul>
                <h3 style="margin-top:0.85rem;font-size:0.72rem;font-weight:700;
                    text-transform:uppercase;letter-spacing:0.05em;color:#64748b">
                    Offsetting factors</h3>
                <ul>{offset_items}</ul>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_driver_cards(result.get("top_features", []))

    with st.expander("Technical details (request / response JSON)", expanded=False):
        col_a, col_b = st.columns(2)
        with col_a:
            st.caption("Request")
            st.json(payload)
        with col_b:
            st.caption("Response")
            st.json(result)


def run_score(api_url: str, payload: dict[str, dict[str, Any]]) -> None:
    result, error = score_transaction(api_url, payload)
    st.session_state.result = result
    st.session_state.error = error
    st.session_state.payload = payload
    st.session_state.scored = True


st.set_page_config(
    page_title="Fraud Risk Pipeline",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()

api_url = DEFAULT_API_URL.rstrip("/")
api_online = health_status(api_url)
render_hero(api_online)

left_col, right_col = st.columns([0.36, 0.64], gap="large")

with left_col:
    st.markdown('<p class="section-title">Try a scenario</p>', unsafe_allow_html=True)
    selected_scenario = st.radio(
        "Scenario",
        list(SCENARIOS),
        index=1,
        horizontal=True,
        label_visibility="collapsed",
    )
    st.markdown(
        f'<p class="section-hint">{escape(SCENARIOS[selected_scenario]["blurb"])}</p>',
        unsafe_allow_html=True,
    )
    preset = SCENARIOS[selected_scenario]

    with st.container(border=True):
        amount = st.number_input(
            "Amount (USD)",
            min_value=0.0,
            value=float(preset["TransactionAmt"]),
            step=10.0,
            format="%.2f",
            key=f"amount_{selected_scenario}",
        )
        transaction_dt = st.number_input(
            "Time offset (sec)",
            min_value=0,
            value=int(preset["TransactionDT"]),
            step=3_600,
            key=f"dt_{selected_scenario}",
        )
        product_cd = st.selectbox(
            "Product",
            ["W", "C", "R", "H", "S"],
            index=["W", "C", "R", "H", "S"].index(str(preset["ProductCD"])),
            key=f"product_{selected_scenario}",
        )
        card1 = st.number_input(
            "Card ID",
            min_value=0,
            value=int(preset["card1"]),
            step=1,
            key=f"card_{selected_scenario}",
        )
        hour = st.slider("Hour (0–23)", 0, 23, int(preset["hour"]), key=f"hour_{selected_scenario}")

        payload = {
            "transaction": {
                "TransactionAmt": amount,
                "TransactionDT": transaction_dt,
                "ProductCD": product_cd,
                "card1": card1,
                "hour": hour,
            }
        }
        score_clicked = st.button("Score transaction", type="primary", use_container_width=True)

with right_col:
    if score_clicked:
        with st.spinner("Running model inference…"):
            run_score(api_url, payload)
    elif not st.session_state.get("scored") and api_online:
        # First visit: auto-demo the edge case so recruiters see value immediately
        demo_payload = {
            "transaction": {
                k: v
                for k, v in SCENARIOS["Review edge"].items()
                if k != "blurb"
            }
        }
        run_score(api_url, demo_payload)

    active_result = st.session_state.get("result")
    active_error = st.session_state.get("error")
    active_payload = st.session_state.get("payload", payload)
    has_scored = st.session_state.get("scored", False)

    chips = [
        ("Scenario", selected_scenario),
        ("Amount", f"${amount:,.2f}"),
        ("Product", product_cd),
        ("Hour", f"{hour:02d}:00"),
    ]
    chips_html = "".join(
        f'<div class="txn-chip"><div class="k">{escape(k)}</div>'
        f'<div class="v">{escape(v)}</div></div>'
        for k, v in chips
    )
    st.markdown(f'<div class="txn-summary">{chips_html}</div>', unsafe_allow_html=True)

    if active_error:
        st.error(f"Could not reach the scoring API. Check that the backend is running.\n\n{active_error}")
    elif active_result and has_scored:
        render_result(active_result, active_payload)
    else:
        st.markdown(
            """
            <div class="empty-state">
                <h2>Score a transaction</h2>
                <p>Pick a scenario on the left and click <strong>Score transaction</strong>
                to see the decision, SHAP drivers, and analyst summary.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown(
    '<p class="footer-note">Fraud Risk Pipeline · IEEE-CIS · cost-based threshold · Tree SHAP</p>',
    unsafe_allow_html=True,
)
