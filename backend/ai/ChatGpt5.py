import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Lazy import so missing azure package doesn't crash the whole app
def get_gpt_client():
    try:
        from azure.ai.inference import ChatCompletionsClient
        from azure.core.credentials import AzureKeyCredential
    except ImportError:
        raise RuntimeError(
            "azure-ai-inference is not installed. "
            "Run: pip install azure-ai-inference"
        )

    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN environment variable is not set")

    return ChatCompletionsClient(
        endpoint="https://models.github.ai/inference",
        credential=AzureKeyCredential(GITHUB_TOKEN),
    )


GPT_MODEL = "openai/gpt-4o"