"""
Concept Explainer — explains a topic in simple, student-friendly language.
"""

from .ai_engine import ask


def explain_concept(topic: str, level: str = "high school") -> str:
    """
    Explain *topic* at the given education *level*.

    Levels: 'elementary', 'middle school', 'high school', 'college', 'expert'
    """
    prompt = f"""You are a friendly and patient tutor.
Explain the concept of "{topic}" in simple, clear language suitable for a {level} student.
- Use an analogy if it helps.
- Break the explanation into short paragraphs.
- End with a 1-sentence summary starting with "In short:".
Do NOT use markdown headers. Use plain numbered points or short paragraphs only."""
    return ask(prompt)
