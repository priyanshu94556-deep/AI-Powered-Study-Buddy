"""
Flashcard Generator — creates term/definition flashcard pairs from a topic or notes.
"""

import re
from dataclasses import dataclass
from typing import List

from .ai_engine import ask


@dataclass
class Flashcard:
    number: int
    term: str
    definition: str


def generate_flashcards(source: str, num_cards: int = 8, from_notes: bool = False) -> List[Flashcard]:
    """
    Generate flashcards from a *source* (topic name or raw notes).

    from_notes: True  → treat source as pasted notes
                False → treat source as a topic name
    """
    if from_notes:
        prompt = f"""You are a study assistant. Read the notes below and create exactly {num_cards} flashcards.

--- NOTES ---
{source}
--- END ---

Format EACH card as:
TERM: <key term or concept>
DEFINITION: <clear, concise definition or explanation in 1-2 sentences>

Separate each card with a blank line. Do NOT add numbering or extra commentary."""
    else:
        prompt = f"""You are a study assistant. Create exactly {num_cards} flashcards for the topic: "{source}".

Format EACH card as:
TERM: <key term or concept>
DEFINITION: <clear, concise definition or explanation in 1-2 sentences>

Separate each card with a blank line. Do NOT add numbering or extra commentary."""

    raw = ask(prompt)
    return _parse_flashcards(raw, num_cards)


def _parse_flashcards(raw: str, n: int) -> List[Flashcard]:
    cards: List[Flashcard] = []
    # Split on blank lines to get card blocks
    blocks = re.split(r'\n\s*\n', raw.strip())
    for block in blocks:
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        term = ""
        definition = ""
        for line in lines:
            t = re.match(r'^TERM:\s*(.+)', line, re.IGNORECASE)
            if t:
                term = t.group(1).strip()
                continue
            d = re.match(r'^DEFINITION:\s*(.+)', line, re.IGNORECASE)
            if d:
                definition = d.group(1).strip()
        if term and definition:
            cards.append(Flashcard(number=len(cards) + 1, term=term, definition=definition))
        if len(cards) == n:
            break
    return cards
