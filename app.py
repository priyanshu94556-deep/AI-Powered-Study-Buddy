"""
AI-Powered Study Buddy — Streamlit Web Application
Run with:  streamlit run app.py
"""

import os
import streamlit as st
from dotenv import load_dotenv

from study_buddy.explainer import explain_concept
from study_buddy.summarizer import summarize_notes
from study_buddy.quiz_generator import generate_quiz
from study_buddy.flashcard_generator import generate_flashcards
from study_buddy.ai_engine import friendly_error

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Study Buddy",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Sidebar nav buttons */
div[data-testid="stSidebarNav"] {display: none;}

/* Card-style containers */
.feature-card {
    background: #f7f8fa;
    border: 1px solid #e5e7eb;
    border-left: 4px solid #3b82d4;
    border-radius: 8px;
    padding: 18px 20px;
    margin-bottom: 14px;
    color: #1f2328 !important;
    line-height: 1.7;
}
.feature-card * {
    color: #1f2328 !important;
}

/* Flashcard flip panels */
.fc-term {
    background: #EFF6FF;
    border: 2px solid #3b82d4;
    border-radius: 10px;
    padding: 20px 24px;
    text-align: center;
    font-size: 1.2rem;
    font-weight: 700;
    color: #1e3a5f !important;
    margin-bottom: 8px;
}
.fc-def {
    background: #F0FDF4;
    border: 2px solid #22c55e;
    border-radius: 10px;
    padding: 16px 24px;
    color: #14532d !important;
    margin-bottom: 20px;
    line-height: 1.6;
}
.fc-def * {
    color: #14532d !important;
}

/* Quiz options */
.quiz-correct {
    background: #F0FDF4;
    border: 1px solid #22c55e;
    border-radius: 6px;
    padding: 10px 14px;
    color: #14532d !important;
    font-weight: 600;
}
.quiz-correct * {
    color: #14532d !important;
}
.quiz-wrong {
    background: #FFF1F2;
    border: 1px solid #f43f5e;
    border-radius: 6px;
    padding: 10px 14px;
    color: #881337 !important;
}
.quiz-wrong * {
    color: #881337 !important;
}
.quiz-explanation {
    background: #FFFBEB;
    border-left: 3px solid #f59e0b;
    border-radius: 4px;
    padding: 8px 14px;
    color: #78350f !important;
    font-size: 0.9rem;
    margin-top: 6px;
}
.quiz-explanation * {
    color: #78350f !important;
}

/* Score badge */
.score-badge {
    display: inline-block;
    padding: 6px 18px;
    border-radius: 20px;
    font-size: 1.1rem;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# ── Session state defaults ────────────────────────────────────────────────────
def _init_state():
    defaults = {
        # Explain
        "explain_result": None,
        "explain_error": None,
        "explain_loading": False,
        # Summarize
        "summarize_result": None,
        "summarize_error": None,
        "summarize_loading": False,
        # Quiz
        "quiz_questions": [],
        "quiz_submitted": False,
        "quiz_answers": {},
        "quiz_error": None,
        "quiz_loading": False,
        # Flashcards
        "flashcards": [],
        "fc_index": 0,
        "fc_revealed": False,
        "fc_error": None,
        "fc_loading": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ── Sidebar navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎓 Study Buddy")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["💡 Explain a Concept",
         "📝 Summarize Notes",
         "❓ Generate a Quiz",
         "🃏 Flashcards"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown(
        "<small style='color:#888'>Powered by Google Gemini Flash</small>",
        unsafe_allow_html=True,
    )

# ── API key guard ─────────────────────────────────────────────────────────────
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY", "")
if not api_key or api_key == "your_gemini_api_key_here":
    st.error(
        "**GEMINI_API_KEY not configured.**\n\n"
        "1. Copy `.env.example` → `.env`\n"
        "2. Paste your key: `GEMINI_API_KEY=AIza...`\n"
        "3. Get a free key at https://aistudio.google.com/app/apikey"
    )
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Concept Explainer
# ══════════════════════════════════════════════════════════════════════════════
if page == "💡 Explain a Concept":
    st.title("💡 Concept Explainer")
    st.caption("Enter any topic and get a clear, student-friendly explanation.")

    topic = st.text_input("Topic or concept", placeholder="e.g. Photosynthesis, Newton's laws, Recursion…")

    level = st.select_slider(
        "Education level",
        options=["elementary", "middle school", "high school", "college", "expert"],
        value="high school",
    )

    explain_btn = st.button(
        "⏳ Generating…" if st.session_state.explain_loading else "Explain",
        type="primary",
        disabled=st.session_state.explain_loading,
        key="explain_btn",
    )

    if explain_btn:
        if not topic.strip():
            st.warning("Please enter a topic first.")
        elif not st.session_state.explain_loading:
            st.session_state.explain_loading = True
            st.session_state.explain_error = None
            # preserve previous result while loading
            with st.spinner("Generating explanation…"):
                try:
                    st.session_state.explain_result = explain_concept(topic.strip(), level)
                    st.session_state.explain_error = None
                except Exception as e:
                    st.session_state.explain_error = friendly_error(e)
            st.session_state.explain_loading = False

    # ── Error display with Try Again ──────────────────────────────────────────
    if st.session_state.explain_error:
        st.error(st.session_state.explain_error)
        if st.button("🔄 Try Again", key="explain_retry"):
            st.session_state.explain_error = None
            st.rerun()

    # ── Result display (persists across reruns) ───────────────────────────────
    if st.session_state.explain_result:
        st.success("Done!")
        st.markdown("### Explanation")
        st.markdown(
            f'<div class="feature-card">{st.session_state.explain_result.replace(chr(10), "<br>")}</div>',
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Notes Summarizer
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📝 Summarize Notes":
    st.title("📝 Notes Summarizer")
    st.caption("Paste your study notes and get an instant structured summary.")

    notes = st.text_area(
        "Your notes",
        height=260,
        placeholder="Paste your notes here…",
    )

    style = st.radio(
        "Summary style",
        ["bullet", "paragraph", "outline"],
        horizontal=True,
        format_func=lambda s: {"bullet": "Bullet Points", "paragraph": "Short Paragraph", "outline": "Outline"}[s],
    )

    summarize_btn = st.button(
        "⏳ Generating…" if st.session_state.summarize_loading else "Summarize",
        type="primary",
        disabled=st.session_state.summarize_loading,
        key="summarize_btn",
    )

    if summarize_btn:
        if not notes.strip():
            st.warning("Please paste some notes first.")
        elif not st.session_state.summarize_loading:
            st.session_state.summarize_loading = True
            st.session_state.summarize_error = None
            with st.spinner("Generating summary…"):
                try:
                    st.session_state.summarize_result = summarize_notes(notes.strip(), style)
                    st.session_state.summarize_error = None
                except Exception as e:
                    st.session_state.summarize_error = friendly_error(e)
            st.session_state.summarize_loading = False

    # ── Error display with Try Again ──────────────────────────────────────────
    if st.session_state.summarize_error:
        st.error(st.session_state.summarize_error)
        if st.button("🔄 Try Again", key="summarize_retry"):
            st.session_state.summarize_error = None
            st.rerun()

    # ── Result display ────────────────────────────────────────────────────────
    if st.session_state.summarize_result:
        st.success("Done!")
        st.markdown("### Summary")
        st.markdown(
            f'<div class="feature-card">{st.session_state.summarize_result.replace(chr(10), "<br>")}</div>',
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — Quiz Generator
# ══════════════════════════════════════════════════════════════════════════════
elif page == "❓ Generate a Quiz":
    st.title("❓ Quiz Generator")
    st.caption("Generate an interactive quiz on any topic and get instant feedback.")

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        topic = st.text_input("Topic", placeholder="e.g. World War II, Python functions…")
    with col2:
        num_q = st.number_input("Questions", min_value=1, max_value=15, value=5)
    with col3:
        q_type = st.selectbox("Type", ["mcq", "short"], format_func=lambda x: "Multiple Choice" if x == "mcq" else "Short Answer")

    gen_col, reset_col = st.columns([2, 1])
    with gen_col:
        generate_btn = st.button(
            "⏳ Generating…" if st.session_state.quiz_loading else "Generate Quiz",
            type="primary",
            disabled=st.session_state.quiz_loading,
            key="quiz_gen_btn",
        )
    with reset_col:
        if st.button("Reset", key="quiz_reset"):
            st.session_state.quiz_questions = []
            st.session_state.quiz_submitted = False
            st.session_state.quiz_answers = {}
            st.session_state.quiz_error = None
            st.rerun()

    if generate_btn:
        if not topic.strip():
            st.warning("Please enter a topic first.")
        elif not st.session_state.quiz_loading:
            st.session_state.quiz_loading = True
            st.session_state.quiz_error = None
            with st.spinner("Generating quiz questions…"):
                try:
                    qs = generate_quiz(topic.strip(), int(num_q), q_type)
                    st.session_state.quiz_questions = qs
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_error = None
                except Exception as e:
                    st.session_state.quiz_error = friendly_error(e)
            st.session_state.quiz_loading = False

    # ── Error display with Try Again ──────────────────────────────────────────
    if st.session_state.quiz_error:
        st.error(st.session_state.quiz_error)
        if st.button("🔄 Try Again", key="quiz_retry"):
            st.session_state.quiz_error = None
            st.rerun()

    # ── Render quiz ────────────────────────────────────────────────────────────
    questions = st.session_state.quiz_questions
    if questions:
        st.markdown("---")
        with st.form("quiz_form"):
            for q in questions:
                st.markdown(f"**Q{q.number}.** {q.question}")
                if q.is_mcq and q.options:
                    choice = st.radio(
                        f"q{q.number}",
                        options=[o.label for o in q.options],
                        format_func=lambda lbl, q=q: next(
                            f"{o.label}) {o.text}" for o in q.options if o.label == lbl
                        ),
                        label_visibility="collapsed",
                        key=f"quiz_radio_{q.number}",
                    )
                    st.session_state.quiz_answers[q.number] = choice
                else:
                    ans = st.text_input(
                        f"Your answer to Q{q.number}",
                        label_visibility="collapsed",
                        placeholder="Type your answer…",
                        key=f"quiz_short_{q.number}",
                    )
                    st.session_state.quiz_answers[q.number] = ans
                st.markdown("")

            submitted = st.form_submit_button("Submit Quiz", type="primary")
            if submitted:
                st.session_state.quiz_submitted = True

        # ── Results ────────────────────────────────────────────────────────────
        if st.session_state.quiz_submitted:
            st.markdown("### Results")
            score = 0
            for q in questions:
                user_ans = st.session_state.quiz_answers.get(q.number, "")
                if q.is_mcq:
                    correct = q.correct_answer.upper()
                    user_upper = str(user_ans).upper()
                    is_correct = user_upper == correct
                    if is_correct:
                        score += 1
                    verdict_class = "quiz-correct" if is_correct else "quiz-wrong"
                    verdict_icon = "✅" if is_correct else "❌"
                    correct_text = next(
                        (f"{o.label}) {o.text}" for o in q.options if o.label == correct), correct
                    )
                    st.markdown(
                        f'<div class="{verdict_class}">'
                        f'{verdict_icon} <b>Q{q.number}:</b> {q.question}<br>'
                        f'Your answer: <b>{user_ans}</b> &nbsp;|&nbsp; Correct: <b>{correct_text}</b>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    if q.explanation:
                        st.markdown(
                            f'<div class="quiz-explanation">💬 {q.explanation}</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.markdown(f"**Q{q.number}.** {q.question}")
                    st.info(f"**Model answer:** {q.correct_answer}")
                    self_correct = st.checkbox(f"I got Q{q.number} right", key=f"self_{q.number}")
                    if self_correct:
                        score += 1
                st.markdown("")

            # Score banner
            total = len(questions)
            pct = int(score / total * 100)
            colour = "#22c55e" if pct >= 70 else "#f59e0b" if pct >= 50 else "#f43f5e"
            st.markdown(
                f'<div style="text-align:center; margin-top:16px;">'
                f'<span class="score-badge" style="background:{colour}22; border:2px solid {colour}; color:{colour};">'
                f'Score: {score} / {total} &nbsp;({pct}%)'
                f'</span></div>',
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — Flashcards
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🃏 Flashcards":
    st.title("🃏 Flashcard Generator")
    st.caption("Generate and flip through interactive flashcards on any topic.")

    source_type = st.radio("Generate from", ["Topic", "My Notes"], horizontal=True)
    from_notes = source_type == "My Notes"

    if from_notes:
        source = st.text_area("Paste your notes", height=200, placeholder="Paste notes here…")
    else:
        source = st.text_input("Topic", placeholder="e.g. Python data structures, The Solar System…")

    num_cards = st.slider("Number of flashcards", min_value=3, max_value=20, value=8)

    gen_col, reset_col = st.columns([2, 1])
    with gen_col:
        gen_btn = st.button(
            "⏳ Generating…" if st.session_state.fc_loading else "Generate Flashcards",
            type="primary",
            disabled=st.session_state.fc_loading,
            key="fc_gen_btn",
        )
    with reset_col:
        if st.button("Reset", key="fc_reset"):
            st.session_state.flashcards = []
            st.session_state.fc_index = 0
            st.session_state.fc_revealed = False
            st.session_state.fc_error = None
            st.rerun()

    if gen_btn:
        if not source.strip():
            st.warning("Please enter a topic or paste some notes first.")
        elif not st.session_state.fc_loading:
            st.session_state.fc_loading = True
            st.session_state.fc_error = None
            with st.spinner("Generating flashcards…"):
                try:
                    cards = generate_flashcards(source.strip(), num_cards, from_notes)
                    st.session_state.flashcards = cards
                    st.session_state.fc_index = 0
                    st.session_state.fc_revealed = False
                    st.session_state.fc_error = None
                except Exception as e:
                    st.session_state.fc_error = friendly_error(e)
            st.session_state.fc_loading = False

    # ── Error display with Try Again ──────────────────────────────────────────
    if st.session_state.fc_error:
        st.error(st.session_state.fc_error)
        if st.button("🔄 Try Again", key="fc_retry"):
            st.session_state.fc_error = None
            st.rerun()

    # ── Flashcard viewer ───────────────────────────────────────────────────────
    cards = st.session_state.flashcards
    if cards:
        idx = st.session_state.fc_index
        card = cards[idx]
        total = len(cards)

        st.markdown("---")
        st.markdown(
            f"<div style='text-align:center; color:#888; font-size:0.9rem; margin-bottom:8px;'>"
            f"Card {idx + 1} of {total}</div>",
            unsafe_allow_html=True,
        )

        # Progress bar
        st.progress((idx + 1) / total)

        # Term card
        st.markdown(
            f'<div class="fc-term">{card.term}</div>',
            unsafe_allow_html=True,
        )

        # Reveal / hide definition
        if st.session_state.fc_revealed:
            st.markdown(
                f'<div class="fc-def"><b>Definition:</b><br>{card.definition}</div>',
                unsafe_allow_html=True,
            )
            reveal_label = "Hide Definition"
        else:
            reveal_label = "Reveal Definition"

        btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
        with btn_col1:
            if st.button("← Previous", disabled=idx == 0):
                st.session_state.fc_index -= 1
                st.session_state.fc_revealed = False
                st.rerun()
        with btn_col2:
            if st.button(reveal_label, type="primary"):
                st.session_state.fc_revealed = not st.session_state.fc_revealed
                st.rerun()
        with btn_col3:
            if st.button("Next →", disabled=idx == total - 1):
                st.session_state.fc_index += 1
                st.session_state.fc_revealed = False
                st.rerun()

        if idx == total - 1 and st.session_state.fc_revealed:
            st.success("You've reviewed all flashcards!")
