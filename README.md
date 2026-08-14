# 🎓 AI-Powered Study Buddy

An interactive command-line study assistant powered by **Google Gemini AI**.  
It explains complex concepts in plain language, summarizes your notes, generates quizzes, and creates flashcards — on demand.

---

## Features

| Feature | What it does |
|---|---|
| 💡 **Concept Explainer** | Explains any topic at your chosen education level (elementary → expert) with analogies |
| 📝 **Notes Summarizer** | Condenses pasted notes into bullet points, a paragraph, or a structured outline |
| ❓ **Quiz Generator** | Creates multiple-choice or short-answer quizzes with instant scoring and explanations |
| 🃏 **Flashcard Generator** | Produces interactive term/definition flashcard decks from a topic or your own notes |

---

## Requirements

- Python **3.10+**
- A free **Google Gemini API key** → [Get one here](https://aistudio.google.com/app/apikey)

---

## Setup

```bash
# 1. Clone / download the project
cd "mai project"

# 2. (Recommended) Create a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your API key
copy .env.example .env         # Windows
# cp .env.example .env         # macOS / Linux

# Edit .env and replace the placeholder with your real Gemini key:
# GEMINI_API_KEY=AIza...
```

---

## Running the App

```bash
python main.py
```

You will see an interactive menu:

```
┌──────────────────────────────────────────┐
│   🎓  AI-Powered Study Buddy             │
│   Explain · Summarize · Quiz · Flashcards│
└──────────────────────────────────────────┘

──────────────── Main Menu ────────────────
  1   💡 Explain a Concept
  2   📝 Summarize Study Notes
  3   ❓ Generate a Quiz
  4   🃏 Generate Flashcards
  5   ❌ Exit
```

---

## Project Structure

```
mai project/
├── main.py                        # Entry point — Rich terminal UI
├── requirements.txt               # Python dependencies
├── .env.example                   # API key template
├── .env                           # Your actual API key (never commit this)
└── study_buddy/
    ├── __init__.py
    ├── ai_engine.py               # Gemini API wrapper
    ├── explainer.py               # Concept explanation logic
    ├── summarizer.py              # Notes summarization logic
    ├── quiz_generator.py          # Quiz generation & parsing
    └── flashcard_generator.py     # Flashcard generation & parsing
```

---

## Example Usage

### Explain a Concept
> Topic: `Photosynthesis` | Level: `middle school`  
> → Plain-English explanation with analogy + "In short:" summary

### Summarize Notes
> Paste notes about the French Revolution  
> → Bullet-point key facts in seconds

### Generate a Quiz
> Topic: `World War II` | 5 MCQ questions  
> → Interactive quiz with instant feedback and explanations

### Flashcards
> Topic: `Python data structures` | 8 cards  
> → Flip-style term → definition review session

---

## Dependencies

| Package | Purpose |
|---|---|
| `google-generativeai` | Gemini AI API client |
| `rich` | Beautiful terminal UI (panels, tables, spinners) |
| `prompt_toolkit` | Advanced input handling |
| `python-dotenv` | `.env` file loading |

---

## Notes

- The app uses **Gemini 1.5 Flash** — fast and free-tier friendly.
- Your API key is stored locally in `.env` and never leaves your machine.
- Internet connection is required for AI responses.
