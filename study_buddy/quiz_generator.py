"""
Quiz Generator — creates multiple-choice or short-answer quizzes from a topic or notes.
"""

import re
from dataclasses import dataclass, field
from typing import List

from .ai_engine import ask


@dataclass
class MCQOption:
    label: str          # A, B, C, D
    text: str
    is_correct: bool = False


@dataclass
class QuizQuestion:
    number: int
    question: str
    options: List[MCQOption] = field(default_factory=list)
    correct_answer: str = ""      # used for short-answer
    explanation: str = ""
    is_mcq: bool = True


def generate_quiz(topic: str, num_questions: int = 5, quiz_type: str = "mcq") -> List[QuizQuestion]:
    """
    Generate a quiz on *topic*.

    quiz_type: 'mcq' (multiple choice) | 'short' (short answer)
    """
    if quiz_type == "mcq":
        return _generate_mcq(topic, num_questions)
    return _generate_short_answer(topic, num_questions)


# ── MCQ ──────────────────────────────────────────────────────────────────────

def _generate_mcq(topic: str, n: int) -> List[QuizQuestion]:
    prompt = f"""Create exactly {n} multiple-choice quiz questions about "{topic}".

Format EACH question strictly as:
Q<number>: <question text>
A) <option>
B) <option>
C) <option>
D) <option>
ANSWER: <letter>
EXPLANATION: <one sentence why the answer is correct>

Do NOT add extra text, headings, or blank lines between the ANSWER/EXPLANATION and the next question."""
    raw = ask(prompt)
    return _parse_mcq(raw, n)


def _parse_mcq(raw: str, n: int) -> List[QuizQuestion]:
    questions: List[QuizQuestion] = []
    # Split on question markers
    blocks = re.split(r'\n(?=Q\d+:)', raw.strip())
    for block in blocks:
        lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
        if not lines:
            continue
        q_match = re.match(r'Q\d+:\s*(.+)', lines[0])
        if not q_match:
            continue
        q_text = q_match.group(1)
        options: List[MCQOption] = []
        answer_letter = ""
        explanation = ""
        for line in lines[1:]:
            opt = re.match(r'^([A-D])[).]\s+(.+)', line)
            if opt:
                options.append(MCQOption(label=opt.group(1), text=opt.group(2)))
                continue
            ans = re.match(r'^ANSWER:\s*([A-D])', line, re.IGNORECASE)
            if ans:
                answer_letter = ans.group(1).upper()
                continue
            exp = re.match(r'^EXPLANATION:\s*(.+)', line, re.IGNORECASE)
            if exp:
                explanation = exp.group(1)
        # Mark correct option
        for opt in options:
            if opt.label == answer_letter:
                opt.is_correct = True
        questions.append(QuizQuestion(
            number=len(questions) + 1,
            question=q_text,
            options=options,
            correct_answer=answer_letter,
            explanation=explanation,
            is_mcq=True,
        ))
        if len(questions) == n:
            break
    return questions


# ── Short Answer ──────────────────────────────────────────────────────────────

def _generate_short_answer(topic: str, n: int) -> List[QuizQuestion]:
    prompt = f"""Create exactly {n} short-answer study questions about "{topic}".

Format EACH question strictly as:
Q<number>: <question text>
ANSWER: <concise 1-2 sentence answer>

Do NOT add extra text or headings."""
    raw = ask(prompt)
    return _parse_short_answer(raw, n)


def _parse_short_answer(raw: str, n: int) -> List[QuizQuestion]:
    questions: List[QuizQuestion] = []
    blocks = re.split(r'\n(?=Q\d+:)', raw.strip())
    for block in blocks:
        lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
        if not lines:
            continue
        q_match = re.match(r'Q\d+:\s*(.+)', lines[0])
        if not q_match:
            continue
        q_text = q_match.group(1)
        answer = ""
        for line in lines[1:]:
            ans = re.match(r'^ANSWER:\s*(.+)', line, re.IGNORECASE)
            if ans:
                answer = ans.group(1)
        questions.append(QuizQuestion(
            number=len(questions) + 1,
            question=q_text,
            correct_answer=answer,
            is_mcq=False,
        ))
        if len(questions) == n:
            break
    return questions
