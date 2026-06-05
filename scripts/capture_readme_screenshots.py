"""Capture README demo screenshots from live Heroku apps."""

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "docs" / "media"

UI_URL = "https://adit-txn-risk-pipeline-ui-e2c4483417ee.herokuapp.com/"
API_DOCS_URL = "https://adit-txn-risk-pipeline-41ee5a80b27b.herokuapp.com/docs"
DRIFT_REPORT = ROOT / "docs" / "media" / "drift_report.html"


def capture() -> None:
    MEDIA.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            device_scale_factor=2,
        )
        page = context.new_page()

        # Streamlit UI — wait for hero + scored results
        page.goto(UI_URL, wait_until="networkidle", timeout=90_000)
        page.wait_for_timeout(4000)
        page.screenshot(path=str(MEDIA / "streamlit-ui.png"), full_page=True)

        # Cropped results panel for prediction-examples
        results = page.locator(".decision-card").first
        if results.count() > 0:
            results.screenshot(path=str(MEDIA / "prediction-examples.png"))
        else:
            page.screenshot(
                path=str(MEDIA / "prediction-examples.png"),
                clip={"x": 520, "y": 280, "width": 860, "height": 520},
            )

        # FastAPI Swagger
        page.goto(API_DOCS_URL, wait_until="networkidle", timeout=60_000)
        page.wait_for_timeout(2000)
        page.screenshot(path=str(MEDIA / "api-docs.png"), full_page=False)

        # Evidently drift report (local HTML)
        if DRIFT_REPORT.exists():
            page.goto(DRIFT_REPORT.as_uri(), wait_until="networkidle", timeout=60_000)
            page.wait_for_timeout(3000)
            page.screenshot(path=str(MEDIA / "drift-report.png"), full_page=False)

        browser.close()

    print("Saved screenshots to", MEDIA)


if __name__ == "__main__":
    capture()
