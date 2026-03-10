import streamlit as st
import pandas as pd
import plotly.express as px
from src.auth import require_auth
from src.loader import load_all
from src.normaliser import normalise_all
from components.sidebar import render_sidebar, apply_filters

NEST_BLUE  = "#1f3c88"
NEST_RED   = "#e63946"
PALETTE    = [NEST_BLUE, NEST_RED, "#3b82f6", "#f4a261", "#2a9d8f", "#e9c46a"]

# ---------------------------------------------------------------------------
# Page config + auth guard
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Cohorts — NeST Dashboard",
    page_icon="🏫",
    layout="wide",
)
require_auth()

# ---------------------------------------------------------------------------
# Load + cache data
# ---------------------------------------------------------------------------

@st.cache_data
def get_data():
    reports, rosters = load_all()
    return normalise_all(reports, rosters)

activities_df, _ = get_data()

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------

filters = render_sidebar(activities_df)
df = apply_filters(activities_df, filters)

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

st.title("🏫 Cohort & Batch Comparisons")
st.caption("Compare performance across colleges, batches, and student types.")
st.markdown("---")

# ---------------------------------------------------------------------------
# Helper: derive college from email domain
# ---------------------------------------------------------------------------

def email_to_college(email: str) -> str:
    if not isinstance(email, str):
        return "Unknown"
    domain = email.strip().lower().split("@")[-1]
    # Map known domains to readable names
    domain_map = {
        "cs.ajce.in":               "Amal Jyothi (CS)",
        "cy.ajce.in":               "Amal Jyothi (CY)",
        "amaljyothi.ac.in":         "Amal Jyothi",
        "saintgits.org":            "Saintgits",
        "icet.ac.in":               "ICET",
        "santhigiricollege.ac.in":  "Santhigiri College",
        "santhigiricollege.com":    "Santhigiri College",
        "cce.edu.in":               "CCE",
        "scmsgroup.org":            "SCMS",
        "mbits.ac.in":              "MBITS",
        "ug.cusat.ac.in":           "CUSAT",
        "rajagiri.edu.in":          "Rajagiri",
        "rajagiricollege.edu.in":   "Rajagiri",
        "nestgroup.net":            "NeST (Internal)",
        "gmail.com":                "Personal Email",
    }
    return domain_map.get(domain, domain)

df = df.copy()
df["college"] = df["email"].apply(email_to_college)

# ---------------------------------------------------------------------------
# Students and completion rate per college
# ---------------------------------------------------------------------------

st.subheader("🏛️ College-wise Breakdown")

college_stats = (
    df.groupby("college")
    .agg(
        students        = ("email", "nunique"),
        total_activities= ("activity_name", "count"),
        completed       = ("status", lambda x: (x == "Completed").sum()),
    )
    .reset_index()
)
college_stats["completion_%"] = (
    100 * college_stats["completed"] / college_stats["total_activities"]
).round(1)
college_stats = college_stats.sort_values("students", ascending=False)

col_left, col_right = st.columns(2)

with col_left:
    fig_students = px.bar(
        college_stats.head(15),
        x="students", y="college",
        orientation="h",
        color="students",
        color_continuous_scale=[NEST_BLUE, "#3b82f6"],
        title="Students per College (Top 15)",
        labels={"students": "Students", "college": ""},
        text="students",
    )
    fig_students.update_traces(textposition="outside")
    fig_students.update_layout(coloraxis_showscale=False, plot_bgcolor="white")
    st.plotly_chart(fig_students, use_container_width=True)

with col_right:
    fig_rate = px.bar(
        college_stats.head(15).sort_values("completion_%", ascending=True),
        x="completion_%", y="college",
        orientation="h",
        color="completion_%",
        color_continuous_scale=["white", NEST_BLUE],
        title="Completion Rate per College (Top 15)",
        labels={"completion_%": "Completion Rate (%)", "college": ""},
        text=college_stats.sort_values("completion_%").head(15)["completion_%"].apply(lambda x: f"{x}%"),
    )
    fig_rate.update_traces(textposition="outside")
    fig_rate.update_layout(coloraxis_showscale=False, plot_bgcolor="white")
    st.plotly_chart(fig_rate, use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Internal vs External comparison
# ---------------------------------------------------------------------------

st.subheader("👥 Internal vs External Students")

type_course = (
    df.drop_duplicates(["email", "course"])
    .groupby(["course", "student_type"])
    .size()
    .reset_index(name="students")
)
fig_type = px.bar(
    type_course,
    x="course", y="students",
    color="student_type",
    barmode="group",
    color_discrete_sequence=PALETTE,
    title="Internal vs External Students per Course",
    labels={"course": "Course", "students": "Students", "student_type": "Type"},
    text="students",
)
fig_type.update_traces(textposition="outside")
fig_type.update_layout(plot_bgcolor="white")
st.plotly_chart(fig_type, use_container_width=True)

# Completion rate by type
type_completion = (
    df.groupby(["course", "student_type"])
    .apply(lambda x: round(100 * (x["status"] == "Completed").sum() / len(x), 1))
    .reset_index(name="completion_%")
)
fig_type_rate = px.bar(
    type_completion,
    x="course", y="completion_%",
    color="student_type",
    barmode="group",
    color_discrete_sequence=PALETTE,
    title="Completion Rate: Internal vs External per Course",
    labels={"course": "Course", "completion_%": "Completion Rate (%)", "student_type": "Type"},
    text=type_completion["completion_%"].apply(lambda x: f"{x}%"),
)
fig_type_rate.update_traces(textposition="outside")
fig_type_rate.update_layout(plot_bgcolor="white")
st.plotly_chart(fig_type_rate, use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Dept/cohort breakdown (for rows that have dept_* populated)
# ---------------------------------------------------------------------------

st.subheader("📦 Cohort Breakdown (from Department field)")
st.caption("Only students with a populated Department field are shown here — this is a subset of all students.")

cohort_df = df[df["dept_course"].notna()].copy()

if cohort_df.empty:
    st.info("No cohort/department data available with current filters.")
else:
    cohort_stats = (
        cohort_df.groupby(["dept_course", "dept_batch", "dept_venue"])
        .agg(
            students  = ("email", "nunique"),
            completed = ("status", lambda x: (x == "Completed").sum()),
            total     = ("activity_name", "count"),
        )
        .reset_index()
    )
    cohort_stats["completion_%"] = (
        100 * cohort_stats["completed"] / cohort_stats["total"]
    ).round(1)

    st.dataframe(
        cohort_stats.sort_values("completion_%", ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "dept_course":   st.column_config.TextColumn("Course Code"),
            "dept_batch":    st.column_config.TextColumn("Batch"),
            "dept_venue":    st.column_config.TextColumn("Venue / College"),
            "students":      st.column_config.NumberColumn("Students"),
            "completed":     st.column_config.NumberColumn("Completed Activities"),
            "total":         st.column_config.NumberColumn("Total Activities"),
            "completion_%":  st.column_config.ProgressColumn(
                                 "Completion %",
                                 min_value=0,
                                 max_value=100,
                                 format="%.1f%%",
                             ),
        },
    )
