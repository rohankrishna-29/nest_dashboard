import streamlit as st
from src.auth import init_auth, login

LOGO_URL = "https://learning.nestdigital.com/pluginfile.php/1/theme_edash/main_logo/1771222660/LogoNeST.png"


def render_login_page():
    """
    Renders the NeST login page.
    On successful login, sets session state and triggers a rerun
    so app.py redirects to the dashboard automatically.
    """
    init_auth()

    st.markdown("""
    <style>
    [data-testid="stForm"] {
        border: none !important;
        background: transparent !important;
    }

    .stApp {
        background: linear-gradient(-45deg, #1f3c88, #e63946, #3b82f6, #f1f1f1);
        background-size: 400% 400%;
        animation: gradientMove 12s ease infinite;
    }

    @keyframes gradientMove {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    label {
        color: white !important;
        font-weight: bold;
    }

    .stAlert {
        background-color: rgba(255, 255, 255, 0.95) !important;
        border-left: 6px solid #e63946 !important;
        color: #b00020 !important;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        f"""
        <div style="text-align:center; padding-top: 60px;">
            <img src="{LOGO_URL}" width="300">
            <h2 style="color:white; margin-top:10px; letter-spacing: 2px;">LOGIN PORTAL</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            username = st.text_input("Username / E-Mail")
            password = st.text_input("Password", type="password")

        _, col_btn, _ = st.columns([3, 1, 3])
        with col_btn:
            submitted = st.form_submit_button("LOGIN", use_container_width=True)

        st.markdown(
            "<p style='text-align:center; color:white; margin-top: 8px;'>"
            "Don't have an account? "
            "<a href='/Sign_up' style='color:#ffd166; font-weight:bold;'>Sign up</a></p>",
            unsafe_allow_html=True,
        )

    if submitted:
        if not username or not password:
            st.error("Please enter both username and password.")
        else:
            success, error_msg = login(username, password)
            if success:
                st.success(f"Welcome back, {st.session_state['display_name']}!")
                # Small pause so the user sees the success message, then rerun
                # to let app.py redirect to the dashboard
                st.rerun()
            else:
                st.error(error_msg)
