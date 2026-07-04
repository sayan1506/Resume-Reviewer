from dataclasses import dataclass
from typing import Literal
import os

ModelChoice = Literal["gemini", "gpt", "gpt5"]

# Fixed fallback order. The user-selected model is always tried FIRST, then the
# remaining models follow in this order, so every selection gets full coverage:
#   pick gpt    -> gpt, gemini, gpt5
#   pick gemini -> gemini, gpt, gpt5
#   pick gpt5   -> gpt5, gpt, gemini
_FALLBACK_ORDER = ["gpt", "gemini", "gpt5"]

_LABELS = {"gpt": "GPT-4o", "gpt5": "GPT-5", "gemini": "Gemini"}

# GitHub Models-hosted choices → (endpoint, model id). All support tool-calling,
# which is required by the with_structured_output(...) chains in the services.
_GITHUB_MODELS = {
    "gpt": {
        "base_url": "https://models.inference.ai.azure.com",
        "model": "gpt-4o",
        "temperature": 0.7,
    },
    "gpt5": {
        "base_url": "https://models.github.ai/inference",
        "model": "openai/gpt-5",
        "temperature": None,  # reasoning model: only the default temperature is allowed
    },
}


@dataclass
class InvokeResult:
    result: object
    model_used: str
    fallback_warning: str | None


def _build_llm(model_name: str):
    """Construct an LLM client for the given model name, or raise on failure.

    A raise here means the model is skipped and the next one in the chain is tried.
    """
    if model_name == "gemini":
        from ai.llm import llm as gemini_llm
        return gemini_llm

    cfg = _GITHUB_MODELS[model_name]

    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        raise RuntimeError("GITHUB_TOKEN not set")

    from langchain_openai import ChatOpenAI

    kwargs = {
        "base_url": cfg["base_url"],
        "api_key": github_token,
        "model": cfg["model"],
    }
    # Reasoning models (temperature=None) reject an explicit temperature —
    # only the server default is allowed, so omit the param entirely.
    if cfg["temperature"] is not None:
        kwargs["temperature"] = cfg["temperature"]

    return ChatOpenAI(**kwargs)


def _fallback_chain(model_choice: str) -> list[str]:
    """Selected model first, then the rest in the fixed _FALLBACK_ORDER."""
    selected = model_choice if model_choice in _FALLBACK_ORDER else "gpt"
    return [selected] + [m for m in _FALLBACK_ORDER if m != selected]


def invoke_with_fallback(model_choice: str, chain_factory, inputs) -> InvokeResult:
    """Run a chain against the selected model, cascading through fallbacks on failure.

    chain_factory: a callable taking an llm and returning a Runnable to invoke.
                   e.g. ``lambda llm: prompt | llm.with_structured_output(Schema)``
    inputs:        the value passed to ``.invoke(...)`` (a dict for prompt chains,
                   or a raw string for a bare llm).

    Tries each model in _fallback_chain(model_choice) until one succeeds. The first
    failure (if any) is reported in ``fallback_warning`` on the successful result.
    Raises HTTPException(502) if every model in the chain fails.
    """
    from fastapi import HTTPException

    first_failure = None  # (model_name, error) of the first model that failed

    for model_name in _fallback_chain(model_choice):
        try:
            llm = _build_llm(model_name)
            result = chain_factory(llm).invoke(inputs)
        except Exception as e:
            if first_failure is None:
                first_failure = (model_name, e)
            continue

        if first_failure is None:
            warning = None
        else:
            failed_model, failed_err = first_failure
            warning = (
                f"{_LABELS[failed_model]} was unavailable ({failed_err}). "
                f"Your request was processed using {_LABELS[model_name]} instead."
            )
        return InvokeResult(result=result, model_used=model_name, fallback_warning=warning)

    raise HTTPException(
        status_code=502,
        detail="The AI model is currently unavailable. Please try again.",
    )
