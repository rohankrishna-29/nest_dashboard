import streamlit as st
import pandas as pd
from src.auth import logout


def render_sidebar(activities_df: pd.DataFrame) -> dict:
    """
    Renders the shared sidebar with logo, user info, navigation filters,
    and logout. Returns a dict of selected filter values to be used by
    whichever page imports this.

    Returns:
        {
            "courses":       list[str]  - selected course names
            "student_types": list[str]  - Internal / External / Unknown
            "categories":    list[str]  - activity categories
            "date_range":    (date, date) | None
        }
    """

    with st.sidebar:

        # ----------------------------------------------------------------
        # Branding
        # ----------------------------------------------------------------
        st.image(
            "https://learning.nestdigital.com/pluginfile.php/1/theme_edash/main_logo/1771222660/LogoNeST.png",
            width=180,
        )
        st.markdown("---")

        # ----------------------------------------------------------------
        # User info + logout
        # ----------------------------------------------------------------
        display_name = st.session_state.get("display_name", "User")
        role = st.session_state.get("role", "")
        st.markdown(f"👤 **{display_name}**")
        st.markdown(f"🔑 Role: `{role}`")

        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()

        st.markdown("---")

        # ----------------------------------------------------------------
        # Filters
        # ----------------------------------------------------------------
        st.markdown("### 🔍 Filters")

        # Course filter
        all_courses = sorted(activities_df["course"].dropna().unique().tolist())
        selected_courses = st.multiselect(
            "Course",
            options=all_courses,
            default=all_courses,
            help="Filter by course"
        )

        # Student type filter
        all_types = sorted(activities_df["student_type"].dropna().unique().tolist())
        selected_types = st.multiselect(
            "Student Type",
            options=all_types,
            default=all_types,
            help="Internal = nestgroup.net employees | External = college students | Unknown = personal email"
        )

        # Activity category filter
        all_categories = sorted(activities_df["activity_category"].dropna().unique().tolist())
        selected_categories = st.multiselect(
            "Activity Category",
            options=all_categories,
            default=all_categories,
            help="Filter by the type of activity"
        )

        # Date range filter — only shown if completed_at data exists
        has_dates = activities_df["completed_at"].notna().any()
        date_range = None

        if has_dates:
            st.markdown("**Completion Date Range**")
            min_date = activities_df["completed_at"].dropna().min().date()
            max_date = activities_df["completed_at"].dropna().max().date()

            date_from = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date)
            date_to = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date)

            if date_from <= date_to:
                date_range = (date_from, date_to)
            else:
                st.warning("'From' date must be before 'To' date.")

        st.markdown("---")
        st.caption("NeST Digital Academy · L&D Analytics")

    return {
        "courses": selected_courses,
        "student_types": selected_types,
        "categories": selected_categories,
        "date_range": date_range,
    }


def apply_filters(activities_df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """
    Applies the filter dict returned by render_sidebar() to the activities
    dataframe. Call this at the top of each page after render_sidebar().

    Usage:
        filters = render_sidebar(activities_df)
        df = apply_filters(activities_df, filters)
        # use df for all charts on this page
    """
    df = activities_df.copy()

    if filters.get("courses"):
        df = df[df["course"].isin(filters["courses"])]

    if filters.get("student_types"):
        df = df[df["student_type"].isin(filters["student_types"])]

    if filters.get("categories"):
        df = df[df["activity_category"].isin(filters["categories"])]

    if filters.get("date_range"):
        date_from, date_to = filters["date_range"]
        # Keep rows that are either not completed (no date) or within range
        completed_mask = (
            activities_df["completed_at"].notna() &
            (activities_df["completed_at"].dt.date >= date_from) &
            (activities_df["completed_at"].dt.date <= date_to)
        )
        not_completed_mask = activities_df["completed_at"].isna()
        df = df[completed_mask | not_completed_mask]

    return df
