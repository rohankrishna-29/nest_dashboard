import streamlit as st
from src.auth import init_auth, is_authenticated, logout
from src.loader import load_all
from src.normaliser import normalise_all
from components.login import render_login_page

st.set_page_config(
    page_title="NeST Digital Academy — Dashboard",
    page_icon="https://learning.nestdigital.com/pluginfile.php/1/theme_edash/main_logo/1771222660/LogoNeST.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_auth()

# ---------------------------------------------------------------------------
# Auth gate — show login page if not authenticated
# ---------------------------------------------------------------------------

if not is_authenticated():
    render_login_page()
    st.stop()

# ---------------------------------------------------------------------------
# Authenticated — show main landing + sidebar nav
# ---------------------------------------------------------------------------

with st.sidebar:
    st.image(
        "https://learning.nestdigital.com/pluginfile.php/1/theme_edash/main_logo/1771222660/LogoNeST.png",
        width=180,
    )
    st.markdown("---")
    st.markdown(f"👤 **{st.session_state['display_name']}**")
    st.markdown(f"🔑 Role: `{st.session_state['role']}`")
    st.markdown("---")

    if st.button("Logout", use_container_width=True):
        logout()
        st.rerun()

# Main landing page content
st.title("📊 NeST Digital Academy — Analytics Dashboard")
st.markdown("Use the sidebar to navigate between reports.")

@st.cache_data
def get_data():
    reports, rosters = load_all()
    return normalise_all(reports, rosters)

activities_df, _ = get_data()

total_students     = activities_df["email"].nunique()
total_courses      = activities_df["course"].nunique()
avg_completion     = round(100 * (activities_df["status"] == "Completed").sum() / len(activities_df), 1)
internal_count     = activities_df.drop_duplicates("email").query("student_type == 'Internal'").shape[0]
external_count     = activities_df.drop_duplicates("email").query("student_type == 'External'").shape[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Courses",        f"{total_courses}")
col2.metric("Total Students",       f"{total_students:,}")
col3.metric("Avg Completion Rate",  f"{avg_completion}%")
col4.metric("Internal / External",  f"{internal_count} / {external_count}")

st.info("👈 Select a page from the sidebar to get started.")
