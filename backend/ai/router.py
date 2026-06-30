from dataclasses import dataclass
from typing import Literal
import os

ModelChoice = Literal["gemini", "gpt", "gpt5"]

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
class LLMResult:
    llm: object
    model_used: str
    fallback_warning: str | None


def get_llm(model_choice: ModelChoice) -> LLMResult:
    from ai.llm import llm as gemini_llm

    if model_choice not in _GITHUB_MODELS:
        return LLMResult(llm=gemini_llm, model_used="gemini", fallback_warning=None)

    cfg = _GITHUB_MODELS[model_choice]

    try:
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

        gpt_llm = ChatOpenAI(**kwargs)
        return LLMResult(llm=gpt_llm, model_used=model_choice, fallback_warning=None)

    except Exception as e:
        label = "GPT-5" if model_choice == "gpt5" else "GPT"
        warning = (
            f"{label} is unavailable ({str(e)}). "
            "Your request was processed using Gemini instead."
        )
        return LLMResult(llm=gemini_llm, model_used="gemini", fallback_warning=warning)
