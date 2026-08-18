"""
Firestore persistent storage wrapper using firebase-admin.

Manages all per-user data: profile, history, tasks, notes, study plan,
quiz scores, flashcard progress, analytics, and study time.

The Admin SDK is initialised once per process from service-account
credentials stored in st.secrets["firebase_service_account"].
Every public function is non-critical — it silently swallows errors so
a Firestore outage never crashes the main application.
"""

import json
import datetime
import streamlit as st

# ── Lazy Admin SDK initialisation ─────────────────────────────────────────────

def _get_db():
    """Return a cached Firestore client, initialising the Admin SDK if needed."""
    if "firestore_db" not in st.session_state:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if not firebase_admin._apps:
            sa_info = dict(st.secrets["firebase_service_account"])
            # Secrets store private_key with literal \n — expand them
            sa_info["private_key"] = sa_info["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(sa_info)
            firebase_admin.initialize_app(cred)

        st.session_state.firestore_db = firestore.client()

    return st.session_state.firestore_db


def _user_ref(uid: str):
    """Convenience: return the user's top-level Firestore document reference."""
    return _get_db().collection("users").document(uid)


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


# ══════════════════════════════════════════════════════════════════════════════
# Profile
# ══════════════════════════════════════════════════════════════════════════════

def save_profile(uid: str, email: str, display_name: str = "") -> None:
    """Upsert the user's profile document."""
    try:
        _user_ref(uid).set(
            {"email": email, "display_name": display_name, "updated_at": _now()},
            merge=True,
        )
    except Exception:
        pass


def get_profile(uid: str) -> dict:
    """Return the user's profile dict, or {} on any error."""
    try:
        doc = _user_ref(uid).get()
        return doc.to_dict() if doc.exists else {}
    except Exception:
        return {}


# ══════════════════════════════════════════════════════════════════════════════
# AI History  (explain / summarize / quiz / flashcards)
# ══════════════════════════════════════════════════════════════════════════════

def save_history(uid: str, entry_type: str, user_input: str, result) -> None:
    """Persist one AI activity record."""
    try:
        doc = {
            "type":      entry_type,
            "input":     user_input[:500],
            "result":    _serialise(entry_type, result),
            "timestamp": _now(),
        }
        _user_ref(uid).collection("history").add(doc)
    except Exception:
        pass


def load_history(uid: str, limit: int = 25) -> list:
    """Return the *limit* most-recent history entries."""
    try:
        docs = (
            _user_ref(uid).collection("history")
            .order_by("timestamp", direction="DESCENDING")
            .limit(limit)
            .stream()
        )
        return [{"id": d.id, **d.to_dict()} for d in docs]
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════════════════
# Tasks
# ══════════════════════════════════════════════════════════════════════════════

def add_task(uid: str, title: str, priority: str = "Medium",
             due_date: str = "") -> str | None:
    """Create a task. Returns the new document ID or None on error."""
    try:
        doc = {
            "title":     title.strip(),
            "priority":  priority,
            "due_date":  due_date,
            "completed": False,
            "created_at": _now(),
            "updated_at": _now(),
        }
        _, ref = _user_ref(uid).collection("tasks").add(doc)
        return ref.id
    except Exception:
        return None


def get_tasks(uid: str) -> list:
    """Return all tasks for the user, sorted by creation date desc."""
    try:
        docs = (
            _user_ref(uid).collection("tasks")
            .order_by("created_at", direction="DESCENDING")
            .stream()
        )
        return [{"id": d.id, **d.to_dict()} for d in docs]
    except Exception:
        return []


def update_task(uid: str, task_id: str, **fields) -> None:
    """Update arbitrary fields on a task (e.g. completed=True, title=...)."""
    try:
        fields["updated_at"] = _now()
        _user_ref(uid).collection("tasks").document(task_id).update(fields)
    except Exception:
        pass


def delete_task(uid: str, task_id: str) -> None:
    """Delete a task permanently."""
    try:
        _user_ref(uid).collection("tasks").document(task_id).delete()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# Notes
# ══════════════════════════════════════════════════════════════════════════════

def add_note(uid: str, title: str, content: str) -> str | None:
    """Create a note. Returns the new document ID or None on error."""
    try:
        doc = {
            "title":      title.strip(),
            "content":    content.strip(),
            "created_at": _now(),
            "updated_at": _now(),
        }
        _, ref = _user_ref(uid).collection("notes").add(doc)
        return ref.id
    except Exception:
        return None


def get_notes(uid: str) -> list:
    """Return all notes, sorted by last-updated desc."""
    try:
        docs = (
            _user_ref(uid).collection("notes")
            .order_by("updated_at", direction="DESCENDING")
            .stream()
        )
        return [{"id": d.id, **d.to_dict()} for d in docs]
    except Exception:
        return []


def update_note(uid: str, note_id: str, title: str, content: str) -> None:
    """Overwrite a note's title and content."""
    try:
        _user_ref(uid).collection("notes").document(note_id).update(
            {"title": title.strip(), "content": content.strip(), "updated_at": _now()}
        )
    except Exception:
        pass


def delete_note(uid: str, note_id: str) -> None:
    try:
        _user_ref(uid).collection("notes").document(note_id).delete()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# Study Plan
# ══════════════════════════════════════════════════════════════════════════════

def add_study_session(uid: str, subject: str, task: str,
                       duration_min: int, date: str) -> str | None:
    """Create a study session entry."""
    try:
        doc = {
            "subject":      subject.strip(),
            "task":         task.strip(),
            "duration_min": duration_min,
            "date":         date,
            "completed":    False,
            "created_at":   _now(),
        }
        _, ref = _user_ref(uid).collection("study_plan").add(doc)
        return ref.id
    except Exception:
        return None


def get_study_plan(uid: str) -> list:
    """Return all study-plan entries."""
    try:
        docs = (
            _user_ref(uid).collection("study_plan")
            .order_by("date")
            .stream()
        )
        return [{"id": d.id, **d.to_dict()} for d in docs]
    except Exception:
        return []


def update_study_session(uid: str, session_id: str, **fields) -> None:
    try:
        _user_ref(uid).collection("study_plan").document(session_id).update(fields)
    except Exception:
        pass


def delete_study_session(uid: str, session_id: str) -> None:
    try:
        _user_ref(uid).collection("study_plan").document(session_id).delete()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# Quiz scores
# ══════════════════════════════════════════════════════════════════════════════

def save_quiz_score(uid: str, topic: str, score: int,
                    total: int, quiz_type: str = "mcq") -> None:
    """Persist a quiz result."""
    try:
        doc = {
            "topic":      topic[:200],
            "score":      score,
            "total":      total,
            "pct":        round(score / total * 100) if total else 0,
            "quiz_type":  quiz_type,
            "timestamp":  _now(),
        }
        _user_ref(uid).collection("quiz_scores").add(doc)
    except Exception:
        pass


def get_quiz_scores(uid: str, limit: int = 20) -> list:
    """Return recent quiz scores."""
    try:
        docs = (
            _user_ref(uid).collection("quiz_scores")
            .order_by("timestamp", direction="DESCENDING")
            .limit(limit)
            .stream()
        )
        return [{"id": d.id, **d.to_dict()} for d in docs]
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════════════════
# Study time  (log increments in minutes)
# ══════════════════════════════════════════════════════════════════════════════

def log_study_time(uid: str, minutes: int, subject: str = "") -> None:
    """Log a study-time increment."""
    try:
        _user_ref(uid).collection("study_time").add(
            {"minutes": minutes, "subject": subject, "timestamp": _now()}
        )
    except Exception:
        pass


def get_total_study_time(uid: str) -> int:
    """Return cumulative study minutes for the user."""
    try:
        docs = _user_ref(uid).collection("study_time").stream()
        return sum(d.to_dict().get("minutes", 0) for d in docs)
    except Exception:
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# Analytics helper  (aggregate from multiple sub-collections)
# ══════════════════════════════════════════════════════════════════════════════

def get_analytics(uid: str) -> dict:
    """
    Return a summary dict for the Analytics page.
    Falls back gracefully — never raises.
    """
    try:
        tasks   = get_tasks(uid)
        scores  = get_quiz_scores(uid, limit=50)
        total_min = get_total_study_time(uid)

        completed   = [t for t in tasks if t.get("completed")]
        pending     = [t for t in tasks if not t.get("completed")]
        avg_quiz    = (sum(s.get("pct", 0) for s in scores) / len(scores)) if scores else 0

        return {
            "total_tasks":    len(tasks),
            "completed_tasks": len(completed),
            "pending_tasks":  len(pending),
            "total_study_min": total_min,
            "quiz_count":     len(scores),
            "avg_quiz_pct":   round(avg_quiz, 1),
            "recent_scores":  scores[:10],
        }
    except Exception:
        return {
            "total_tasks": 0, "completed_tasks": 0, "pending_tasks": 0,
            "total_study_min": 0, "quiz_count": 0, "avg_quiz_pct": 0.0,
            "recent_scores": [],
        }


# ══════════════════════════════════════════════════════════════════════════════
# Internal serialiser
# ══════════════════════════════════════════════════════════════════════════════

def _serialise(entry_type: str, result) -> str:
    """Convert AI result objects to a JSON-safe string for Firestore."""
    if isinstance(result, str):
        return result[:4000]
    if entry_type == "quiz" and isinstance(result, list):
        rows = [{"number": q.number, "question": q.question,
                 "answer": q.correct_answer, "is_mcq": q.is_mcq}
                for q in result]
        return json.dumps(rows, ensure_ascii=False)[:4000]
    if entry_type == "flashcards" and isinstance(result, list):
        rows = [{"term": c.term, "definition": c.definition} for c in result]
        return json.dumps(rows, ensure_ascii=False)[:4000]
    return str(result)[:4000]
