from typing import Optional, Tuple
import pandas as pd
import re

# ---------------------------------------------------------------------------
# Email domain classification
# ---------------------------------------------------------------------------

# Known internal domain for Nest Digital employees
INTERNAL_DOMAIN = "nestgroup.net"

# Known college/institutional domain patterns
COLLEGE_DOMAIN_PATTERNS = [
    r"\.ac\.in$",
    r"\.edu\.in$",
    r"\.ac\.in",
    r"\.[a-z]+\.in$",       # catches cs.ajce.in, cy.ajce.in etc.
    r"saintgits\.org$",
    r"scmsgroup\.org$",
    r"rajagiricollege\.edu\.in$",
    r"mbits\.ac\.in$",
    r"depaul\.edu\.in$",
]


def classify_student_type(email: str) -> str:
    """
    Returns 'Internal', 'External', or 'Unknown' based on email domain.
    - Internal  = nestgroup.net employees
    - External  = institutional college emails
    - Unknown   = gmail/icloud/personal addresses
    """
    if not isinstance(email, str):
        return "Unknown"

    email = email.strip().lower()
    domain = email.split("@")[-1]

    if domain == INTERNAL_DOMAIN:
        return "Internal"

    for pattern in COLLEGE_DOMAIN_PATTERNS:
        if re.search(pattern, domain):
            return "External"

    return "Unknown"


# ---------------------------------------------------------------------------
# Cohort/college parsing from Department column
# ---------------------------------------------------------------------------

def parse_department(dept: str) -> dict[str, Optional[str]]:
    """
    Parses the Department field into structured parts.
    Examples:
      EMB-JUNE2025-B6-RETAIL-G3  -> course=EMB, month=JUNE2025, batch=B6, venue=RETAIL, group=G3
      ANG-NOV2025-B5-AMALJYOTHI  -> course=ANG, month=NOV2025, batch=B5, venue=AMALJYOTHI
      DOCC-FEB26-B1              -> course=DOCC, month=FEB26, batch=B1
      NDA                        -> course=NDA (no further structure)
      FDP-HRTRNDS-MAY2025        -> course=FDP, track=HRTRNDS, month=MAY2025
    """
    result: dict[str, Optional[str]] = {
        "dept_course": None,
        "dept_batch": None,
        "dept_month": None,
        "dept_venue": None,
    }

    if not isinstance(dept, str) or dept.strip() == "":
        return result

    parts = dept.strip().split("-")
    result["dept_course"] = parts[0] if len(parts) > 0 else None

    # Look for batch pattern like B1, B2, B5 etc.
    for part in parts:
        if re.match(r"^B\d+$", part, re.IGNORECASE):
            result["dept_batch"] = part.upper()

    # Look for month pattern like NOV2025, JUNE2025, FEB26, MAY2025
    for part in parts:
        if re.match(r"^[A-Z]+\d{2,4}$", part, re.IGNORECASE):
            result["dept_month"] = part.upper()

    # Venue is whatever is left after course, batch, month — usually college name
    exclude = {result["dept_course"], result["dept_batch"], result["dept_month"]}
    venue_parts = [p for p in parts[1:] if p not in exclude and not re.match(r"^G\d+$", p)]
    if venue_parts:
        result["dept_venue"] = "-".join(venue_parts)

    return result


# ---------------------------------------------------------------------------
# Activity column parsing
# ---------------------------------------------------------------------------

def get_activity_column_pairs(df: pd.DataFrame) -> list:
    """
    The LMS exports each activity as two adjacent columns:
      - col N:   activity name  (e.g. "HTML", "SUBMISSION 1")
      - col N+1: Unnamed: N+1   (the completion timestamp)

    Returns a list of (activity_col, timestamp_col) pairs.
    Skips metadata columns: student_name, ID number, Email address, Department, course, source_file.
    """
    skip = {"student_name", "ID number", "Email address", "Department", "course", "source_file"}
    cols = [c for c in df.columns if c not in skip]

    pairs = []
    i = 0
    while i < len(cols) - 1:
        current = cols[i]
        nxt = cols[i + 1]
        if not current.startswith("Unnamed") and nxt.startswith("Unnamed"):
            pairs.append((current, nxt))
            i += 2
        else:
            i += 1

    return pairs


def parse_status_and_timestamp(value: str) -> Tuple[str, Optional[pd.Timestamp]]:
    """
    Parses a cell value like:
      "Completed  2025-12-14 13:11:28"   -> ("Completed", Timestamp)
      "Not completed"                     -> ("Not completed", None)
      "Completed (achieved pass grade) 2025-06-02 21:04:52" -> ("Completed", Timestamp)
    """
    if not isinstance(value, str):
        return ("Not completed", None)

    value = value.strip()

    if value == "" or value.lower() == "nan":
        return ("Not completed", None)

    if value.lower().startswith("not completed"):
        return ("Not completed", None)

    # Try to extract a datetime from the string
    dt_match = re.search(r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", value)
    timestamp = pd.to_datetime(dt_match.group(1)) if dt_match else None

    return ("Completed", timestamp)


# ---------------------------------------------------------------------------
# Normalise a single activity report into long format
# ---------------------------------------------------------------------------

def normalise_activity_report(df: pd.DataFrame, course_name: str) -> pd.DataFrame:
    """
    Takes a wide raw activity report dataframe and returns a long-format
    normalised dataframe with one row per (student, activity).

    Output schema:
      student_name | email | course | student_type | dept_course | dept_batch |
      dept_month   | dept_venue | activity_name | activity_category |
      status | completed_at | source_file
    """
    rows = []
    activity_pairs = get_activity_column_pairs(df)

    for _, row in df.iterrows():
        email = str(row.get("Email address", "")).strip()
        student_name = str(row.get("student_name", "")).strip()
        dept = row.get("Department", "")
        dept_info = parse_department(dept)
        student_type = classify_student_type(email)

        for activity_col, timestamp_col in activity_pairs:
            # Status comes from the activity column itself
            status_raw = str(row.get(activity_col, "")).strip()
            status, completed_at = parse_status_and_timestamp(status_raw)

            # If status is "Not completed", also check the timestamp column
            # (some rows store the timestamp there instead)
            if status == "Not completed":
                ts_raw = str(row.get(timestamp_col, "")).strip()
                status2, completed_at2 = parse_status_and_timestamp(ts_raw)
                if status2 == "Completed":
                    status = "Completed"
                    completed_at = completed_at2

            rows.append({
                "student_name": student_name,
                "email": email,
                "course": course_name,
                "student_type": student_type,
                "dept_course": dept_info["dept_course"],
                "dept_batch": dept_info["dept_batch"],
                "dept_month": dept_info["dept_month"],
                "dept_venue": dept_info["dept_venue"],
                "activity_name": activity_col.strip(),
                "activity_category": categorise_activity(activity_col),
                "status": status,
                "completed_at": completed_at,
                "source_file": row.get("source_file", ""),
            })

    return pd.DataFrame(rows)


def categorise_activity(activity_name: str) -> str:
    """
    Groups activity column names into broader categories for filtering/charting.
    """
    name = activity_name.lower()

    if any(k in name for k in ["entrance", "exit test", "quiz", "assessment", "post"]):
        return "Assessment"
    if any(k in name for k in ["submission", "task", "assignment"]):
        return "Submission"
    if any(k in name for k in ["mini project", "final project", "dashboard", "project"]):
        return "Project"
    if any(k in name for k in ["feedback"]):
        return "Feedback"
    if any(k in name for k in ["certificate", "internship cert"]):
        return "Certificate"
    if any(k in name for k in ["reference link"]):
        return "Reference Material"
    if any(k in name for k in ["html", "css", "javascript", "c programming", "pre-learning"]):
        return "Module"
    if any(k in name for k in ["qr code", "live feedback", "click here to type"]):
        return "Misc"

    return "Other"


# ---------------------------------------------------------------------------
# Normalise the roster file
# ---------------------------------------------------------------------------

def normalise_roster(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the student roster file into a simple, flat schema.

    Output schema:
      student_name | email | course | cohort | college | student_type
    """
    roster = pd.DataFrame()
    roster["student_name"] = (df["firstname"].fillna("") + " " + df["lastname"].fillna("")).str.strip()
    roster["email"] = df["email"].str.strip().str.lower()
    roster["course"] = df.get("course1", df.get("course", "Unknown"))
    roster["cohort"] = df.get("cohort1", None)
    roster["college"] = df["email"].apply(lambda e: e.split("@")[-1] if isinstance(e, str) else None)
    roster["student_type"] = df["email"].apply(classify_student_type)
    return roster


# ---------------------------------------------------------------------------
# Master normalise function — call this from app/pages
# ---------------------------------------------------------------------------

def normalise_all(activity_reports: dict, rosters: dict) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Takes raw dicts from loader.load_all() and returns:
      - activities_df: full long-format activity table
      - roster_df:     cleaned roster table
    """
    activity_frames = []
    for course_name, df in activity_reports.items():
        normalised = normalise_activity_report(df, course_name)
        activity_frames.append(normalised)

    activities_df = pd.concat(activity_frames, ignore_index=True) if activity_frames else pd.DataFrame()

    roster_frames = []
    for course_name, df in rosters.items():
        normalised = normalise_roster(df)
        roster_frames.append(normalised)

    roster_df = pd.concat(roster_frames, ignore_index=True) if roster_frames else pd.DataFrame()

    return activities_df, roster_df