"""
AI Engine — wraps Google Gemini (google-genai SDK) and exposes a single ask() helper.
"""

import os
import re
from google import genai
from dotenv import load_dotenv

load_dotenv()

# ── Model configuration ───────────────────────────────────────────────────────
# Change this one constant to switch models across the entire app.
# "gemini-flash-latest" is Google's stable alias for the current recommended
# Flash model — verified working against this API key on 2025-05-30.
MODEL = "models/gemini-flash-latest"


def _get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise EnvironmentError(
            "GEMINI_API_KEY is not set.\n"
            "1. Copy .env.example to .env\n"
            "2. Replace 'your_gemini_api_key_here' with your real key\n"
            "   → https://aistudio.google.com/app/apikey"
        )
    return genai.Client(api_key=api_key)


def friendly_error(exc: Exception) -> str:
    """
    Convert a raw API/SDK exception into a short, user-readable message.
    Never exposes raw JSON dicts or stack details to the caller.

    Used by all four features (Explain, Summarize, Quiz, Flashcards) via app.py.
    To change any user-facing error message, edit only this function.
    """
    msg = str(exc)
    code = None

    # Extract numeric HTTP status code if present (e.g. "429 RESOURCE_EXHAUSTED")
    m = re.search(r'\b(\d{3})\b', msg)
    if m:
        code = int(m.group(1))

    if code == 429 or "RESOURCE_EXHAUSTED" in msg:
        return "Daily AI usage limit has been reached. Please try again later."

    if code == 503 or "UNAVAILABLE" in msg or "Service Unavailable" in msg:
        return "The AI service is temporarily busy. Please try again."
    if code == 401 or "API_KEY_INVALID" in msg or "invalid" in msg.lower() and "key" in msg.lower():
        return (
            "Your Gemini API key appears to be invalid. "
            "Please check your .env file and restart the app."
        )
    if code == 404 or "NOT_FOUND" in msg:
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
        return str(exc)   # already a clean human message

    # Generic fallback — never show raw dicts
    # Strip anything that looks like a JSON blob (starts with {)
    clean = re.sub(r'\{.*', '', msg, flags=re.DOTALL).strip(" .'\"")
    return clean if clean else "An unexpected error occurred. Please try again."


def ask(prompt: str) -> str:
    """Send a prompt to Gemini and return the text response."""
    client = _get_client()
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
    )
    text = getattr(response, "text", None)
    if not text:
        # Dig into candidates in case .text is None (e.g. safety filter, empty part)
        try:
            text = response.candidates[0].content.parts[0].text
        except (IndexError, AttributeError):
            text = None
    if not text:
        raise ValueError(
            "Gemini returned an empty response. "
            "The model may have blocked the request or returned no content."
        )
    return text.strip()
