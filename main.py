"""
AI-Powered Study Buddy — Rich terminal interface.

Run with:  python main.py
"""

import sys
import io
import textwrap

# Force UTF-8 stdout on Windows so Rich emoji render correctly
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from prompt_toolkit import prompt as pt_prompt
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich import box

from study_buddy.explainer import explain_concept
from study_buddy.summarizer import summarize_notes
from study_buddy.quiz_generator import generate_quiz, QuizQuestion
from study_buddy.flashcard_generator import generate_flashcards

console = Console(highlight=False)

# ── Helpers ───────────────────────────────────────────────────────────────────

ACCENT = "bold cyan"
TITLE_STYLE = "bold white on #3b82d4"
ERROR_STYLE = "bold red"
SUCCESS_STYLE = "bold green"
MUTED = "dim"

PROMPT_STYLE = Style.from_dict({"": "ansicyan"})


def header():
    console.print()
    console.print(
        Panel.fit(
            "[bold white]AI-Powered Study Buddy[/bold white]\n"
            "[dim]Explain  |  Summarize  |  Quiz  |  Flashcards[/dim]",
            border_style="cyan",
            padding=(1, 4),
        )
    )
    console.print()


def menu() -> str:
    console.print(Rule("[cyan]Main Menu[/cyan]"))
    options = [
        ("1", "[cyan]Explain[/cyan]   a Concept"),
        ("2", "[cyan]Summarize[/cyan] Study Notes"),
        ("3", "[cyan]Quiz[/cyan]      Generate a Quiz"),
        ("4", "[cyan]Flashcards[/cyan] Generate Flashcards"),
        ("5", "[cyan]Exit[/cyan]"),
    ]
    table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    table.add_column(style="bold cyan", width=4)
    table.add_column()
    for key, label in options:
        table.add_row(key, label)
    console.print(table)
    choice = Prompt.ask("[cyan]Choose an option[/cyan]", choices=["1", "2", "3", "4", "5"])
    return choice


def spinner_ask(message: str, func, *args, **kwargs):
    """Run *func* with a live spinner, return its result."""
    with console.status(f"[cyan]{message}[/cyan]", spinner="dots"):
        return func(*args, **kwargs)


def pause():
    console.print()
    Prompt.ask("[dim]Press Enter to return to the main menu[/dim]", default="")


# ── Feature: Explain Concept ─────────────────────────────────────────────────

def feature_explain():
    console.print(Rule("[cyan]Concept Explainer[/cyan]"))
    topic = Prompt.ask("[cyan]Enter the topic or concept to explain[/cyan]")
    if not topic.strip():
        console.print("[red]Topic cannot be empty.[/red]")
        return

    levels = ["elementary", "middle school", "high school", "college", "expert"]
    console.print("\nEducation levels:")
    for i, lvl in enumerate(levels, 1):
        console.print(f"  [cyan]{i}[/cyan]  {lvl}")
    lvl_choice = IntPrompt.ask("[cyan]Choose level[/cyan]", default=3)
    level = levels[max(1, min(lvl_choice, len(levels))) - 1]

    console.print()
    result = spinner_ask(f"Explaining '{topic}' at {level} level…", explain_concept, topic, level)
    console.print(
        Panel(
            result,
            title=f"[bold]Explanation: {topic}[/bold]",
            subtitle=f"[dim]Level: {level}[/dim]",
            border_style="cyan",
            padding=(1, 2),
        )
    )
    pause()


# ── Feature: Summarize Notes ─────────────────────────────────────────────────

def feature_summarize():
    console.print(Rule("[cyan]Notes Summarizer[/cyan]"))
    console.print("[dim]Paste your notes below. Enter a line with just 'END' when done.[/dim]\n")

    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip().upper() == "END":
            break
        lines.append(line)

    notes = "\n".join(lines).strip()
    if not notes:
        console.print("[red]No notes provided.[/red]")
        return

    styles = ["bullet", "paragraph", "outline"]
    console.print("\nSummary styles:")
    for i, s in enumerate(styles, 1):
        console.print(f"  [cyan]{i}[/cyan]  {s}")
    s_choice = IntPrompt.ask("[cyan]Choose style[/cyan]", default=1)
    style = styles[max(1, min(s_choice, 3)) - 1]

    console.print()
    result = spinner_ask("Summarizing your notes…", summarize_notes, notes, style)
    console.print(
        Panel(
            result,
            title="[bold]Summary[/bold]",
            subtitle=f"[dim]Style: {style}[/dim]",
            border_style="green",
            padding=(1, 2),
        )
    )
    pause()


# ── Feature: Quiz ─────────────────────────────────────────────────────────────

def feature_quiz():
    console.print(Rule("[cyan]Quiz Generator[/cyan]"))
    topic = Prompt.ask("[cyan]Enter the topic for the quiz[/cyan]")
    if not topic.strip():
        console.print("[red]Topic cannot be empty.[/red]")
        return

    num = IntPrompt.ask("[cyan]Number of questions[/cyan]", default=5)
    num = max(1, min(num, 15))

    q_type = Prompt.ask(
        "[cyan]Quiz type[/cyan]",
        choices=["mcq", "short"],
        default="mcq",
    )

    console.print()
    questions = spinner_ask(f"Generating {num} {q_type.upper()} questions…", generate_quiz, topic, num, q_type)

    if not questions:
        console.print("[red]Could not generate quiz questions. Try again.[/red]")
        return

    _run_quiz(questions, q_type)
    pause()


def _run_quiz(questions: list[QuizQuestion], q_type: str):
    score = 0
    total = len(questions)
    console.print(Rule(f"[bold]Quiz — {total} questions[/bold]"))

    for q in questions:
        console.print(f"\n[bold cyan]Q{q.number}.[/bold cyan] {q.question}")

        if q_type == "mcq" and q.options:
            for opt in q.options:
                console.print(f"   [cyan]{opt.label})[/cyan] {opt.text}")
            user_ans = Prompt.ask(
                "   [cyan]Your answer[/cyan]",
                choices=[o.label for o in q.options],
            ).upper()
            correct = q.correct_answer.upper()
            if user_ans == correct:
                console.print(f"   [green]Correct![/green]")
                score += 1
            else:
                console.print(f"   [red]Incorrect. Answer: {correct}[/red]")
            if q.explanation:
                console.print(f"   [dim]{q.explanation}[/dim]")

        else:  # short answer
            user_ans = Prompt.ask("   [cyan]Your answer[/cyan]")
            console.print(f"   [green]Model answer:[/green] {q.correct_answer}")
            correct_self = Confirm.ask("   [cyan]Did you get it right?[/cyan]", default=False)
            if correct_self:
                score += 1

    console.print()
    console.print(Rule("[bold]Results[/bold]"))
    pct = int(score / total * 100)
    colour = "green" if pct >= 70 else "yellow" if pct >= 50 else "red"
    console.print(
        Panel(
            f"[{colour}]You scored [bold]{score}/{total}[/bold] ({pct}%)[/{colour}]",
            border_style=colour,
            padding=(0, 2),
        )
    )


# ── Feature: Flashcards ───────────────────────────────────────────────────────

def feature_flashcards():
    console.print(Rule("[cyan]Flashcard Generator[/cyan]"))
    source_type = Prompt.ask(
        "[cyan]Generate from[/cyan]",
        choices=["topic", "notes"],
        default="topic",
    )

    from_notes = source_type == "notes"
    if from_notes:
        console.print("[dim]Paste your notes below. Enter a line with just 'END' when done.[/dim]\n")
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if line.strip().upper() == "END":
                break
            lines.append(line)
        source = "\n".join(lines).strip()
        if not source:
            console.print("[red]No notes provided.[/red]")
            return
    else:
        source = Prompt.ask("[cyan]Enter the topic[/cyan]")
        if not source.strip():
            console.print("[red]Topic cannot be empty.[/red]")
            return

    num = IntPrompt.ask("[cyan]Number of flashcards[/cyan]", default=8)
    num = max(1, min(num, 20))

    console.print()
    cards = spinner_ask("Generating flashcards…", generate_flashcards, source, num, from_notes)

    if not cards:
        console.print("[red]Could not generate flashcards. Try again.[/red]")
        return

    _run_flashcards(cards)
    pause()


def _run_flashcards(cards):
    total = len(cards)
    console.print(Rule(f"[bold]Flashcards — {total} cards[/bold]"))
    console.print("[dim]Press Enter to reveal each definition.[/dim]\n")

    for card in cards:
        console.print(
            Panel(
                f"[bold]{card.term}[/bold]",
                title=f"[cyan]Card {card.number}/{total}[/cyan]",
                subtitle="[dim]TERM[/dim]",
                border_style="cyan",
                padding=(1, 2),
            )
        )
        Prompt.ask("[dim]Press Enter to reveal definition[/dim]", default="")
        console.print(
            Panel(
                card.definition,
                title=f"[cyan]Card {card.number}/{total}[/cyan]",
                subtitle="[dim]DEFINITION[/dim]",
                border_style="green",
                padding=(1, 2),
            )
        )
        console.print()

    console.print("[green]✓ All flashcards reviewed![/green]")


# ── Entry Point ───────────────────────────────────────────────────────────────

FEATURES = {
    "1": feature_explain,
    "2": feature_summarize,
    "3": feature_quiz,
    "4": feature_flashcards,
}


def main():
    header()
    while True:
        try:
            choice = menu()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye! Happy studying![/dim]")
            sys.exit(0)

        if choice == "5":
            console.print("\n[dim]Goodbye! Happy studying![/dim]")
            sys.exit(0)

        fn = FEATURES.get(choice)
        if fn:
            console.print()
            try:
                fn()
            except EnvironmentError as e:
                console.print(f"\n[red]Configuration Error:[/red]\n{e}")
                pause()
            except Exception as e:
                console.print(f"\n[red]An error occurred:[/red] {e}")
                pause()


if __name__ == "__main__":
    main()
