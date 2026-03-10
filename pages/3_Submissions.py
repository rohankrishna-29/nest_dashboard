import streamlit as st
import pandas as pd
import plotly.express as px
from src.auth import require_auth
from src.loader import load_all
from src.normaliser import normalise_all
from components.sidebar import render_sidebar, apply_filters

NEST_BLUE  = "#1f3c88"
NEST_RED   = "#e63946"
PALETTE    = [NEST_BLUE, NEST_RED, "#3b82f6", "#f4a261", "#2a9d8f"]

# ---------------------------------------------------------------------------
# Page config + auth guard
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Submissions — NeST Dashboard",
    page_icon="📝",
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

st.title("📝 Submission & Activity Tracking")
st.caption("Drill into specific activities and individual student progress.")
st.markdown("---")

# ---------------------------------------------------------------------------
# Activity completion summary table
# ---------------------------------------------------------------------------

st.subheader("📊 Activity Completion Summary")
st.caption("How many students completed each activity, grouped by course and category.")

activity_summary = (
    df.groupby(["course", "activity_category", "activity_name"])
    .agg(
        total_students  = ("email", "nunique"),
        completed       = ("status", lambda x: (x == "Completed").sum()),
    )
    .reset_index()
)
activity_summary["completion_%"] = (
    100 * activity_summary["completed"] / activity_summary["total_students"]
).round(1)

course_options = ["All"] + sorted(df["course"].dropna().unique().tolist())
selected_course_filter = st.selectbox("Filter by course", options=course_options, key="activity_course")

if selected_course_filter != "All":
    display_summary = activity_summary[activity_summary["course"] == selected_course_filter]
else:
    display_summary = activity_summary

st.dataframe(
    display_summary.sort_values(["course", "completion_%"], ascending=[True, False]),
    use_container_width=True,
    hide_index=True,
    column_config={
        "course":           st.column_config.TextColumn("Course"),
        "activity_category":st.column_config.TextColumn("Category"),
        "activity_name":    st.column_config.TextColumn("Activity"),
        "total_students":   st.column_config.NumberColumn("Students"),
        "completed":        st.column_config.NumberColumn("Completed"),
        "completion_%":     st.column_config.ProgressColumn(
                                "Completion %",
                                min_value=0,
                                max_value=100,
                                format="%.1f%%",
                            ),
    },
)

st.markdown("---")

# ---------------------------------------------------------------------------
# Submission rate by category — bar chart
# ---------------------------------------------------------------------------

st.subheader("📂 Submission Rate by Category")

cat_summary = (
    df.groupby(["course", "activity_category"])
    .agg(
        total     = ("email", "count"),
        completed = ("status", lambda x: (x == "Completed").sum()),
    )
    .reset_index()
)
cat_summary["rate"] = (100 * cat_summary["completed"] / cat_summary["total"]).round(1)

fig_cat = px.bar(
    cat_summary,
    x="activity_category", y="rate",
    color="course", barmode="group",
    color_discrete_sequence=PALETTE,
    labels={"activity_category": "Category", "rate": "Completion Rate (%)", "course": "Course"},
    title="Submission Rate by Activity Category & Course",
    text=cat_summary["rate"].apply(lambda x: f"{x}%"),
)
fig_cat.update_traces(textposition="outside")
fig_cat.update_layout(plot_bgcolor="white", xaxis_tickangle=-15)
st.plotly_chart(fig_cat, use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Individual student lookup
# ---------------------------------------------------------------------------

st.subheader("🔍 Individual Student Lookup")
st.caption("Search for a student by name or email to see their full activity history.")

search_query = st.text_input("Search by name or email", placeholder="e.g. john or john@gmail.com")

if search_query.strip():
    mask = (
        df["student_name"].str.contains(search_query, case=False, na=False) |
        df["email"].str.contains(search_query, case=False, na=False)
    )
    matched_students = df[mask]["email"].unique()

    if len(matched_students) == 0:
        st.warning("No students found matching that search.")

    elif len(matched_students) > 1:
        selected_email = st.selectbox(
            f"{len(matched_students)} students found — select one:",
            options=matched_students,
        )
    else:
        selected_email = matched_students[0]

    if len(matched_students) >= 1:
        student_df = df[df["email"] == selected_email].copy()
        student_name = student_df["student_name"].iloc[0]
        student_type = student_df["student_type"].iloc[0]
        course_name  = student_df["course"].iloc[0]

        st.markdown(f"### {student_name}")
        info_col1, info_col2, info_col3 = st.columns(3)
        info_col1.markdown(f"**Email:** {selected_email}")
        info_col2.markdown(f"**Type:** {student_type}")
        info_col3.markdown(f"**Course:** {course_name}")

        done  = (student_df["status"] == "Completed").sum()
        total = len(student_df)
        rate  = round(100 * done / total, 1) if total else 0
        st.progress(int(rate), text=f"Overall completion: {rate}% ({done}/{total} activities)")

        # Activity breakdown table
        st.dataframe(
            student_df[["activity_category", "activity_name", "status", "completed_at"]]
                .sort_values(["activity_category", "activity_name"]),
            use_container_width=True,
            hide_index=True,
            column_config={
                "activity_category": st.column_config.TextColumn("Category"),
                "activity_name":     st.column_config.TextColumn("Activity"),
                "status":            st.column_config.TextColumn("Status"),
                "completed_at":      st.column_config.DatetimeColumn(
                                         "Completed At",
                                         format="DD MMM YYYY, hh:mm a",
                                     ),
            },
        )
