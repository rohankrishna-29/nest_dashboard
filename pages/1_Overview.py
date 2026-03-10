import streamlit as st
import pandas as pd
from src.auth import require_auth
from src.loader import load_all
from src.normaliser import normalise_all
from components.sidebar import render_sidebar, apply_filters
from components.charts import (
    chart_students_per_course,
    chart_student_type_split,
    chart_student_type_per_course,
)

# ---------------------------------------------------------------------------
# Page config + auth guard
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Overview — NeST Dashboard",
    page_icon="📋",
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

activities_df, roster_df = get_data()

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------

filters = render_sidebar(activities_df)
df = apply_filters(activities_df, filters)

# ---------------------------------------------------------------------------
# Headline metrics
# ---------------------------------------------------------------------------

st.title("📋 Enrollment Overview")
st.caption("A high-level summary of students, courses, and activity across all batches.")
st.markdown("---")

total_students   = df["email"].nunique()
total_courses    = df["course"].nunique()
total_activities = df["activity_name"].nunique()
overall_completion = round(100 * (df["status"] == "Completed").sum() / len(df), 1) if len(df) else 0

internal_count = df.drop_duplicates("email").query("student_type == 'Internal'").shape[0]
external_count = df.drop_duplicates("email").query("student_type == 'External'").shape[0]

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Students",       f"{total_students:,}")
col2.metric("Courses",              f"{total_courses}")
col3.metric("Unique Activities",    f"{total_activities}")
col4.metric("Overall Completion",   f"{overall_completion}%")
col5.metric("Internal / External",  f"{internal_count} / {external_count}")

st.markdown("---")

# ---------------------------------------------------------------------------
# Enrollment charts — row 1
# ---------------------------------------------------------------------------

col_left, col_right = st.columns(2)

with col_left:
    st.plotly_chart(
        chart_students_per_course(df),
        use_container_width=True,
    )

with col_right:
    st.plotly_chart(
        chart_student_type_split(df),
        use_container_width=True,
    )

# ---------------------------------------------------------------------------
# Enrollment charts — row 2
# ---------------------------------------------------------------------------

st.plotly_chart(
    chart_student_type_per_course(df),
    use_container_width=True,
)

# ---------------------------------------------------------------------------
# Raw student table (collapsible)
# ---------------------------------------------------------------------------

with st.expander("🔎 Browse Student List"):
    student_summary = (
        df.groupby(["email", "student_name", "course", "student_type"])
        .agg(
            activities_total   = ("activity_name", "count"),
            activities_done    = ("status", lambda x: (x == "Completed").sum()),
        )
        .reset_index()
    )
    student_summary["completion_%"] = (
        100 * student_summary["activities_done"] / student_summary["activities_total"]
    ).round(1)

    st.dataframe(
        student_summary.sort_values("completion_%", ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "email":             st.column_config.TextColumn("Email"),
            "student_name":      st.column_config.TextColumn("Name"),
            "course":            st.column_config.TextColumn("Course"),
            "student_type":      st.column_config.TextColumn("Type"),
            "activities_total":  st.column_config.NumberColumn("Total Activities"),
            "activities_done":   st.column_config.NumberColumn("Completed"),
            "completion_%":      st.column_config.ProgressColumn(
                                     "Completion %",
                                     min_value=0,
                                     max_value=100,
                                     format="%.1f%%",
                                 ),
        },
    )
