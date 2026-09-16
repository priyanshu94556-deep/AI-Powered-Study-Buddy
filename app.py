"""
AI-Powered Study Buddy — Streamlit Web Application
Run with:  streamlit run app.py
"""

import os
import datetime
from typing import List, cast
import streamlit as st
from dotenv import load_dotenv

# ── Existing AI modules (unchanged) ──────────────────────────────────────────
from study_buddy.explainer import explain_concept
from study_buddy.summarizer import summarize_notes
from study_buddy.quiz_generator import generate_quiz, QuizQuestion, MCQOption
from study_buddy.flashcard_generator import generate_flashcards, Flashcard
from study_buddy.ai_engine import friendly_error, ask

# ── Firebase availability check ───────────────────────────────────────────────
_FIREBASE_AVAILABLE = (
    "firebase" in st.secrets
    and "firebase_service_account" in st.secrets
)

# ── Firebase / storage imports (lazy but resolved at module level) ────────────
# Imported unconditionally so static analysis can resolve all names.
# At runtime the underlying SDK init is still deferred per-session.
from study_buddy.auth import sign_in, sign_up, send_password_reset
from study_buddy.storage import (
    save_profile,
    save_history,
    load_history,
    add_task,
    get_tasks,
    update_task,
    delete_task,
    add_note,
    get_notes,
    update_note,
    delete_note,
    add_study_session,
    get_study_plan,
    update_study_session,
    delete_study_session,
    save_quiz_score,
    get_analytics,
    get_quiz_scores,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Study Buddy",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
div[data-testid="stSidebarNav"] { display: none; }
html, body, [class*="css"] {
    font-family: -apple-system, "Segoe UI", system-ui, sans-serif;
}
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e1b4b 0%, #2e1065 100%);
    border-right: 1px solid #4c1d95;
}
section[data-testid="stSidebar"] * { color: #e0e7ff; }
section[data-testid="stSidebar"] hr {
    border-color: rgba(167,139,250,0.25) !important; margin: 10px 0 !important;
}
/* Sidebar nav buttons */
.nav-btn button {
    background: transparent !important;
    border: none !important;
    color: #c7d2fe !important;
    font-size: 0.92rem !important;
    font-weight: 500 !important;
    text-align: left !important;
    padding: 8px 14px !important;
    border-radius: 8px !important;
    width: 100% !important;
    transition: background 0.15s !important;
}
.nav-btn button:hover {
    background: rgba(167,139,250,0.15) !important;
    color: #f0e6ff !important;
}
.nav-btn-active button {
    background: rgba(124,58,237,0.35) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
}
.main .block-container {
    padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1140px;
}
.dash-hero {
    background: linear-gradient(135deg, #1e1b4b 0%, #4c1d95 50%, #6d28d9 100%);
    border-radius: 16px; padding: 36px 40px; margin-bottom: 28px;
    position: relative; overflow: hidden;
}
.dash-hero::before {
    content: ""; position: absolute; top: -60px; right: -60px;
    width: 220px; height: 220px; background: rgba(255,255,255,0.05); border-radius: 50%;
}
.dash-hero::after {
    content: ""; position: absolute; bottom: -40px; right: 80px;
    width: 140px; height: 140px; background: rgba(255,255,255,0.04); border-radius: 50%;
}
.dash-hero-eyebrow {
    display: inline-block; background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.25); color: #ddd6fe !important;
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; border-radius: 20px; padding: 4px 14px; margin-bottom: 14px;
}
.dash-hero-title {
    font-size: 1.9rem; font-weight: 800; color: #ffffff !important;
    letter-spacing: -0.5px; line-height: 1.2; margin-bottom: 6px;
}
.dash-hero-sub { font-size: 1.0rem; color: #c4b5fd !important; font-weight: 500; margin-bottom: 4px; }
.dash-hero-tagline { font-size: 0.88rem; color: rgba(255,255,255,0.6) !important; }
.metric-card {
    background: #ffffff; border: 1px solid #ede9fe; border-top: 3px solid #7c3aed;
    border-radius: 12px; padding: 20px 18px 16px 18px; text-align: center;
    box-shadow: 0 2px 12px rgba(109,40,217,0.08); transition: box-shadow 0.18s, transform 0.18s;
}
.metric-card:hover { box-shadow: 0 6px 20px rgba(109,40,217,0.14); transform: translateY(-2px); }
.metric-card .mc-icon  { font-size: 1.6rem; display: block; margin-bottom: 8px; }
.metric-card .mc-value { font-size: 1.65rem; font-weight: 800; color: #4c1d95; display: block; line-height: 1.1; }
.metric-card .mc-label { font-size: 0.77rem; color: #6b7280; font-weight: 600; margin-top: 4px; display: block; text-transform: uppercase; letter-spacing: 0.05em; }
.mc-assignments { border-top-color: #7c3aed; }
.mc-completed   { border-top-color: #059669; }
.mc-streak      { border-top-color: #f59e0b; }
.mc-time        { border-top-color: #0891b2; }
.mc-progress    { border-top-color: #6366f1; }
.ai-action-tile {
    background: #ffffff; border: 1.5px solid #ddd6fe; border-top: 4px solid #7c3aed;
    border-radius: 14px; padding: 28px 20px 22px 20px; text-align: center;
    box-shadow: 0 2px 12px rgba(109,40,217,0.08);
    transition: box-shadow 0.18s, transform 0.18s, border-color 0.18s; margin-bottom: 8px;
}
.ai-action-tile:hover {
    box-shadow: 0 8px 24px rgba(109,40,217,0.16); transform: translateY(-3px); border-color: #7c3aed;
}
.ai-action-tile-icon { font-size: 2.2rem; display: block; margin-bottom: 10px; }
.ai-action-tile-label { font-size: 1.0rem; font-weight: 700; color: #1e1b4b; display: block; margin-bottom: 4px; }
.ai-action-tile-desc { font-size: 0.78rem; color: #6b7280; line-height: 1.4; }
.section-hd {
    font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.1em; color: #6b7280; margin: 0 0 12px 0;
    display: flex; align-items: center; gap: 10px;
}
.section-hd::after { content: ""; flex: 1; height: 1px; background: #e5e7eb; }
.page-title-bar {
    display: flex; align-items: flex-start; gap: 14px; padding: 16px 20px;
    background: #f5f3ff; border: 1px solid #ddd6fe; border-left: 4px solid #7c3aed;
    border-radius: 0 10px 10px 0; margin-bottom: 24px;
}
.page-title-bar-icon { font-size: 1.6rem; line-height: 1; margin-top: 2px; }
.page-title-bar h2 { margin: 0 0 2px 0 !important; font-size: 1.2rem !important; font-weight: 700 !important; color: #1e1b4b !important; }
.page-title-bar p  { margin: 0 !important; font-size: 0.84rem !important; color: #6b7280 !important; }
.content-card {
    background: #ffffff; border: 1px solid #ede9fe; border-radius: 12px;
    padding: 20px 22px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(109,40,217,0.05);
}
.result-card {
    background: #faf5ff; border: 1px solid #ddd6fe; border-left: 4px solid #7c3aed;
    border-radius: 8px; padding: 20px 22px; margin-bottom: 14px;
    line-height: 1.8; color: #1f2937 !important; font-size: 0.93rem;
}
.result-card * { color: #1f2937 !important; }
/* Explain-only: white bg, black text */
.explain-result-card {
    background: #ffffff !important; border: 1px solid #d1d5db !important;
    border-left: 4px solid #7c3aed !important; border-radius: 8px;
    padding: 20px 22px; margin-bottom: 14px; line-height: 1.8;
    font-size: 0.93rem; color: #000000 !important;
}
.explain-result-card * { color: #000000 !important; background: transparent !important; }
.explain-result-card br { display: block; content: ""; margin: 2px 0; }
.task-item {
    display: flex; align-items: center; gap: 12px; padding: 11px 14px;
    background: #fafafa; border: 1px solid #f0e9ff; border-radius: 8px;
    margin-bottom: 6px; transition: background 0.12s;
}
.task-item:hover { background: #f5f3ff; }
.task-done { background: #f0fdf4 !important; border-color: #bbf7d0 !important; }
.task-done:hover { background: #dcfce7 !important; }
.priority-high   { border-left: 3px solid #ef4444; }
.priority-medium { border-left: 3px solid #f59e0b; }
.priority-low    { border-left: 3px solid #22c55e; }
.session-card {
    display: flex; align-items: flex-start; gap: 12px; padding: 12px 14px;
    background: #fafafa; border: 1px solid #e5e7eb; border-radius: 8px; margin-bottom: 6px;
}
.session-done { background: #f0fdf4; border-color: #bbf7d0; }
.session-subject { font-weight: 700; font-size: 0.9rem; color: #1e1b4b; }
.session-meta { font-size: 0.76rem; color: #6b7280; margin-top: 2px; }
.fc-term {
    background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
    border: 1.5px solid #c4b5fd; border-radius: 14px; padding: 36px 28px;
    text-align: center; font-size: 1.25rem; font-weight: 700; color: #1e1b4b !important;
    margin-bottom: 12px; min-height: 110px; display: flex; align-items: center;
    justify-content: center; box-shadow: 0 4px 16px rgba(124,58,237,0.1);
}
.fc-def {
    background: #f0fdf4; border: 1.5px solid #bbf7d0; border-radius: 12px;
    padding: 18px 24px; color: #14532d !important; margin-bottom: 20px;
    line-height: 1.7; font-size: 0.93rem;
}
.fc-def * { color: #14532d !important; }
.fc-counter {
    text-align: center; font-size: 0.8rem; color: #6b7280 !important;
    margin-bottom: 8px; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase;
}
.quiz-correct {
    background: #f0fdf4; border: 1px solid #86efac; border-radius: 8px;
    padding: 11px 16px; color: #14532d !important; font-weight: 600;
    margin-bottom: 4px; font-size: 0.92rem;
}
.quiz-correct * { color: #14532d !important; }
.quiz-wrong {
    background: #fff1f2; border: 1px solid #fca5a5; border-radius: 8px;
    padding: 11px 16px; color: #7f1d1d !important; margin-bottom: 4px; font-size: 0.92rem;
}
.quiz-wrong * { color: #7f1d1d !important; }
.quiz-explanation {
    background: #fffbeb; border-left: 3px solid #f59e0b; border-radius: 4px;
    padding: 8px 14px; color: #78350f !important; font-size: 0.85rem;
    margin-top: 4px; margin-bottom: 14px;
}
.quiz-explanation * { color: #78350f !important; }
.score-badge {
    display: inline-block; padding: 8px 28px; border-radius: 24px;
    font-size: 1.1rem; font-weight: 800; letter-spacing: 0.02em;
}
.note-card {
    background: #fffbeb; border: 1px solid #fde68a; border-radius: 10px;
    padding: 16px 18px; margin-bottom: 10px; transition: box-shadow 0.15s;
}
.note-card:hover { box-shadow: 0 4px 12px rgba(245,158,11,0.12); }
.note-card h4 { margin: 0 0 6px 0; color: #78350f !important; font-size: 0.95rem; font-weight: 700; }
.note-card p  { margin: 0; color: #92400e !important; font-size: 0.87rem; line-height: 1.65; }
.auth-wrap {
    max-width: 420px; margin: 48px auto 0 auto; background: #ffffff;
    border: 1px solid #ede9fe; border-radius: 16px; padding: 36px 32px;
    box-shadow: 0 8px 32px rgba(109,40,217,0.12);
}
.auth-header { text-align: center; margin-bottom: 24px; }
.auth-header h1 { font-size: 1.7rem; font-weight: 800; color: #1e1b4b; margin: 10px 0 4px 0; letter-spacing: -0.3px; }
.auth-header p  { color: #6b7280; font-size: 0.9rem; margin: 0; }
div[data-testid="stButton"] > button {
    border-radius: 8px !important; font-weight: 600 !important;
    font-size: 0.88rem !important; transition: opacity 0.15s, transform 0.12s !important;
}
div[data-testid="stButton"] > button:hover  { opacity: 0.9 !important; transform: translateY(-1px) !important; }
div[data-testid="stButton"] > button:active { transform: translateY(0) !important; }
div[data-testid="stMetric"] {
    background: #ffffff; border: 1px solid #ede9fe; border-top: 3px solid #7c3aed;
    border-radius: 12px; padding: 16px 14px; box-shadow: 0 2px 8px rgba(109,40,217,0.07);
}
div[data-testid="stMetricLabel"] { font-size: 0.78rem !important; font-weight: 600 !important; color: #6b7280 !important; }
div[data-testid="stMetricValue"] { font-size: 1.6rem !important; font-weight: 800 !important; color: #4c1d95 !important; }
@media (prefers-color-scheme: dark) {
    .dash-hero { background: linear-gradient(135deg, #0f0a1e 0%, #2e1065 60%, #4c1d95 100%); }
    .metric-card { background: #1e1b4b; border-color: #312e81; border-top-color: #7c3aed; }
    .metric-card .mc-value { color: #c4b5fd; }
    .metric-card .mc-label { color: #a5b4fc; }
    .metric-card:hover { box-shadow: 0 6px 20px rgba(124,58,237,0.3); }
    .mc-completed { border-top-color: #059669; }
    .mc-streak    { border-top-color: #f59e0b; }
    .mc-time      { border-top-color: #0891b2; }
    .mc-progress  { border-top-color: #6366f1; }
    .content-card { background: #1e1b4b; border-color: #312e81; }
    .result-card  { background: #1a1040; border-color: #4338ca; }
    .result-card * { color: #e0e7ff !important; }
    .page-title-bar { background: #1a1040; border-color: #4338ca; border-left-color: #7c3aed; }
    .page-title-bar h2 { color: #e0e7ff !important; }
    .page-title-bar p  { color: #a5b4fc !important; }
    .note-card { background: #1c1917; border-color: #78350f; }
    .note-card h4 { color: #fde68a !important; }
    .note-card p  { color: #fef3c7 !important; }
    .task-item { background: #1a1040; border-color: #312e81; }
    .task-item:hover { background: #1e1b4b; }
    .task-done { background: #022c22 !important; border-color: #14532d !important; }
    .session-card { background: #1a1040; border-color: #312e81; }
    .session-done { background: #022c22; border-color: #14532d; }
    .session-subject { color: #e0e7ff; }
    .auth-wrap { background: #1e1b4b; border-color: #312e81; }
    .auth-header h1 { color: #e0e7ff; }
    .auth-header p  { color: #a5b4fc; }
    div[data-testid="stMetric"] { background: #1e1b4b; border-color: #312e81; }
    div[data-testid="stMetricValue"] { color: #c4b5fd !important; }
    .ai-action-tile { background: #1e1b4b; border-color: #312e81; }
    .ai-action-tile-label { color: #e0e7ff; }
    .ai-action-tile-desc  { color: #a5b4fc; }
    .explain-result-card { background: #ffffff !important; color: #000000 !important; }
    .explain-result-card * { color: #000000 !important; background: transparent !important; }
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ALL VALID PAGE NAMES (single source of truth for valid values)
# ══════════════════════════════════════════════════════════════════════════════
_PAGES_GUEST = [
    "🏠 Dashboard",
    "🗂️ AI Flashcards",
    "🧠 AI Quiz",
    "🤖 AI Study Coach",
    "ℹ️ About",
]
_PAGES_AUTH = [
    "🏠 Dashboard",
    "📋 My Tasks",
    "📚 Study Plan",
    "🗂️ AI Flashcards",
    "🧠 AI Quiz",
    "📝 Notes",
    "📊 Analytics",
    "🤖 AI Study Coach",
    "📜 History",
    "ℹ️ About",
]
# Auth overlay pseudo-pages (not in sidebar, but valid values for current_page)
_AUTH_PAGES = {"🔑 Login", "✨ Sign Up"}


# ══════════════════════════════════════════════════════════════════════════════
# Session-state bootstrap
# ══════════════════════════════════════════════════════════════════════════════
def _init_state():
    defaults = {
        # ── Single source of truth for current page ──
        "current_page": "🏠 Dashboard",
        # ── Navigation history (most-recent LAST) ──
        "nav_history": ["🏠 Dashboard"],
        # ── Auth ──
        "user": None,
        "auth_mode": "Sign In",
        # ── Feature state ──
        "explain_result": None, "explain_error": None, "explain_loading": False,
        "summarize_result": None, "summarize_error": None, "summarize_loading": False,
        "quiz_questions": [], "quiz_submitted": False,
        "quiz_answers": {}, "quiz_error": None, "quiz_loading": False,
        "quiz_topic_used": "",
        "flashcards": [], "fc_index": 0, "fc_revealed": False,
        "fc_error": None, "fc_loading": False,
        "dash_action": None, "dash_result": None,
        "dash_error": None, "dash_loading": False,
        "task_edit_id": None,
        "note_edit_id": None,
        "coach_result": None, "coach_error": None, "coach_loading": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ══════════════════════════════════════════════════════════════════════════════
# Navigation helpers  — current_page is the ONE source of truth
# ══════════════════════════════════════════════════════════════════════════════

def _go(page: str) -> None:
    """Navigate to a page: update history and current_page, then rerun."""
    hist = st.session_state.nav_history
    # Avoid consecutive duplicate entries (caused by reruns staying on same page)
    if not hist or hist[-1] != page:
        hist.append(page)
    st.session_state.current_page = page
    st.rerun()


def _go_back() -> None:
    """Go one step back in history. Login/Sign Up always return to Dashboard."""
    cp = st.session_state.current_page
    if cp in _AUTH_PAGES:
        # Auth pages always go straight to Dashboard
        st.session_state.nav_history = ["🏠 Dashboard"]
        st.session_state.current_page = "🏠 Dashboard"
        st.rerun()
        return
    hist = st.session_state.nav_history
    if len(hist) >= 2:
        hist.pop()                              # remove current
        dest = hist[-1]                         # previous is now current
        st.session_state.current_page = dest
        st.rerun()


def _render_back_button() -> None:
    """
    Render ← back button at the very top-left of the main area.
    • On Login/Sign Up: always shows "← Dashboard"
    • On other pages: shows the previous page name, hidden when at root.
    """
    cp = st.session_state.current_page
    if cp in _AUTH_PAGES:
        col_btn, _ = st.columns([1, 6])
        with col_btn:
            if st.button("← Dashboard", key="back_btn", use_container_width=True):
                _go_back()
        return
    hist = st.session_state.nav_history
    if len(hist) < 2:
        return
    prev_label = hist[-2].split(" ", 1)[-1]
    col_btn, _ = st.columns([1, 6])
    with col_btn:
        if st.button(f"← {prev_label}", key="back_btn", use_container_width=True):
            _go_back()


# ══════════════════════════════════════════════════════════════════════════════
# Auth helpers
# ══════════════════════════════════════════════════════════════════════════════
def _uid() -> str | None:
    u = st.session_state.get("user")
    return u["uid"] if u else None


def _save_hist(entry_type: str, user_input: str, result) -> None:
    if not _FIREBASE_AVAILABLE or not _uid():
        return
    uid = _uid()
    if uid is None:
        return
    try:
        save_history(uid, entry_type, user_input, result)
    except Exception:
        pass


def _render_auth_panel(initial_mode: str = "Sign In"):
    _render_back_button()   # "← Dashboard" for auth pages

    st.markdown('<div class="auth-wrap" style="margin-top:8px;">', unsafe_allow_html=True)
    st.markdown(
        '<div class="auth-header">'
        '<span style="font-size:2.2rem;">🎓</span>'
        '<h1>AI Study Buddy</h1>'
        '<p>Sign in to save your progress and access personal features</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    mode = st.radio(
        "auth_mode_sel",
        ["Sign In", "Sign Up", "Reset Password"],
        index=["Sign In", "Sign Up", "Reset Password"].index(initial_mode),
        horizontal=True, label_visibility="collapsed", key="auth_mode_radio",
    )

    email: str = ""
    password: str = ""
    submitted: bool = False
    with st.form("auth_form", clear_on_submit=False):
        email = st.text_input("Email address", placeholder="you@example.com")
        password = ""
        if mode != "Reset Password":
            password = st.text_input("Password", type="password", placeholder="••••••••")
        if mode == "Sign Up":
            st.caption("Password must be at least 6 characters.")
        btn_label = {"Sign In": "Sign In", "Sign Up": "Create Account",
                     "Reset Password": "Send Reset Link"}[mode]
        submitted = st.form_submit_button(btn_label, type="primary", use_container_width=True)

    if submitted:
        email = email.strip()
        if not email:
            st.warning("⚠️ Please enter your email address.")
            return
        if mode != "Reset Password" and not password:
            st.warning("⚠️ Please enter your password.")
            return

        if mode == "Sign In":
            try:
                user = sign_in(email, password)
                st.session_state.user = user
                st.session_state.nav_history = ["🏠 Dashboard"]
                st.session_state.current_page = "🏠 Dashboard"
                if _FIREBASE_AVAILABLE:
                    try:
                        save_profile(user["uid"], user["email"])
                    except Exception:
                        pass
                st.rerun()
            except RuntimeError as exc:
                st.error(str(exc))

        elif mode == "Sign Up":
            try:
                user = sign_up(email, password)
                st.session_state.user = user
                st.session_state.nav_history = ["🏠 Dashboard"]
                st.session_state.current_page = "🏠 Dashboard"
                if _FIREBASE_AVAILABLE:
                    try:
                        save_profile(user["uid"], user["email"])
                    except Exception:
                        pass
                st.success("✅ Account created! Welcome to AI Study Buddy.")
                st.rerun()
            except RuntimeError as exc:
                st.error(str(exc))
        else:
            try:
                send_password_reset(email)
                st.success("✅ Reset email sent — check your inbox.")
            except RuntimeError as exc:
                st.error(str(exc))

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# Sidebar — uses buttons that call _go(), NOT st.radio
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        "<div style='text-align:center; padding:20px 8px 12px 8px;'>"
        "<span style='font-size:2rem;'>🎓</span>"
        "<div style='font-size:1.1rem; font-weight:800; color:#e0e7ff; margin-top:6px;'>AI Study Buddy</div>"
        "<div style='font-size:0.73rem; color:#a5b4fc; margin-top:2px;'>AI Learning Assistant</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<hr>", unsafe_allow_html=True)

    _nav_items = _PAGES_AUTH if (_FIREBASE_AVAILABLE and st.session_state.user) else _PAGES_GUEST
    _cp = st.session_state.current_page

    for _item in _nav_items:
        _label = _item.split(" ", 1)[-1]   # strip emoji for display
        _is_active = (_item == _cp)
        _div_cls = "nav-btn-active" if _is_active else "nav-btn"
        st.markdown(f"<div class='{_div_cls}'>", unsafe_allow_html=True)
        if st.button(_item, key=f"nav_{_item}", use_container_width=True):
            _go(_item)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    if _FIREBASE_AVAILABLE and st.session_state.user:
        _email = st.session_state.user.get("email", "")
        st.markdown(
            f"<div style='font-size:0.75rem; color:#a5b4fc; padding:2px 8px;'>Signed in as</div>"
            f"<div style='font-size:0.82rem; color:#e0e7ff; padding:2px 8px 8px 8px;"
            f"font-weight:600; word-break:break-all;'>{_email}</div>",
            unsafe_allow_html=True,
        )
        if st.button("🚪 Sign Out", use_container_width=True, key="sign_out_btn"):
            st.session_state.user = None
            st.session_state.nav_history = ["🏠 Dashboard"]
            st.session_state.current_page = "🏠 Dashboard"
            for k in ["pyrebase_app", "firestore_db"]:
                st.session_state.pop(k, None)
            st.rerun()
    elif _FIREBASE_AVAILABLE:
        st.markdown(
            "<div style='font-size:0.75rem; color:#a5b4fc; padding:2px 8px 6px 8px;'>"
            "👤 Browsing as guest</div>",
            unsafe_allow_html=True,
        )
        sb_l, sb_r = st.columns(2)
        with sb_l:
            if st.button("🔑 Login", use_container_width=True, key="sb_login"):
                _go("🔑 Login")
        with sb_r:
            if st.button("✨ Sign Up", use_container_width=True, key="sb_signup"):
                _go("✨ Sign Up")
    else:
        st.markdown(
            "<div style='font-size:0.73rem; color:#a5b4fc; padding:4px 8px;'>"
            "Demo mode — AI features available without login.</div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        "<div style='text-align:center; padding-top:8px;'>"
        "<span style='font-size:0.7rem; color:#4338ca;'>© 2025 AI Study Buddy</span>"
        "</div>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════
def _ptb(icon: str, title: str, subtitle: str):
    st.markdown(
        f"<div class='page-title-bar'>"
        f"<div class='page-title-bar-icon'>{icon}</div>"
        f"<div><h2>{title}</h2><p>{subtitle}</p></div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_tasks(task_list: list, uid: str | None, show_complete_btn: bool = True) -> None:
    """Render a list of task items with action buttons. Top-level so uid is explicit."""
    if not task_list:
        st.info("No tasks here.")
        return
    for t in task_list:
        prio     = t.get("priority", "Medium")
        prio_cls = f"priority-{prio.lower()}"
        done_cls = "task-done" if t.get("completed") else ""
        due      = t.get("due_date", "")
        due_str  = f" · Due: {due}" if due else ""
        col_main, col_act = st.columns([4, 1])
        with col_main:
            st.markdown(
                f"<div class='task-item {done_cls} {prio_cls}'>"
                f"<div><div style='font-weight:600; font-size:0.93rem;'>{t['title']}</div>"
                f"<div style='font-size:0.76rem; color:#6b7280;'>{prio}{due_str}</div>"
                f"</div></div>",
                unsafe_allow_html=True,
            )
        with col_act:
            if _FIREBASE_AVAILABLE and uid:
                if show_complete_btn:
                    if st.button("✅", key=f"done_{t['id']}", help="Mark complete"):
                        update_task(uid, t["id"], completed=True)
                        st.rerun()
                else:
                    if st.button("↩️", key=f"undo_{t['id']}", help="Mark pending"):
                        update_task(uid, t["id"], completed=False)
                        st.rerun()
                if st.button("🗑️", key=f"del_{t['id']}", help="Delete"):
                    delete_task(uid, t["id"])
                    st.rerun()


def _render_plan(sessions: list, uid: str | None) -> None:
    """Render study plan session cards with action buttons. Top-level so uid is explicit."""
    if not sessions:
        st.info("No sessions here.")
        return
    for s in sessions:
        col_info, col_btn = st.columns([5, 1])
        done     = s.get("completed", False)
        done_cls = "session-done" if done else ""
        icon     = "✅" if done else "🕐"
        with col_info:
            st.markdown(
                f"<div class='session-card {done_cls}'>"
                f"<span style='font-size:1.1rem; line-height:1;'>{icon}</span>"
                f"<div>"
                f"<div class='session-subject'>{s.get('subject','')} — {s.get('task','')}</div>"
                f"<div class='session-meta'>📅 {s.get('date','')} &nbsp;·&nbsp; ⏱️ {s.get('duration_min',0)} min</div>"
                f"</div></div>",
                unsafe_allow_html=True,
            )
        with col_btn:
            if _FIREBASE_AVAILABLE and uid:
                if not done:
                    if st.button("✅", key=f"sp_done_{s['id']}"):
                        update_study_session(uid, s["id"], completed=True)
                        st.rerun()
                if st.button("🗑️", key=f"sp_del_{s['id']}"):
                    delete_study_session(uid, s["id"])
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# RENDER — driven entirely by st.session_state.current_page
# ══════════════════════════════════════════════════════════════════════════════
_page = st.session_state.current_page

# ── Auth overlay ──────────────────────────────────────────────────────────────
if _page in _AUTH_PAGES:
    if _FIREBASE_AVAILABLE and not _uid():
        _render_auth_panel(initial_mode="Sign In" if _page == "🔑 Login" else "Sign Up")
    else:
        # Already logged in — just go to Dashboard
        _go("🏠 Dashboard")
    st.stop()

# ── Back button (top of every normal page) ────────────────────────────────────
_render_back_button()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE — Dashboard
# ══════════════════════════════════════════════════════════════════════════════
if _page == "🏠 Dashboard":
    uid = _uid()
    if uid:
        st.markdown(
            "<div class='dash-hero'>"
            "<div class='dash-hero-eyebrow'>✨ Your AI-Powered Study Companion</div>"
            "<div class='dash-hero-title'>🎓 AI-Powered Study Buddy</div>"
            "<div class='dash-hero-sub'>Your Personal AI Learning Assistant</div>"
            "<div class='dash-hero-tagline'>Learn Smarter. Study Better. Achieve More.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='dash-hero'>"
            "<div class='dash-hero-eyebrow'>✨ Your AI-Powered Study Companion</div>"
            "<div class='dash-hero-title'>🎓 AI-Powered Study Buddy</div>"
            "<div class='dash-hero-sub'>Your Personal AI Learning Assistant</div>"
            "<div class='dash-hero-tagline' style='margin-top:10px; font-size:0.93rem;"
            " color:rgba(255,255,255,0.85) !important;'>"
            "🚀 Use all AI features as a <strong style='color:#fff;'>guest</strong> — "
            "or <strong style='color:#fff;'>Login / Sign Up</strong> to save your progress."
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        if _FIREBASE_AVAILABLE:
            cta1, cta2, cta3 = st.columns([1, 1, 4])
            with cta1:
                if st.button("🔑 Login", type="primary", use_container_width=True, key="hero_login"):
                    _go("🔑 Login")
            with cta2:
                if st.button("✨ Sign Up", use_container_width=True, key="hero_signup"):
                    _go("✨ Sign Up")

    # ── Metric cards ─────────────────────────────────────────────────────────
    if _FIREBASE_AVAILABLE and uid:
        _analytics = get_analytics(uid)
        _tasks_all = get_tasks(uid)
        total_tasks  = _analytics["total_tasks"]
        completed_t  = _analytics["completed_tasks"]
        study_min    = _analytics["total_study_min"]
        progress_pct = round(completed_t / total_tasks * 100) if total_tasks else 0
    else:
        total_tasks = completed_t = study_min = progress_pct = 0
        _tasks_all = []

    study_hrs = f"{study_min // 60}h {study_min % 60}m" if study_min else "0h 0m"
    streak    = 0

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, icon, val, label, extra_cls in [
        (c1, "📚", total_tasks,        "Total Assignments", "mc-assignments"),
        (c2, "✅", completed_t,         "Completed Tasks",   "mc-completed"),
        (c3, "🔥", f"{streak} days",    "Study Streak",      "mc-streak"),
        (c4, "⏱️", study_hrs,           "Study Time",        "mc-time"),
        (c5, "📈", f"{progress_pct}%",  "Overall Progress",  "mc-progress"),
    ]:
        col.markdown(
            f"<div class='metric-card {extra_cls}'>"
            f"<span class='mc-icon'>{icon}</span>"
            f"<span class='mc-value'>{val}</span>"
            f"<span class='mc-label'>{label}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── CENTER: four AI action tiles ─────────────────────────────────────────
    st.markdown("<div class='section-hd'>AI Tools</div>", unsafe_allow_html=True)
    at1, at2, at3, at4 = st.columns(4)
    for col, icon, label, desc in [
        (at1, "📖", "Explain",    "Explain any concept in simple language"),
        (at2, "📝", "Summarize",  "Condense notes into key points"),
        (at3, "🧠", "AI Quiz",    "Test yourself with AI-generated quizzes"),
        (at4, "🗂️", "Flashcards", "Generate flip-card study sets"),
    ]:
        col.markdown(
            f"<div class='ai-action-tile'>"
            f"<span class='ai-action-tile-icon'>{icon}</span>"
            f"<span class='ai-action-tile-label'>{label}</span>"
            f"<span class='ai-action-tile-desc'>{desc}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Input + action buttons ────────────────────────────────────────────────
    st.markdown(
        "<div class='content-card'>"
        "<p style='font-size:0.9rem; color:#374151; margin:0 0 12px 0; font-weight:600;'>"
        "Enter a topic or paste notes, then choose an action:</p>",
        unsafe_allow_html=True,
    )
    dash_input = st.text_area(
        "dash_input", height=130,
        placeholder="e.g. Photosynthesis, Python loops, World War II causes…",
        label_visibility="collapsed", key="dash_input_area",
    )
    qc1, qc2, qc3, qc4 = st.columns(4)
    with qc1: exp_btn   = st.button("📖 Explain",    use_container_width=True, type="primary", key="dash_exp")
    with qc2: sum_btn   = st.button("📝 Summarize",  use_container_width=True, key="dash_sum")
    with qc3: quiz_btn  = st.button("🧠 Quiz",       use_container_width=True, key="dash_quiz")
    with qc4: flash_btn = st.button("🗂️ Flashcards", use_container_width=True, key="dash_flash")
    st.markdown("</div>", unsafe_allow_html=True)

    triggered = None
    if exp_btn:     triggered = "explain"
    elif sum_btn:   triggered = "summarize"
    elif quiz_btn:  triggered = "quiz"
    elif flash_btn: triggered = "flashcards"

    if triggered:
        raw = dash_input.strip() if dash_input else ""
        if not raw:
            st.warning("⚠️ Please enter a topic or notes first.")
        else:
            st.session_state.dash_action = triggered
            st.session_state.dash_result = None
            st.session_state.dash_error  = None
            with st.spinner("🤖 Generating…"):
                try:
                    if triggered == "explain":
                        r = explain_concept(raw)
                    elif triggered == "summarize":
                        r = summarize_notes(raw)
                    elif triggered == "quiz":
                        r = generate_quiz(raw, 5, "mcq")
                    else:
                        r = generate_flashcards(raw, 6, False)
                    st.session_state.dash_result = r
                    _save_hist(triggered, raw, r)
                except Exception as e:
                    st.session_state.dash_error = friendly_error(e)

    if st.session_state.dash_error:
        st.error(st.session_state.dash_error)

    if st.session_state.dash_result is not None and not st.session_state.dash_error:
        action = st.session_state.dash_action
        result = st.session_state.dash_result
        st.markdown("---")
        if action == "explain" and isinstance(result, str):
            st.markdown("<div class='section-hd'>Explanation</div>", unsafe_allow_html=True)
            st.markdown(
                f'<div class="explain-result-card">{result.replace(chr(10), "<br>")}</div>',
                unsafe_allow_html=True,
            )
        elif action == "summarize" and isinstance(result, str):
            st.markdown("<div class='section-hd'>Summary</div>", unsafe_allow_html=True)
            st.markdown(
                f'<div class="result-card">{result.replace(chr(10), "<br>")}</div>',
                unsafe_allow_html=True,
            )
        elif action == "quiz" and isinstance(result, list):
            st.markdown("<div class='section-hd'>Quiz Preview</div>", unsafe_allow_html=True)
            for q in cast(List[QuizQuestion], result):
                with st.expander(f"Q{q.number}: {q.question}"):
                    if q.is_mcq and q.options:
                        for o in cast(List[MCQOption], q.options):
                            st.markdown(f"{'✅ ' if o.is_correct else ''}**{o.label})** {o.text}")
                    if q.explanation:
                        st.info(f"💬 {q.explanation}")
            st.caption("👉 Use **🧠 AI Quiz** in the sidebar for the full interactive experience.")
        elif action == "flashcards" and isinstance(result, list):
            st.markdown("<div class='section-hd'>Flashcard Preview</div>", unsafe_allow_html=True)
            for card in cast(List[Flashcard], result):
                with st.expander(f"🗂️ {card.term}"):
                    st.markdown(f"**Definition:** {card.definition}")
            st.caption("👉 Use **🗂️ AI Flashcards** in the sidebar for the full flip-card experience.")

    if uid and _tasks_all:
        st.markdown("<br>", unsafe_allow_html=True)
        col_left, col_right = st.columns([1.1, 0.9])
        with col_left:
            st.markdown("<div class='section-hd'>Recent Tasks</div>", unsafe_allow_html=True)
            for t in _tasks_all[:5]:
                done_cls  = "task-done" if t.get("completed") else ""
                prio      = t.get("priority", "Medium")
                prio_cls  = f"priority-{prio.lower()}"
                icon_done = "✅" if t.get("completed") else "⬜"
                st.markdown(
                    f"<div class='task-item {done_cls} {prio_cls}'>"
                    f"{icon_done} <span style='font-size:0.9rem;'>{t['title'][:50]}</span>"
                    f"<span style='margin-left:auto; font-size:0.75rem; color:#9ca3af;'>{prio}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        with col_right:
            st.markdown("<div class='section-hd'>Weekly Study Progress</div>", unsafe_allow_html=True)
            st.progress(min(progress_pct / 100, 1.0))
            st.caption(f"{progress_pct}% of tasks completed")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE — My Tasks
# ══════════════════════════════════════════════════════════════════════════════
elif _page == "📋 My Tasks":
    _ptb("📋", "My Tasks", "Manage your assignments and to-do items.")
    uid = _uid()

    with st.expander("➕ Add New Task", expanded=False):
        with st.form("add_task_form", clear_on_submit=True):
            t_title = st.text_input("Task title", placeholder="e.g. Read Chapter 5")
            tc1, tc2 = st.columns(2)
            with tc1:
                t_priority = st.selectbox("Priority", ["High", "Medium", "Low"])
            with tc2:
                t_due = st.date_input("Due date (optional)", value=None)
            add_submitted = st.form_submit_button("Add Task", type="primary")
        if add_submitted:
            if not t_title.strip():
                st.warning("⚠️ Please enter a task title.")
            elif _FIREBASE_AVAILABLE and uid:
                due_str = str(t_due) if t_due else ""
                add_task(uid, t_title.strip(), t_priority, due_str)
                st.success("✅ Task added!")
                st.rerun()
            else:
                st.info("Configure Firebase to save tasks permanently.")

    if _FIREBASE_AVAILABLE and uid:
        tasks = get_tasks(uid)
    else:
        tasks = []

    pending   = [t for t in tasks if not t.get("completed")]
    completed = [t for t in tasks if t.get("completed")]

    s1, s2, s3, s4 = st.columns(4)
    for col, label, val in [
        (s1, "Total Tasks",  len(tasks)),
        (s2, "Completed",    len(completed)),
        (s3, "Pending",      len(pending)),
        (s4, "Completion %", f"{round(len(completed)/len(tasks)*100) if tasks else 0}%"),
    ]:
        col.metric(label, val)

    st.markdown("---")
    tab_pending, tab_done = st.tabs([f"⬜ Pending ({len(pending)})", f"✅ Completed ({len(completed)})"])

    with tab_pending:
        _render_tasks(pending, uid, show_complete_btn=True)
    with tab_done:
        _render_tasks(completed, uid, show_complete_btn=False)

    if not _FIREBASE_AVAILABLE:
        st.info("🔧 Configure Firebase secrets to enable persistent task storage.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE — Study Plan
# ══════════════════════════════════════════════════════════════════════════════
elif _page == "📚 Study Plan":
    _ptb("📚", "Study Plan", "Plan your study sessions and track progress by subject.")
    uid = _uid()

    with st.expander("➕ Add Study Session", expanded=False):
        with st.form("add_session_form", clear_on_submit=True):
            sc1, sc2 = st.columns(2)
            with sc1:
                sp_subject  = st.text_input("Subject", placeholder="e.g. Mathematics")
                sp_task     = st.text_input("Study task", placeholder="e.g. Practice integration")
            with sc2:
                sp_duration = st.number_input("Duration (minutes)", min_value=5, max_value=480, value=60)
                sp_date     = st.date_input("Date", value=datetime.date.today())
            sp_submitted = st.form_submit_button("Add Session", type="primary")
        if sp_submitted:
            if not sp_subject.strip() or not sp_task.strip():
                st.warning("⚠️ Please fill in subject and task.")
            elif _FIREBASE_AVAILABLE and uid:
                add_study_session(uid, sp_subject, sp_task, sp_duration, str(sp_date))
                st.success("✅ Study session added!")
                st.rerun()
            else:
                st.info("Configure Firebase to save study plan.")

    if _FIREBASE_AVAILABLE and uid:
        plan = get_study_plan(uid)
    else:
        plan = []

    today_str         = str(datetime.date.today())
    today_sessions    = [s for s in plan if s.get("date") == today_str]
    upcoming_sessions = [s for s in plan if s.get("date", "") > today_str]

    m1, m2, m3 = st.columns(3)
    m1.metric("Today's Sessions",    len(today_sessions))
    m2.metric("Upcoming Sessions",   len(upcoming_sessions))
    total_planned_min = sum(s.get("duration_min", 0) for s in plan)
    m3.metric("Total Planned Hours", f"{total_planned_min // 60}h {total_planned_min % 60}m")

    st.markdown("---")
    tab_today, tab_upcoming, tab_all = st.tabs(["📅 Today", "🔜 Upcoming", "📋 All Sessions"])

    with tab_today:    _render_plan(today_sessions, uid)
    with tab_upcoming: _render_plan(upcoming_sessions, uid)
    with tab_all:      _render_plan(plan, uid)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE — AI Flashcards
# ══════════════════════════════════════════════════════════════════════════════
elif _page == "🗂️ AI Flashcards":
    _ptb("🗂️", "AI Flashcards", "Generate and flip through smart flashcards on any topic.")

    source_type = st.radio("Generate from", ["Topic", "My Notes"], horizontal=True)
    from_notes  = source_type == "My Notes"

    if from_notes:
        source = st.text_area("Paste your notes", height=200, placeholder="Paste notes here…")
    else:
        source = st.text_input("Topic", placeholder="e.g. Python data structures, The Solar System…")

    num_cards = st.slider("Number of flashcards", min_value=3, max_value=20, value=8)

    gen_col, reset_col = st.columns([2, 1])
    with gen_col:
        gen_btn = st.button(
            "⏳ Generating…" if st.session_state.fc_loading else "⚡ Generate Flashcards",
            type="primary", disabled=st.session_state.fc_loading, key="fc_gen_btn",
        )
    with reset_col:
        if st.button("🔄 Reset", key="fc_reset"):
            st.session_state.flashcards  = []
            st.session_state.fc_index    = 0
            st.session_state.fc_revealed = False
            st.session_state.fc_error    = None
            st.rerun()

    if gen_btn:
        if not source.strip():
            st.warning("⚠️ Please enter a topic or notes first.")
        elif not st.session_state.fc_loading:
            st.session_state.fc_loading = True
            st.session_state.fc_error   = None
            with st.spinner("Generating flashcards…"):
                try:
                    cards = generate_flashcards(source.strip(), num_cards, from_notes)
                    st.session_state.flashcards  = cards
                    st.session_state.fc_index    = 0
                    st.session_state.fc_revealed = False
                    st.session_state.fc_error    = None
                    _save_hist("flashcards", source.strip(), cards)
                except Exception as e:
                    st.session_state.fc_error = friendly_error(e)
            st.session_state.fc_loading = False

    if st.session_state.fc_error:
        st.error(st.session_state.fc_error)
        if st.button("🔄 Try Again", key="fc_retry"):
            st.session_state.fc_error = None
            st.rerun()

    cards = st.session_state.flashcards
    if cards:
        idx   = st.session_state.fc_index
        card  = cards[idx]
        total = len(cards)

        st.markdown("---")
        st.markdown(f"<div class='fc-counter'>Card {idx+1} of {total}</div>", unsafe_allow_html=True)
        st.progress((idx + 1) / total)
        st.markdown(f'<div class="fc-term">{card.term}</div>', unsafe_allow_html=True)

        if st.session_state.fc_revealed:
            st.markdown(
                f'<div class="fc-def"><b>Definition:</b><br>{card.definition}</div>',
                unsafe_allow_html=True,
            )
            reveal_label = "🙈 Hide Definition"
        else:
            reveal_label = "👁 Reveal Definition"

        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("← Previous", disabled=idx == 0, key="fc_prev"):
                st.session_state.fc_index   -= 1
                st.session_state.fc_revealed = False
                st.rerun()
        with b2:
            if st.button(reveal_label, type="primary", key="fc_reveal"):
                st.session_state.fc_revealed = not st.session_state.fc_revealed
                st.rerun()
        with b3:
            if st.button("Next →", disabled=idx == total - 1, key="fc_next"):
                st.session_state.fc_index   += 1
                st.session_state.fc_revealed = False
                st.rerun()

        if idx == total - 1 and st.session_state.fc_revealed:
            st.success("🎉 You've reviewed all flashcards!")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE — AI Quiz
# ══════════════════════════════════════════════════════════════════════════════
elif _page == "🧠 AI Quiz":
    _ptb("🧠", "AI Quiz", "Generate and take an interactive quiz on any topic.")

    qcol1, qcol2, qcol3 = st.columns([3, 1, 1])
    with qcol1:
        quiz_topic = st.text_input("Topic", placeholder="e.g. World War II, Python functions…")
    with qcol2:
        num_q = st.number_input("Questions", min_value=1, max_value=15, value=5)
    with qcol3:
        q_type = st.selectbox(
            "Type", ["mcq", "short"],
            format_func=lambda x: "Multiple Choice" if x == "mcq" else "Short Answer",
        )

    gc, rc = st.columns([2, 1])
    with gc:
        gen_btn = st.button(
            "⏳ Generating…" if st.session_state.quiz_loading else "⚡ Generate Quiz",
            type="primary", disabled=st.session_state.quiz_loading, key="quiz_gen_btn",
        )
    with rc:
        if st.button("🔄 Reset Quiz", key="quiz_reset"):
            st.session_state.quiz_questions  = []
            st.session_state.quiz_submitted  = False
            st.session_state.quiz_answers    = {}
            st.session_state.quiz_error      = None
            st.session_state.quiz_topic_used = ""
            st.rerun()

    if gen_btn:
        if not quiz_topic.strip():
            st.warning("⚠️ Please enter a topic first.")
        elif not st.session_state.quiz_loading:
            st.session_state.quiz_loading = True
            st.session_state.quiz_error   = None
            with st.spinner("Generating quiz questions…"):
                try:
                    qs = generate_quiz(quiz_topic.strip(), int(num_q), q_type)
                    st.session_state.quiz_questions  = qs
                    st.session_state.quiz_submitted  = False
                    st.session_state.quiz_answers    = {}
                    st.session_state.quiz_error      = None
                    st.session_state.quiz_topic_used = quiz_topic.strip()
                    _save_hist("quiz", quiz_topic.strip(), qs)
                except Exception as e:
                    st.session_state.quiz_error = friendly_error(e)
            st.session_state.quiz_loading = False

    if st.session_state.quiz_error:
        st.error(st.session_state.quiz_error)
        if st.button("🔄 Try Again", key="quiz_retry"):
            st.session_state.quiz_error = None
            st.rerun()

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

        if st.session_state.quiz_submitted:
            st.markdown("<div class='section-hd'>Results</div>", unsafe_allow_html=True)
            score = 0
            for q in questions:
                user_ans = st.session_state.quiz_answers.get(q.number, "")
                if q.is_mcq:
                    correct  = q.correct_answer.upper()
                    is_right = str(user_ans).upper() == correct
                    if is_right:
                        score += 1
                    vcls  = "quiz-correct" if is_right else "quiz-wrong"
                    vicon = "✅" if is_right else "❌"
                    ctxt  = next(
                        (f"{o.label}) {o.text}" for o in q.options if o.label == correct), correct
                    )
                    st.markdown(
                        f'<div class="{vcls}">{vicon} <b>Q{q.number}:</b> {q.question}<br>'
                        f'Your answer: <b>{user_ans}</b> &nbsp;|&nbsp; Correct: <b>{ctxt}</b></div>',
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
                    if st.checkbox(f"I got Q{q.number} right", key=f"self_{q.number}"):
                        score += 1
                st.markdown("")

            total_q = len(questions)
            pct     = int(score / total_q * 100)
            colour  = "#22c55e" if pct >= 70 else "#f59e0b" if pct >= 50 else "#ef4444"
            st.markdown(
                f'<div style="text-align:center; margin-top:20px;">'
                f'<span class="score-badge" style="background:{colour}22; border:2px solid {colour}; color:{colour};">'
                f'Score: {score} / {total_q} &nbsp;({pct}%)</span></div>',
                unsafe_allow_html=True,
            )

            uid = _uid()
            if _FIREBASE_AVAILABLE and uid:
                save_quiz_score(uid, st.session_state.quiz_topic_used, score, total_q, q_type)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE — Notes
# ══════════════════════════════════════════════════════════════════════════════
elif _page == "📝 Notes":
    _ptb("📝", "Notes", "Create, search and manage your study notes.")
    uid = _uid()

    search_q   = st.text_input("🔍 Search notes", placeholder="Search by title or content…", key="note_search")
    edit_id    = st.session_state.note_edit_id
    edit_label = "✏️ Edit Note" if edit_id else "➕ Add New Note"

    with st.expander(edit_label, expanded=edit_id is not None):
        pre_title = pre_content = ""
        if edit_id and _FIREBASE_AVAILABLE and uid:
            all_notes = get_notes(uid)
            for n in all_notes:
                if n["id"] == edit_id:
                    pre_title   = n.get("title", "")
                    pre_content = n.get("content", "")
                    break

        with st.form("note_form", clear_on_submit=True):
            n_title   = st.text_input("Title", value=pre_title, placeholder="Note title")
            n_content = st.text_area("Content", value=pre_content, height=180,
                                     placeholder="Write your notes here…")
            nc1, nc2 = st.columns(2)
            with nc1: save_btn   = st.form_submit_button("💾 Save Note", type="primary")
            with nc2: cancel_btn = st.form_submit_button("Cancel")

        if cancel_btn:
            st.session_state.note_edit_id = None
            st.rerun()

        if save_btn:
            if not n_title.strip() or not n_content.strip():
                st.warning("⚠️ Please fill in both title and content.")
            elif _FIREBASE_AVAILABLE and uid:
                if edit_id:
                    update_note(uid, edit_id, n_title, n_content)
                    st.session_state.note_edit_id = None
                    st.success("✅ Note updated!")
                else:
                    add_note(uid, n_title, n_content)
                    st.success("✅ Note saved!")
                st.rerun()
            else:
                st.info("Configure Firebase to save notes permanently.")

    if _FIREBASE_AVAILABLE and uid:
        all_notes = get_notes(uid)
    else:
        all_notes = []

    if search_q:
        sq = search_q.lower()
        all_notes = [n for n in all_notes
                     if sq in n.get("title", "").lower() or sq in n.get("content", "").lower()]

    if not all_notes:
        st.info("No notes yet. Add your first note above!" if not search_q else "No notes match your search.")
    else:
        st.markdown(f"<div class='section-hd'>{len(all_notes)} Note(s)</div>", unsafe_allow_html=True)
        for n in all_notes:
            col_note, col_btn = st.columns([5, 1])
            with col_note:
                ts     = n.get("updated_at")
                ts_str = ts.strftime("%b %d, %Y") if hasattr(ts, "strftime") else ""
                st.markdown(
                    f"<div class='note-card'>"
                    f"<h4>{n.get('title','Untitled')}"
                    f"<span style='font-size:0.72rem; font-weight:400; color:#9ca3af; margin-left:8px;'>{ts_str}</span>"
                    f"</h4>"
                    f"<p>{n.get('content','')[:200]}{'…' if len(n.get('content','')) > 200 else ''}</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            with col_btn:
                if _FIREBASE_AVAILABLE and uid:
                    if st.button("✏️", key=f"edit_note_{n['id']}", help="Edit"):
                        st.session_state.note_edit_id = n["id"]
                        st.rerun()
                    if st.button("🗑️", key=f"del_note_{n['id']}", help="Delete"):
                        delete_note(uid, n["id"])
                        st.rerun()

    if not _FIREBASE_AVAILABLE:
        st.info("🔧 Configure Firebase secrets to enable persistent notes.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE — Analytics
# ══════════════════════════════════════════════════════════════════════════════
elif _page == "📊 Analytics":
    _ptb("📊", "Analytics", "Track your study performance and progress over time.")
    uid = _uid()

    if not _FIREBASE_AVAILABLE or not uid:
        st.info("🔧 Configure Firebase secrets to view your analytics.")
    else:
        data   = get_analytics(uid)
        scores = data["recent_scores"]

        a1, a2, a3, a4 = st.columns(4)
        study_hrs_str = f"{data['total_study_min'] // 60}h {data['total_study_min'] % 60}m"
        a1.metric("✅ Completed Tasks",  data["completed_tasks"])
        a2.metric("⬜ Pending Tasks",    data["pending_tasks"])
        a3.metric("⏱️ Total Study Time", study_hrs_str)
        a4.metric("🧠 Avg Quiz Score",   f"{data['avg_quiz_pct']}%")

        st.markdown("---")
        col_l, col_r = st.columns(2)

        with col_l:
            st.markdown("<div class='section-hd'>Task Completion</div>", unsafe_allow_html=True)
            total_t = data["total_tasks"]
            if total_t:
                done_pct = round(data["completed_tasks"] / total_t * 100)
                st.progress(done_pct / 100)
                st.caption(f"{done_pct}% of {total_t} tasks completed")
            else:
                st.info("No tasks yet.")
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<div class='section-hd'>Overall Progress</div>", unsafe_allow_html=True)
            overall = round((data["completed_tasks"] / data["total_tasks"] * 100)
                            if data["total_tasks"] else 0)
            st.progress(overall / 100)
            st.caption(f"{overall}% overall")

        with col_r:
            st.markdown("<div class='section-hd'>Recent Quiz Scores</div>", unsafe_allow_html=True)
            if scores:
                for s in scores[:8]:
                    pct    = s.get("pct", 0)
                    colour = "#22c55e" if pct >= 70 else "#f59e0b" if pct >= 50 else "#ef4444"
                    ts     = s.get("timestamp")
                    ts_str = ts.strftime("%b %d") if hasattr(ts, "strftime") else ""
                    st.markdown(
                        f"<div style='display:flex; align-items:center; gap:10px; margin-bottom:8px;'>"
                        f"<div style='flex:1; font-size:0.85rem;'>{s.get('topic','')[:35]}</div>"
                        f"<div style='font-size:0.8rem; color:#6b7280;'>{ts_str}</div>"
                        f"<div style='font-weight:700; color:{colour};'>{pct}%</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No quiz scores yet. Take a quiz to see results.")

        if len(scores) >= 2:
            st.markdown("---")
            st.markdown("<div class='section-hd'>Quiz Score Trend</div>", unsafe_allow_html=True)
            import pandas as pd
            df = pd.DataFrame({
                "Quiz": [f"#{i+1} {s.get('topic','')[:20]}" for i, s in enumerate(reversed(scores[:10]))],
                "Score (%)": [s.get("pct", 0) for s in reversed(scores[:10])],
            }).set_index("Quiz")
            st.bar_chart(df)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE — AI Study Coach
# ══════════════════════════════════════════════════════════════════════════════
elif _page == "🤖 AI Study Coach":
    _ptb("🤖", "AI Study Coach", "Get a personalised study plan and exam strategy from your AI coach.")

    st.markdown(
        "<div class='content-card'>"
        "<p style='font-size:0.93rem; color:#374151;'>"
        "Describe your study situation — upcoming exams, subjects, time available, "
        "or any specific challenge. Your AI coach will create a personalised plan.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    coach_input = st.text_area(
        "Describe your situation", height=160,
        placeholder="e.g. I have a Mathematics and Physics exam in 7 days. "
                    "I'm weak in integration and optics. I can study 4 hours a day.\n\n"
                    "Give me a detailed study plan with daily schedule and revision tips.",
        key="coach_input",
    )

    if st.button(
        "⏳ Generating…" if st.session_state.coach_loading else "🤖 Get My Study Plan",
        type="primary", disabled=st.session_state.coach_loading, key="coach_btn",
    ):
        if not coach_input.strip():
            st.warning("⚠️ Please describe your study situation first.")
        else:
            st.session_state.coach_loading = True
            st.session_state.coach_error   = None
            with st.spinner("Your AI coach is preparing your personalised plan…"):
                try:
                    prompt = f"""You are an expert AI Study Coach for students.

A student has described their situation:
---
{coach_input.strip()}
---

Provide a detailed, structured response with clear sections:

1. **Study Plan Overview** — brief summary
2. **Daily Schedule** — day-by-day breakdown with specific time slots
3. **Priority Topics** — what to focus on most (with reasons)
4. **Study Techniques** — specific methods for each subject/topic
5. **Revision Strategy** — how to revise effectively
6. **Break Schedule** — recommended breaks and rest
7. **Exam Day Tips** — final preparation advice

Use bullet points and short paragraphs. Be specific, practical and encouraging.
Do NOT use markdown code blocks. Use plain text with clear headings."""
                    result = ask(prompt)
                    st.session_state.coach_result = result
                    st.session_state.coach_error  = None
                    _save_hist("coach", coach_input.strip()[:200], result)
                except Exception as e:
                    st.session_state.coach_error = friendly_error(e)
            st.session_state.coach_loading = False

    if st.session_state.coach_error:
        st.error(st.session_state.coach_error)
        if st.button("🔄 Try Again", key="coach_retry"):
            st.session_state.coach_error = None
            st.rerun()

    if st.session_state.coach_result:
        st.markdown("<div class='section-hd'>Your Personalised Study Plan</div>", unsafe_allow_html=True)
        st.markdown(
            f'<div class="result-card">{st.session_state.coach_result.replace(chr(10), "<br>")}</div>',
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE — History
# ══════════════════════════════════════════════════════════════════════════════
elif _page == "📜 History":
    _ptb("📜", "AI History", "Your recent AI-powered study sessions.")
    uid = _uid()

    if not _FIREBASE_AVAILABLE or not uid:
        st.info("🔧 Configure Firebase secrets to view your history.")
    else:
        try:
            entries = load_history(uid, limit=30)
        except Exception as exc:
            st.error(f"Could not load history: {exc}")
            entries = []

        if not entries:
            st.info("No history yet — use any AI feature to get started!")
        else:
            _icons = {"explain": "📖", "summarize": "📝", "quiz": "🧠",
                      "flashcards": "🗂️", "coach": "🤖"}
            for entry in entries:
                etype  = entry.get("type", "")
                icon   = _icons.get(etype, "📄")
                einput = entry.get("input", "")[:60]
                ts     = entry.get("timestamp")
                ts_str = ts.strftime("%b %d, %Y %H:%M") if hasattr(ts, "strftime") else ""
                result_str = entry.get("result", "")
                with st.expander(f"{icon} **{etype.capitalize()}** — {einput}… · {ts_str}"):
                    st.markdown(
                        f'<div class="result-card">{result_str[:1500].replace(chr(10), "<br>")}</div>',
                        unsafe_allow_html=True,
                    )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE — About
# ══════════════════════════════════════════════════════════════════════════════
elif _page == "ℹ️ About":
    _ptb("ℹ️", "About AI Study Buddy", "Learn more about this application.")

    st.markdown(
        """
        <div class="content-card">
          <h4 style="margin-top:0; color:#1e1b4b;">🎓 What is AI Study Buddy?</h4>
          <p>AI Study Buddy is a personal AI-powered learning assistant built for students.
          It uses NVIDIA NIM to help you understand any topic, condense your notes,
          test your knowledge, and revise using flashcards — all from a single, easy-to-use interface.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            """
            <div class="content-card">
              <h4 style="margin-top:0; color:#1e1b4b;">✨ Features</h4>
              <ul style="margin:0; padding-left:18px; line-height:2;">
                <li>🏠 <strong>Dashboard</strong> — productivity overview</li>
                <li>📋 <strong>My Tasks</strong> — task management</li>
                <li>📚 <strong>Study Plan</strong> — schedule &amp; tracking</li>
                <li>🗂️ <strong>AI Flashcards</strong> — flip-card study</li>
                <li>🧠 <strong>AI Quiz</strong> — MCQ &amp; short-answer</li>
                <li>📝 <strong>Notes</strong> — persistent note-taking</li>
                <li>📊 <strong>Analytics</strong> — progress tracking</li>
                <li>🤖 <strong>AI Study Coach</strong> — personalised plans</li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_b:
        st.markdown(
            """
            <div class="content-card">
              <h4 style="margin-top:0; color:#1e1b4b;">🛠️ Technology Stack</h4>
              <p style="line-height:2.2;">
                <span style="background:#ede9fe; color:#4c1d95; border-radius:20px; padding:2px 10px; font-size:0.8rem; font-weight:600; margin:2px;">Python 3.14</span>
                <span style="background:#ede9fe; color:#4c1d95; border-radius:20px; padding:2px 10px; font-size:0.8rem; font-weight:600; margin:2px;">Streamlit</span>
                <span style="background:#ede9fe; color:#4c1d95; border-radius:20px; padding:2px 10px; font-size:0.8rem; font-weight:600; margin:2px;">NVIDIA NIM</span>
                <span style="background:#ede9fe; color:#4c1d95; border-radius:20px; padding:2px 10px; font-size:0.8rem; font-weight:600; margin:2px;">Firebase Auth</span>
                <span style="background:#ede9fe; color:#4c1d95; border-radius:20px; padding:2px 10px; font-size:0.8rem; font-weight:600; margin:2px;">Firestore</span>
                <span style="background:#ede9fe; color:#4c1d95; border-radius:20px; padding:2px 10px; font-size:0.8rem; font-weight:600; margin:2px;">pyrebase4</span>
                <span style="background:#ede9fe; color:#4c1d95; border-radius:20px; padding:2px 10px; font-size:0.8rem; font-weight:600; margin:2px;">firebase-admin</span>
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        "<div style='text-align:center; color:#6b7280; font-size:0.83rem; margin-top:24px; "
        "padding-top:16px; border-top:1px solid #e5e7eb;'>"
        "Built with ❤️ using <strong>Streamlit</strong> &amp; <strong>NVIDIA NIM AI</strong>"
        "</div>",
        unsafe_allow_html=True,
    )
