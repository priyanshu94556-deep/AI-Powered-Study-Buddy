"""
Firebase Authentication wrapper using pyrebase4 (REST API).

Handles email/password sign-up, sign-in, sign-out, and password-reset.
All functions return a plain dict or raise a RuntimeError with a
clean, user-readable message — never raw Firebase JSON.
"""

import re
import streamlit as st

# ── Lazy initialisation ───────────────────────────────────────────────────────
# pyrebase is initialised once per Streamlit session and cached in st.session_state.

def _get_firebase_app():
    """Return a cached pyrebase Firebase app, initialised from st.secrets."""
    if "pyrebase_app" not in st.session_state:
        import pyrebase  # lazy import so non-auth pages don't pay the cost

        config = {
            "apiKey":            st.secrets["firebase"]["api_key"],
            "authDomain":        st.secrets["firebase"]["auth_domain"],
            "projectId":         st.secrets["firebase"]["project_id"],
            "storageBucket":     st.secrets["firebase"].get("storage_bucket", ""),
            "messagingSenderId": st.secrets["firebase"].get("messaging_sender_id", ""),
            "appId":             st.secrets["firebase"]["app_id"],
            "databaseURL":       st.secrets["firebase"].get("database_url", ""),
        }
        st.session_state.pyrebase_app = pyrebase.initialize_app(config)

    return st.session_state.pyrebase_app


def _auth():
    """Return the pyrebase Auth object."""
    return _get_firebase_app().auth()


# ── Error helpers ─────────────────────────────────────────────────────────────

_ERROR_MAP = {
    "EMAIL_EXISTS":             "An account with this email already exists.",
    "EMAIL_NOT_FOUND":          "No account found with that email address.",
    "INVALID_PASSWORD":         "Incorrect password. Please try again.",
    "INVALID_EMAIL":            "That doesn't look like a valid email address.",
    "WEAK_PASSWORD":            "Password must be at least 6 characters.",
    "USER_DISABLED":            "This account has been disabled.",
    "TOO_MANY_ATTEMPTS_TRY_LATER": "Too many failed attempts. Please try again later.",
    "INVALID_LOGIN_CREDENTIALS": "Incorrect email or password.",
    "INVALID_ID_TOKEN":         "Your session has expired. Please sign in again.",
}

def _friendly(exc: Exception) -> str:
    msg = str(exc)
    for key, human in _ERROR_MAP.items():
        if key in msg:
            return human
    # Strip anything that looks like raw JSON
    clean = re.sub(r'\{.*', '', msg, flags=re.DOTALL).strip(" .'\"")
    return clean if clean else "An unexpected error occurred. Please try again."


# ── Public API ────────────────────────────────────────────────────────────────

def sign_up(email: str, password: str) -> dict:
    """
    Create a new account.
    Returns user dict with keys: uid, email, id_token, refresh_token.
    Raises RuntimeError on failure.
    """
    try:
        user = _auth().create_user_with_email_and_password(email, password)
        return {
            "uid":           user["localId"],
            "email":         user["email"],
            "id_token":      user["idToken"],
            "refresh_token": user["refreshToken"],
        }
    except Exception as exc:
        raise RuntimeError(_friendly(exc)) from exc


def sign_in(email: str, password: str) -> dict:
    """
    Sign in an existing account.
    Returns user dict with keys: uid, email, id_token, refresh_token.
    Raises RuntimeError on failure.
    """
    try:
        user = _auth().sign_in_with_email_and_password(email, password)
        return {
            "uid":           user["localId"],
            "email":         user["email"],
            "id_token":      user["idToken"],
            "refresh_token": user["refreshToken"],
        }
    except Exception as exc:
        raise RuntimeError(_friendly(exc)) from exc


def send_password_reset(email: str) -> None:
    """
    Send a password-reset email.
    Raises RuntimeError on failure.
    """
    try:
        _auth().send_password_reset_email(email)
    except Exception as exc:
        raise RuntimeError(_friendly(exc)) from exc


def refresh_token(refresh_tok: str) -> dict:
    """
    Refresh an expired id_token.
    Returns updated dict with id_token and refresh_token.
    Raises RuntimeError on failure.
    """
    try:
        refreshed = _auth().refresh(refresh_tok)
        return {
            "id_token":      refreshed["idToken"],
            "refresh_token": refreshed["refreshToken"],
        }
    except Exception as exc:
        raise RuntimeError(_friendly(exc)) from exc
