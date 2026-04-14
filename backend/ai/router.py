from dataclasses import dataclass
from typing import Literal
import os

ModelChoice = Literal["gemini", "gpt"]


@dataclass
class LLMResult:
    llm: object
    model_used: str
    fallback_warning: str | None


def get_llm(model_choice: ModelChoice) -> LLMResult:
    from ai.llm import llm as gemini_llm

    if model_choice == "gemini":
        return LLMResult(llm=gemini_llm, model_used="gemini", fallback_warning=None)

    try:
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise RuntimeError("GITHUB_TOKEN not set")

        from langchain_openai import ChatOpenAI

        gpt_llm = ChatOpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=github_token,
            model="gpt-4o",
            temperature=0.7,
        )
        return LLMResult(llm=gpt_llm, model_used="gpt", fallback_warning=None)

    except Exception as e:
        warning = (
            f"GPT is unavailable ({str(e)}). "
            "Your request was processed using Gemini instead."
        )
        return LLMResult(llm=gemini_llm, model_used="gemini", fallback_warning=warning)
