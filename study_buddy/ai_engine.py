"""
AI Engine — wraps NVIDIA NIM API and exposes a single ask() helper.
"""

import os
import re

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

MODEL = "openai/gpt-oss-20b"
BASE_URL = "https://integrate.api.nvidia.com/v1"


def _get_client() -> OpenAI:
    api_key = os.getenv("NVIDIA_API_KEY")

    if not api_key or api_key == "your_nvidia_api_key_here":
        raise EnvironmentError(
            "NVIDIA_API_KEY is not set.\n"
            "1. Add NVIDIA_API_KEY to your .env file.\n"
            "2. Restart the Streamlit app."
        )

    return OpenAI(
        base_url=BASE_URL,
        api_key=api_key,
    )


def friendly_error(exc: Exception) -> str:
    """
    Convert a raw API/SDK exception into a short,
    user-readable message.
    """

    msg = str(exc)
    code = None

    m = re.search(r"\b(\d{3})\b", msg)
    if m:
        code = int(m.group(1))

    if (
        code == 429
        or "RESOURCE_EXHAUSTED" in msg
        or "rate limit" in msg.lower()
        or "rate_limit" in msg.lower()
    ):
        return "Daily AI usage limit has been reached. Please try again later."

    if (
        code == 503
        or "UNAVAILABLE" in msg
        or "Service Unavailable" in msg
        or "temporarily unavailable" in msg.lower()
    ):
        return "The AI service is temporarily busy. Please try again."

    if (
        code == 401
        or "API_KEY_INVALID" in msg
        or "unauthorized" in msg.lower()
        or ("invalid" in msg.lower() and "key" in msg.lower())
    ):
        return (
            "Your NVIDIA API key appears to be invalid. "
            "Please check your NVIDIA API key configuration."
        )

    if code == 404 or "not found" in msg.lower():
        return (
            "The requested AI model was not found. "
            "Please contact the app administrator."
        )

    if "empty response" in msg.lower() or "no content" in msg.lower():
        return (
            "The AI returned an empty response. "
            "Try rephrasing your input and clicking again."
        )

    if isinstance(exc, EnvironmentError):
        return str(exc)

    clean = re.sub(r"\{.*", "", msg, flags=re.DOTALL).strip(" .'\"")

    return clean if clean else "An unexpected error occurred. Please try again."


def ask(prompt: str) -> str:
    """
    Send a prompt to NVIDIA NIM and return the final text response.
    """

    client = _get_client()

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0.2,

        # GPT-OSS-20B is a reasoning model.
        # Keep reasoning low so enough tokens remain
        # for the actual visible answer.
        reasoning_effort="low",

        # More room for reasoning + final answer.
        max_tokens=4096,
    )

    message = response.choices[0].message

    # Normal final answer
    text = getattr(message, "content", None)

    # Some NVIDIA/OpenAI-compatible responses may expose
    # useful text through reasoning_content.
    if not text:
        text = getattr(message, "reasoning_content", None)

    if not text:
        raise ValueError(
            "NVIDIA returned an empty response. "
            "The model may have returned no visible content."
        )

    return text.strip()