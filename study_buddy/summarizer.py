"""
Notes Summarizer — condenses study notes into key points.
"""

from .ai_engine import ask


def summarize_notes(notes: str, style: str = "bullet") -> str:
    """
    Summarize the provided *notes*.

    Styles:
        'bullet'    — concise bullet-point key facts
        'paragraph' — a short prose summary
        'outline'   — hierarchical topic outline
    """
    style_instructions = {
        "bullet": "Produce a concise bullet-point list of the most important facts and ideas. "
                  "Each bullet should be a single sentence.",
        "paragraph": "Write a clear, flowing summary in 3-5 sentences. "
                     "Capture the main ideas without unnecessary detail.",
        "outline": "Create a hierarchical outline (main topics with sub-points) "
                   "that organises all key information.",
    }
    instruction = style_instructions.get(style, style_instructions["bullet"])
    prompt = f"""You are an expert academic summarizer.
Read the following study notes and produce a summary.

STYLE: {instruction}

--- NOTES START ---
{notes}
--- NOTES END ---

Only output the summary itself. Do not add any commentary or preamble."""
    return ask(prompt)
