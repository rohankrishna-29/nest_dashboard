import streamlit as st

# ---------------------------------------------------------------------------
# Credentials — replace this with a proper user store / env variables later
# ---------------------------------------------------------------------------

USERS = {
    "admin": {"password": "1234", "role": "admin", "display_name": "Admin"},
    "user": {"password": "password", "role": "viewer", "display_name": "Viewer"},
}

# ---------------------------------------------------------------------------
# Session state helpers
# ---------------------------------------------------------------------------

def init_auth():
    """
    Initialises auth-related session state keys if they don't exist yet.
    Call this at the top of every page.
    """
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = None
    if "role" not in st.session_state:
        st.session_state["role"] = None
    if "display_name" not in st.session_state:
        st.session_state["display_name"] = None


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

    if username not in USERS:
        return False, "Invalid username or password."

    if USERS[username]["password"] != password:
        return False, "Invalid username or password."

    st.session_state["authenticated"] = True
    st.session_state["username"] = username
    st.session_state["role"] = USERS[username]["role"]
    st.session_state["display_name"] = USERS[username]["display_name"]

    return True, ""


def logout():
    """
    Clears all auth session state keys.
    """
    for key in ["authenticated", "username", "role", "display_name"]:
        st.session_state[key] = None
    st.session_state["authenticated"] = False


# ---------------------------------------------------------------------------
# Page guard — call this at the top of every page that needs auth
# ---------------------------------------------------------------------------

def require_auth():
    """
    If the user is not authenticated, stops the page and shows a message.
    Place this at the very top of each page in pages/.

    Usage:
        from src.auth import require_auth
        require_auth()
        # rest of page code only runs if authenticated
    """
    init_auth()

    if not is_authenticated():
        st.warning("Please log in to access this page.")
        st.markdown("[Go to Login](/) ")
        st.stop()
