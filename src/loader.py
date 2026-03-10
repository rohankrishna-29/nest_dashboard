import pandas as pd
import os

# Anchor to the project root (the folder containing app.py)
# Works correctly on Windows regardless of which page triggers the import
_THIS_FILE   = os.path.abspath(__file__)          # .../nest_dashboard/src/loader.py
_SRC_DIR     = os.path.dirname(_THIS_FILE)         # .../nest_dashboard/src/
_PROJECT_ROOT = os.path.dirname(_SRC_DIR)          # .../nest_dashboard/
DATA_DIR     = os.path.join(_PROJECT_ROOT, "data")

# File-to-course mapping — update course names once Nest Digital confirms
ACTIVITY_REPORTS = {
    "Activity Report 1.csv": "Angular",
    "Activity Report 2.csv": "Data Analytics",
    "Activity Report 3.csv": "Embedded Systems",
    "Activity Report 4.csv": "Workshop",
}

ROSTER_FILES = {
    "ANG-NOV2025-B5-AMALJYOTHI.csv": "Angular",
}


def load_activity_report(filename: str, course_name: str) -> pd.DataFrame:
    """
    Loads a single activity report CSV.
    These are UTF-16 tab-separated files exported from the LMS.
    Adds a 'course' column based on the filename mapping above.
    """
    filepath = os.path.join(DATA_DIR, filename)
    df = pd.read_csv(filepath, encoding="utf-16", sep="\t")

    # Rename the first unnamed column to 'student_name'
    df.rename(columns={df.columns[0]: "student_name"}, inplace=True)

    # Tag with course
    df["course"] = course_name
    df["source_file"] = filename

    return df


def load_roster(filename: str, course_name: str) -> pd.DataFrame:
    """
    Loads a student roster CSV (latin1 encoded, comma separated).
    """
    filepath = os.path.join(DATA_DIR, filename)
    df = pd.read_csv(filepath, encoding="latin1")
    df["course"] = course_name
    df["source_file"] = filename
    return df


def load_all_activity_reports() -> dict:
    """
    Returns a dict of { course_name: raw_dataframe } for all activity reports.
    """
    if not os.path.isdir(DATA_DIR):
        raise FileNotFoundError(
            f"[loader] data/ folder not found at: {DATA_DIR}. "
            "Make sure your CSV files are in the data/ folder inside your project root."
        )
    reports = {}
    for filename, course_name in ACTIVITY_REPORTS.items():
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            reports[course_name] = load_activity_report(filename, course_name)
        else:
            print(f"[loader] Warning: {filename} not found at {filepath}")
    return reports


def load_all_rosters() -> dict:
    """
    Returns a dict of { course_name: raw_dataframe } for all roster files.
    """
    rosters = {}
    for filename, course_name in ROSTER_FILES.items():
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            rosters[course_name] = load_roster(filename, course_name)
        else:
            print(f"[loader] Warning: {filename} not found in data/")
    return rosters


def load_all() -> tuple[dict, dict]:
    """
    Convenience function — loads everything at once.
    Returns (activity_reports, rosters) as two dicts.
    """
    return load_all_activity_reports(), load_all_rosters()