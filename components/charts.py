import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# Brand colours
# ---------------------------------------------------------------------------
NEST_BLUE   = "#1f3c88"
NEST_RED    = "#e63946"
NEST_LIGHT  = "#3b82f6"
PALETTE     = [NEST_BLUE, NEST_RED, NEST_LIGHT, "#f4a261", "#2a9d8f", "#e9c46a"]


# ---------------------------------------------------------------------------
# Enrollment & Overview charts
# ---------------------------------------------------------------------------

def chart_students_per_course(activities_df: pd.DataFrame) -> go.Figure:
    """Bar chart — unique students per course."""
    data = (
        activities_df.groupby("course")["email"]
        .nunique()
        .reset_index()
        .rename(columns={"email": "students"})
        .sort_values("students", ascending=False)
    )
    fig = px.bar(
        data, x="course", y="students",
        color="course", color_discrete_sequence=PALETTE,
        title="Students per Course",
        labels={"course": "Course", "students": "Unique Students"},
        text="students",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(showlegend=False, plot_bgcolor="white")
    return fig


def chart_student_type_split(activities_df: pd.DataFrame) -> go.Figure:
    """Donut chart — Internal vs External vs Unknown."""
    counts = activities_df.drop_duplicates("email")["student_type"].value_counts()
    data = pd.DataFrame({"student_type": counts.index, "students": counts.values})
    fig = px.pie(
        data, names="student_type", values="students",
        hole=0.45,
        color_discrete_sequence=PALETTE,
        title="Student Type Breakdown",
    )
    fig.update_traces(textinfo="label+percent")
    return fig


def chart_student_type_per_course(activities_df: pd.DataFrame) -> go.Figure:
    """Stacked bar — student type breakdown per course."""
    data = (
        activities_df.drop_duplicates(["email", "course"])
        .groupby(["course", "student_type"])
        .size()
        .reset_index(name="count")
    )
    fig = px.bar(
        data, x="course", y="count", color="student_type",
        color_discrete_sequence=PALETTE,
        title="Student Type per Course",
        labels={"course": "Course", "count": "Students", "student_type": "Type"},
        barmode="stack",
        text="count",
    )
    fig.update_traces(textposition="inside")
    fig.update_layout(plot_bgcolor="white")
    return fig


# ---------------------------------------------------------------------------
# Completion & Drop-off charts
# ---------------------------------------------------------------------------

def chart_completion_rate_per_course(activities_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar — overall completion rate % per course."""
    data = (
        activities_df.groupby("course")
        .apply(lambda x: round(100 * (x["status"] == "Completed").sum() / len(x), 1))
        .reset_index(name="completion_rate")
        .sort_values("completion_rate", ascending=True)
    )
    fig = px.bar(
        data, x="completion_rate", y="course",
        orientation="h",
        color="completion_rate",
        color_continuous_scale=[NEST_BLUE, NEST_LIGHT],
        title="Overall Completion Rate by Course (%)",
        labels={"completion_rate": "Completion Rate (%)", "course": ""},
        text=data["completion_rate"].apply(lambda x: f"{x}%"),
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(coloraxis_showscale=False, plot_bgcolor="white")
    return fig


def chart_completion_funnel(activities_df: pd.DataFrame, course: str) -> go.Figure:
    """
    Funnel chart — shows how many students completed each activity
    in order, revealing where drop-off occurs for a given course.
    Only includes activity categories relevant to learning progression
    (excludes Certificates, Feedback, Misc).
    """
    exclude_cats = {"Certificate", "Feedback", "Misc", "Other"}
    df = activities_df[
        (activities_df["course"] == course) &
        (~activities_df["activity_category"].isin(exclude_cats))
    ]

    # Count completions per activity, sorted by most completions first
    data = (
        df[df["status"] == "Completed"]
        .groupby("activity_name")["email"]
        .nunique()
        .reset_index(name="completed_students")
        .sort_values("completed_students", ascending=False)
        .head(15)  # cap at 15 activities for readability
    )

    fig = go.Figure(go.Funnel(
        y=data["activity_name"],
        x=data["completed_students"],
        marker=dict(color=NEST_BLUE),
        textinfo="value+percent initial",
    ))
    fig.update_layout(title=f"Completion Funnel — {course}")
    return fig


def chart_completion_by_category(activities_df: pd.DataFrame) -> go.Figure:
    """Grouped bar — completion rate per activity category per course."""
    data = (
        activities_df.groupby(["course", "activity_category"])
        .apply(lambda x: round(100 * (x["status"] == "Completed").sum() / len(x), 1))
        .reset_index(name="completion_rate")
    )
    fig = px.bar(
        data, x="activity_category", y="completion_rate",
        color="course", barmode="group",
        color_discrete_sequence=PALETTE,
        title="Completion Rate by Activity Category",
        labels={
            "activity_category": "Activity Category",
            "completion_rate": "Completion Rate (%)",
            "course": "Course",
        },
    )
    fig.update_layout(plot_bgcolor="white", xaxis_tickangle=-20)
    return fig


def chart_inactive_students(activities_df: pd.DataFrame) -> go.Figure:
    """Bar chart — students with zero completions per course."""
    total = (
        activities_df.groupby(["course", "email"])["status"]
        .apply(lambda x: (x == "Completed").sum())
        .reset_index(name="completed_count")
    )
    inactive = (
        total[total["completed_count"] == 0]
        .groupby("course")
        .size()
        .reset_index(name="inactive_students")
    )
    fig = px.bar(
        inactive, x="course", y="inactive_students",
        color="course", color_discrete_sequence=PALETTE,
        title="Inactive Students (Zero Completions) per Course",
        labels={"course": "Course", "inactive_students": "Students"},
        text="inactive_students",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(showlegend=False, plot_bgcolor="white")
    return fig


# ---------------------------------------------------------------------------
# Time-based / trend charts
# ---------------------------------------------------------------------------

def chart_submissions_over_time(activities_df: pd.DataFrame) -> go.Figure:
    """Line chart — number of completions per week across all courses."""
    df = activities_df[activities_df["completed_at"].notna()].copy()
    df["week"] = df["completed_at"].dt.to_period("W").apply(lambda p: p.start_time)

    data = (
        df.groupby(["week", "course"])
        .size()
        .reset_index(name="completions")
    )
    fig = px.line(
        data, x="week", y="completions", color="course",
        color_discrete_sequence=PALETTE,
        title="Completions Over Time (Weekly)",
        labels={"week": "Week", "completions": "Completions", "course": "Course"},
        markers=True,
    )
    fig.update_layout(plot_bgcolor="white")
    return fig


def chart_completion_heatmap(activities_df: pd.DataFrame, course: str) -> go.Figure:
    """
    Heatmap — activity vs month, showing completion volume.
    Useful for spotting deadline-driven spikes.
    """
    df = activities_df[
        (activities_df["course"] == course) &
        (activities_df["completed_at"].notna())
    ].copy()

    if df.empty:
        fig = go.Figure()
        fig.update_layout(title=f"No completion data available for {course}")
        return fig

    df["month"] = df["completed_at"].dt.to_period("M").astype(str)

    pivot = (
        df.groupby(["activity_name", "month"])
        .size()
        .unstack(fill_value=0)
    )

    fig = px.imshow(
        pivot,
        color_continuous_scale=["white", NEST_BLUE],
        title=f"Completion Heatmap — {course}",
        labels={"x": "Month", "y": "Activity", "color": "Completions"},
        aspect="auto",
    )
    fig.update_layout(xaxis_tickangle=-30)
    return fig