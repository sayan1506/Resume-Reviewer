import os
from dotenv import load_dotenv

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential


load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

endpoint = "https://models.github.ai/inference"
model = "openai/gpt-5"


client = ChatCompletionsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(GITHUB_TOKEN),
)


def generate_ai_response(prompt: str):

    response = client.complete(
        model=model,
        messages=[
            SystemMessage("You are an expert AI assistant."),
            UserMessage(prompt),
        ],
    )

    return response.choices[0].message.content