import streamlit as st
import os
from src.auth import init_auth, login

LOGO_URL = "https://learning.nestdigital.com/pluginfile.php/1/theme_edash/main_logo/1771222660/LogoNeST.png"


def render_login_page():
    """
    Renders the NeST Digital Academy login page.
    Clean glassmorphism design — HTML used only for styling, never wrapping Streamlit widgets.
    """
    init_auth()

    # ── All CSS + background + particles (no wrapping divs around widgets) ──
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Inter:wght@300;400;500&display=swap');

    html, body, [data-testid="stAppViewContainer"], .stApp {
        margin: 0; padding: 0;
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: #0a0f1e !important;
        min-height: 100vh;
    }

    .stApp::before {
        content: '';
        position: fixed;
        inset: 0;
        background:
            radial-gradient(ellipse 80% 60% at 20% 20%, rgba(30, 64, 175, 0.5) 0%, transparent 60%),
            radial-gradient(ellipse 60% 50% at 80% 80%, rgba(220, 38, 38, 0.3) 0%, transparent 55%),
            radial-gradient(ellipse 50% 40% at 60% 10%, rgba(59, 130, 246, 0.2) 0%, transparent 50%);
        animation: meshShift 14s ease-in-out infinite alternate;
        z-index: 0;
        pointer-events: none;
    }

    @keyframes meshShift {
        0%   { opacity: 1; transform: scale(1); }
        100% { opacity: 0.8; transform: scale(1.05); }
    }

    /* Hide Streamlit chrome */
    #MainMenu, footer, header,
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"] { display: none !important; }

    /* Center the entire block container */
    [data-testid="stAppViewContainer"] > .main {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
        position: relative;
        z-index: 1;
        padding: 0 20px !important;
    }

    [data-testid="stAppViewContainer"] > .main > .block-container {
        width: 100%;
        max-width: 400px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        padding: 48px 40px 40px !important;
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(255, 255, 255, 0.09) !important;
        border-radius: 24px !important;
        backdrop-filter: blur(24px) !important;
        -webkit-backdrop-filter: blur(24px) !important;
        box-shadow:
            0 0 0 1px rgba(255,255,255,0.03),
            0 32px 64px rgba(0,0,0,0.55),
            0 0 80px rgba(37, 99, 235, 0.08) !important;
        animation: cardIn 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
    }

    @keyframes cardIn {
        from { opacity: 0; transform: translateY(28px) scale(0.97); }
        to   { opacity: 1; transform: translateY(0) scale(1); }
    }

    /* Labels */
    label, .stTextInput label, [data-testid="stWidgetLabel"] {
        font-size: 11px !important;
        font-weight: 500 !important;
        color: rgba(148, 163, 184, 0.85) !important;
        letter-spacing: 0.9px !important;
        text-transform: uppercase !important;
    }

    /* Input fields */
    [data-testid="stTextInput"] input {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.10) !important;
        border-radius: 10px !important;
        color: #f1f5f9 !important;
        font-size: 14px !important;
        font-family: 'Inter', sans-serif !important;
        padding: 12px 16px !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
        caret-color: #3b82f6 !important;
    }

    [data-testid="stTextInput"] input:focus {
        border-color: rgba(59, 130, 246, 0.55) !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12) !important;
        background: rgba(255, 255, 255, 0.07) !important;
        outline: none !important;
    }

    [data-testid="stTextInput"] input::placeholder {
        color: rgba(148, 163, 184, 0.3) !important;
    }

    /* Form container */
    [data-testid="stForm"] {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }

    /* Submit button */
    [data-testid="stFormSubmitButton"] button {
        width: 100% !important;
        background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 60%, #1e40af 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 13px 24px !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        letter-spacing: 1.4px !important;
        text-transform: uppercase !important;
        cursor: pointer !important;
        transition: all 0.25s ease !important;
        margin-top: 8px !important;
        box-shadow: 0 4px 20px rgba(37, 99, 235, 0.35) !important;
    }

    [data-testid="stFormSubmitButton"] button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 28px rgba(37, 99, 235, 0.55) !important;
    }

    [data-testid="stFormSubmitButton"] button:active {
        transform: translateY(0) !important;
    }

    /* Alerts */
    [data-testid="stAlert"] {
        border-radius: 10px !important;
        font-size: 13px !important;
        margin-top: 4px !important;
    }

    /* Particles */
    .particles {
        position: fixed;
        inset: 0;
        overflow: hidden;
        pointer-events: none;
        z-index: 0;
    }
    .dot {
        position: absolute;
        width: 2px; height: 2px;
        border-radius: 50%;
        background: rgba(59, 130, 246, 0.55);
        animation: dotDrift linear infinite;
    }
    @keyframes dotDrift {
        from { transform: translateY(100vh); opacity: 0; }
        10%  { opacity: 1; }
        90%  { opacity: 0.3; }
        to   { transform: translateY(-10vh) translateX(var(--dx, 20px)); opacity: 0; }
    }
    </style>

    <!-- Particles -->
    <div class="particles">
      <div class="dot" style="left:8%;  animation-duration:20s; animation-delay:0s;  --dx:25px;"></div>
      <div class="dot" style="left:22%; animation-duration:25s; animation-delay:4s;  --dx:-20px; background:rgba(239,68,68,0.4);"></div>
      <div class="dot" style="left:50%; animation-duration:18s; animation-delay:8s;  --dx:15px;"></div>
      <div class="dot" style="left:70%; animation-duration:22s; animation-delay:2s;  --dx:-30px; background:rgba(239,68,68,0.35);"></div>
      <div class="dot" style="left:88%; animation-duration:28s; animation-delay:6s;  --dx:20px;"></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Logo ──
    st.markdown(f"""
        <div style="text-align:center; margin-bottom:6px;">
            <img src="{LOGO_URL}" style="height:50px; object-fit:contain; opacity:0.95;">
        </div>
        <div style="width:40px; height:2px; background:linear-gradient(90deg,#2563eb,#ef4444);
                    border-radius:2px; margin:16px auto 24px;">
        </div>
        <div style="text-align:center; margin-bottom:28px;">
            <p style="font-family:'Outfit',sans-serif; font-size:22px; font-weight:600;
                      color:#f1f5f9; margin:0 0 6px; letter-spacing:0.3px;">Welcome Back</p>
            <p style="font-size:13px; color:rgba(148,163,184,0.8); margin:0; font-weight:300;">
                Sign in to your Analytics Dashboard
            </p>
        </div>
    """, unsafe_allow_html=True)

    # ── Form ──
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submitted = st.form_submit_button("Sign In →")

    # ── Footer ──
    signup_exists = os.path.exists("pages/Sign_up.py")
    if signup_exists:
        st.markdown("""
            <div style="text-align:center; margin-top:20px; font-size:12.5px; color:rgba(100,116,139,0.8);">
                Don't have an account?
                <a href='/Sign_up' style="color:#60a5fa; text-decoration:none; font-weight:500;">Sign up</a>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("""
        <div style="text-align:center; margin-top:28px; font-size:11px;
                    color:rgba(71,85,105,0.6); letter-spacing:0.4px;">
            NeST Digital Academy &nbsp;·&nbsp; Analytics Dashboard
        </div>
    """, unsafe_allow_html=True)

    # ── Handle submission ──
    if submitted:
        if not username or not password:
            st.error("Please enter both your username and password.")
        else:
            success, error_msg = login(username, password)
            if success:
                st.success(f"Welcome back, {st.session_state['display_name']}! Redirecting…")
                st.rerun()
            else:
                st.error(error_msg)