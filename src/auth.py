import streamlit as st
import bcrypt
import re

# ---------------------------------------------------------------------------
# Password Policy
# ---------------------------------------------------------------------------
PASSWORD_POLICY = {
    "min_length": 8,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_digit": True,
    "require_special": True,
    "special_chars": r"[!@#$%^&*(),.?\":{}|<>]",
}

def validate_password(password: str) -> tuple[bool, str]:
    """
    Validates password against policy.
    Returns (is_valid, error_message).
    """
    if len(password) < PASSWORD_POLICY["min_length"]:
        return False, f"Password must be at least {PASSWORD_POLICY['min_length']} characters long."
    if PASSWORD_POLICY["require_uppercase"] and not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter (e.g. A–Z)."
    if PASSWORD_POLICY["require_lowercase"] and not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter (e.g. a–z)."
    if PASSWORD_POLICY["require_digit"] and not re.search(r"\d", password):
        return False, "Password must contain at least one number (e.g. 0–9)."
    if PASSWORD_POLICY["require_special"] and not re.search(PASSWORD_POLICY["special_chars"], password):
        return False, "Password must contain at least one special character (e.g. @, #, !, $)."
    return True, ""


# ---------------------------------------------------------------------------
# Credentials — passwords are bcrypt-hashed
# To add a new user, hash their password:
#   import bcrypt; bcrypt.hashpw(b"Nest@123", bcrypt.gensalt())
# ---------------------------------------------------------------------------
USERS = {
    "admin": {
        "password_hash": bcrypt.hashpw(b"Nestdigital@123", bcrypt.gensalt()),
        "role": "admin",
        "display_name": "Admin",
    },
    "user": {
        "password_hash": bcrypt.hashpw(b"Nestdigital@123", bcrypt.gensalt()),
        "role": "viewer",
        "display_name": "Viewer",
    },
}

# ---------------------------------------------------------------------------
# Session state helpers
# ---------------------------------------------------------------------------
def init_auth():
    """
    Initialises auth-related session state keys if they don't exist yet.
    Call this at the top of every page.
    """
    defaults = {
        "authenticated": False,
        "username": None,
        "role": None,
        "display_name": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False)


def get_current_user() -> dict:
    return {
        "username": st.session_state.get("username"),
        "role": st.session_state.get("role"),
        "display_name": st.session_state.get("display_name"),
    }


def login(username: str, password: str) -> tuple[bool, str]:
    """
    Validates credentials and sets session state on success.
    Returns (success, error_message).
    """
    username = username.strip()

    if not username or not password:
        return False, "Please enter both username and password."

    # Check password policy first — gives specific, helpful feedback
    is_valid, policy_error = validate_password(password)
    if not is_valid:
        return False, policy_error

    if username not in USERS:
        return False, "Invalid username or password."

    user = USERS[username]
    password_bytes = password.encode("utf-8")

    stored_hash = user["password_hash"]
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode("utf-8")

    if not bcrypt.checkpw(password_bytes, stored_hash):
        return False, "Invalid username or password."

    st.session_state["authenticated"] = True
    st.session_state["username"] = username
    st.session_state["role"] = user["role"]
    st.session_state["display_name"] = user["display_name"]
    return True, ""


def logout():
    """
    Clears all auth-related session state keys.
    """
    for key in ["authenticated", "username", "role", "display_name"]:
        if key in st.session_state:
            del st.session_state[key]


# ---------------------------------------------------------------------------
# Page guard — call this at the top of every page that needs auth
# ---------------------------------------------------------------------------
def require_auth():
    """
    If the user is not authenticated, stops the page and redirects to home.
    Place this at the very top of each page in pages/.

    Usage:
        from src.auth import require_auth
        require_auth()
        # rest of page code only runs if authenticated
    """
    init_auth()
    if not is_authenticated():
        st.warning("Please log in to access this page.")
        st.switch_page("app.py")
        st.stop()