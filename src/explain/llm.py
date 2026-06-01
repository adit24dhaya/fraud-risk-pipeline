import os
from dataclasses import dataclass
from typing import Any

import httpx

from src.explain.types import DomainConfig, FeatureContribution

HF_INFERENCE_BASE = "https://api-inference.huggingface.co/models"


class HfInferenceError(RuntimeError):
    """Raised when the Hugging Face inference API returns an error."""


@dataclass(frozen=True)
class HfLlmSettings:
    api_token: str
    model_id: str
    timeout_seconds: float
    max_new_tokens: int

    @property
    def is_configured(self) -> bool:
        return bool(self.api_token)


def load_hf_settings() -> HfLlmSettings:
    return HfLlmSettings(
        api_token=os.getenv("HF_API_TOKEN", "").strip(),
        model_id=os.getenv("HF_MODEL_ID", "Qwen/Qwen2.5-7B-Instruct").strip(),
        timeout_seconds=float(os.getenv("HF_INFERENCE_TIMEOUT_SECONDS", "30")),
        max_new_tokens=int(os.getenv("HF_MAX_NEW_TOKENS", "256")),
    )


def build_analyst_prompt(
    *,
    prediction: float,
    decision: str,
    threshold: float,
    shap_features: list[FeatureContribution],
    domain: DomainConfig,
) -> str:
    decision_label = (
        domain.positive_decision_phrase
        if prediction >= threshold
        else domain.negative_decision_phrase
    )
    driver_lines = []
    for item in shap_features[:5]:
        driver_lines.append(
            f"- {item.feature}: SHAP {item.shap_value:+.4f} ({item.direction})"
        )
    drivers = "\n".join(driver_lines) if driver_lines else "- No SHAP drivers available"
    guardrails = "\n".join(f"- {rule}" for rule in domain.guardrails)

    return (
        f"You are a {domain.reviewer_role} writing a brief review note.\n\n"
        f"Guardrails:\n{guardrails}\n\n"
        f"Model score: {prediction:.1%}\n"
        f"Cost-based threshold: {threshold:.3f}\n"
        f"Decision framing: {decision_label}\n"
        f"System decision code: {decision}\n\n"
        f"Top Tree SHAP drivers:\n{drivers}\n\n"
        "Write 2-4 sentences in plain English for a human reviewer. "
        "Do not invent features that are not listed."
    )


def generate_hf_summary(
    prompt: str,
    settings: HfLlmSettings,
    *,
    client: httpx.Client | None = None,
) -> str:
    if not settings.is_configured:
        msg = "HF_API_TOKEN is not set"
        raise HfInferenceError(msg)

    url = f"{HF_INFERENCE_BASE}/{settings.model_id}"
    headers = {"Authorization": f"Bearer {settings.api_token}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": settings.max_new_tokens,
            "temperature": 0.2,
            "return_full_text": False,
        },
    }

    owns_client = client is None
    http = client or httpx.Client(timeout=settings.timeout_seconds)
    try:
        response = http.post(url, headers=headers, json=payload)
    except httpx.TimeoutException as exc:
        raise HfInferenceError("Hugging Face inference request timed out") from exc
    except httpx.HTTPError as exc:
        raise HfInferenceError(f"Hugging Face inference request failed: {exc}") from exc
    finally:
        if owns_client:
            http.close()

    if response.status_code >= 400:
        raise HfInferenceError(_format_hf_error(response))

    return _parse_hf_response(response.json())


def _format_hf_error(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return f"Hugging Face API error ({response.status_code})"
    if isinstance(body, dict) and "error" in body:
        return str(body["error"])
    return f"Hugging Face API error ({response.status_code}): {body}"


def _parse_hf_response(data: Any) -> str:
    if isinstance(data, list) and data:
        data = data[0]
    if isinstance(data, dict):
        if "generated_text" in data:
            text = str(data["generated_text"]).strip()
            if text:
                return text
        if "error" in data:
            raise HfInferenceError(str(data["error"]))
    raise HfInferenceError(f"Unexpected Hugging Face response: {data!r}")
