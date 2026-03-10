import streamlit as st
from src.auth import require_auth
from src.loader import load_all
from src.normaliser import normalise_all
from components.sidebar import render_sidebar, apply_filters
from components.charts import (
    chart_completion_rate_per_course,
    chart_completion_funnel,
    chart_completion_by_category,
    chart_inactive_students,
    chart_submissions_over_time,
    chart_completion_heatmap,
)

# ---------------------------------------------------------------------------
# Page config + auth guard
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Completion — NeST Dashboard",
    page_icon="✅",
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
# Headline metrics
# ---------------------------------------------------------------------------

st.title("✅ Completion & Drop-off Analysis")
st.caption("Understand how far students are getting through each course.")
st.markdown("---")

total_students  = df["email"].nunique()
completed_any   = df[df["status"] == "Completed"]["email"].nunique()
completed_none  = total_students - completed_any
avg_completion  = round(100 * (df["status"] == "Completed").sum() / len(df), 1) if len(df) else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Students",          f"{total_students:,}")
col2.metric("Started (≥1 completion)", f"{completed_any:,}")
col3.metric("Fully Inactive",          f"{completed_none:,}")
col4.metric("Avg Completion Rate",     f"{avg_completion}%")

st.markdown("---")

# ---------------------------------------------------------------------------
# Completion rate per course + by category
# ---------------------------------------------------------------------------

col_left, col_right = st.columns(2)

with col_left:
    st.plotly_chart(
        chart_completion_rate_per_course(df),
        use_container_width=True,
    )

with col_right:
    st.plotly_chart(
        chart_inactive_students(df),
        use_container_width=True,
    )

st.plotly_chart(
    chart_completion_by_category(df),
    use_container_width=True,
)

st.markdown("---")

# ---------------------------------------------------------------------------
# Per-course funnel — user picks the course
# ---------------------------------------------------------------------------

st.subheader("🔽 Completion Funnel")
st.caption("Select a course to see where students are dropping off activity by activity.")

available_courses = sorted(df["course"].dropna().unique().tolist())

if available_courses:
    selected_course = st.selectbox("Select course", options=available_courses)

    col_funnel, col_heatmap = st.columns(2)

    with col_funnel:
        st.plotly_chart(
            chart_completion_funnel(df, selected_course),
            use_container_width=True,
        )

    with col_heatmap:
        st.plotly_chart(
            chart_completion_heatmap(df, selected_course),
            use_container_width=True,
        )
else:
    st.info("No courses available with current filters.")

st.markdown("---")

# ---------------------------------------------------------------------------
# Completions over time
# ---------------------------------------------------------------------------

st.subheader("📈 Completions Over Time")
st.caption("Weekly completion activity across all courses — useful for spotting batch deadlines and engagement spikes.")

st.plotly_chart(
    chart_submissions_over_time(df),
    use_container_width=True,
)

# ---------------------------------------------------------------------------
# At-risk students table
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("⚠️ At-Risk Students")
st.caption("Students who started a course (completed at least one early activity) but have stalled before finishing.")

exclude_cats = {"Certificate", "Feedback", "Misc", "Other"}
core_df = df[~df["activity_category"].isin(exclude_cats)]

student_progress = (
    core_df.groupby(["email", "student_name", "course", "student_type"])
    .agg(
        total   = ("activity_name", "count"),
        done    = ("status", lambda x: (x == "Completed").sum()),
    )
    .reset_index()
)
student_progress["completion_%"] = (
    100 * student_progress["done"] / student_progress["total"]
).round(1)

# At-risk = completed at least 1 but less than 80%
at_risk = student_progress[
    (student_progress["done"] > 0) &
    (student_progress["completion_%"] < 80)
].sort_values("completion_%")

if not at_risk.empty:
    st.dataframe(
        at_risk,
        use_container_width=True,
        hide_index=True,
        column_config={
            "email":         st.column_config.TextColumn("Email"),
            "student_name":  st.column_config.TextColumn("Name"),
            "course":        st.column_config.TextColumn("Course"),
            "student_type":  st.column_config.TextColumn("Type"),
            "total":         st.column_config.NumberColumn("Core Activities"),
            "done":          st.column_config.NumberColumn("Completed"),
            "completion_%":  st.column_config.ProgressColumn(
                                 "Completion %",
                                 min_value=0,
                                 max_value=100,
                                 format="%.1f%%",
                             ),
        },
    )
    st.caption(f"{len(at_risk)} at-risk students identified.")
else:
    st.success("No at-risk students with current filters.")
