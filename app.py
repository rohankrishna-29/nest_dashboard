import streamlit as st
from src.auth import init_auth, is_authenticated
from components.login import render_login_page

st.set_page_config(
    page_title="NeST Digital Academy — Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_auth()

if not is_authenticated():
    render_login_page()
    st.stop()

# Authenticated — redirect straight to Overview
st.switch_page("pages/1_Overview.py")