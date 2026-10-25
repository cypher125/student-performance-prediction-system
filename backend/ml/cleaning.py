"""Validate and clean academic records in the YABATECH format (3.5, 3.16).

Used for the simulated dataset now and for CSV uploads in the web app later.
Every step is counted so Chapter 4 can report what cleaning changed.
"""
import re

import numpy as np
import pandas as pd

from . import config
from .grading import gpa_to_class

ID_COLUMNS = ["student_code", "level", "session", "semester"]
NUMERIC_RANGES = {
    "attendance_pct": (0, 100),
    "ca_score": (0, 100),
    "assignment_score": (0, 100),
    "exam_score": (0, 100),
    "gpa": (0, 4),
    "prior_gpa": (0, 4),
}
# A record missing two or more of these is excluded (3.5). prior_gpa is not in the
# list because first-semester ND1 students have no previous GPA by design.
KEY_PREDICTORS = ["attendance_pct", "ca_score", "assignment_score"]
OUTPUT_COLUMNS = ID_COLUMNS + list(NUMERIC_RANGES) + [config.TARGET]


def normalize_level(value):
    if pd.isna(value):
        return None
    text = re.sub(r"[^A-Z0-9]", "", str(value).upper())
    return text if text in config.LEVELS else None


def normalize_semester(value):
    if pd.isna(value):
        return None
    text = re.sub(r"\s+", " ", str(value).strip().lower()).removesuffix(" semester")
    if text in {"first", "1st", "1"}:
        return "First"
    if text in {"second", "2nd", "2"}:
        return "Second"
    return None


def normalize_session(value):
    """'2021/22', '2021-2022' or '2021 / 2022' -> '2021/2022'; None if not a valid session."""
    if pd.isna(value):
        return None
    match = re.fullmatch(r"\s*(\d{4})\s*[/-]\s*(\d{2}|\d{4})\s*", str(value))
    if not match:
        return None
    start, end = int(match.group(1)), match.group(2)
    end_year = int(end) if len(end) == 4 else (start // 100) * 100 + int(end)
    return f"{start}/{start + 1}" if end_year == start + 1 else None


def clean_records(raw):
    """Return the cleaned records and a step-by-step log of what changed."""
    df = raw.copy()
    log = []

    def note(step, affected):
        log.append({"step": step, "records_affected": int(affected), "records_remaining": len(df)})

    note("Records received", len(df))

    before = df[["level", "semester", "session"]].astype("string")
    df["level"] = df["level"].map(normalize_level)
    df["semester"] = df["semester"].map(normalize_semester)
    df["session"] = df["session"].map(normalize_session)
    df["student_code"] = df["student_code"].astype("string").str.strip().str.upper()
    after = df[["level", "semester", "session"]].astype("string")
    changed = (before.fillna("") != after.fillna("")).any(axis=1) & after.notna().all(axis=1)
    note("Level, semester and session labels standardised", changed.sum())

    out_of_range = pd.Series(False, index=df.index)
    for column, (low, high) in NUMERIC_RANGES.items():
        values = pd.to_numeric(df[column], errors="coerce")
        bad = values.notna() & ~values.between(low, high)
        bad |= df[column].notna() & values.isna()  # text where a number belongs
        out_of_range |= bad
        df[column] = values.mask(bad)
    note("Records with impossible values blanked (out of range or not a number)", out_of_range.sum())

    invalid = df[ID_COLUMNS].isna().any(axis=1) | (df["student_code"] == "")
    df = df[~invalid]
    note("Records removed: missing or unrecognised student code, level, semester or session", invalid.sum())

    duplicated = df.duplicated(subset=ID_COLUMNS, keep="first")
    df = df[~duplicated]
    note("Duplicate records removed (same student, level, session and semester)", duplicated.sum())

    no_outcome = df["gpa"].isna()
    df = df[~no_outcome]
    note("Records removed: no semester GPA, so the outcome is unknown", no_outcome.sum())

    sparse = df[KEY_PREDICTORS].isna().sum(axis=1) >= 2
    df = df[~sparse]
    note("Records removed: two or more of attendance, CA and assignment missing", sparse.sum())

    df = df.copy()
    df[config.TARGET] = df["gpa"].map(gpa_to_class)
    df = df[OUTPUT_COLUMNS].reset_index(drop=True)
    note("Clean records", len(df))
    return df, log


def missing_value_summary(df):
    """Count and share of blanks left per predictor; the model pipeline imputes these."""
    rows = []
    for column in config.EARLY_NUMERIC_FEATURES:
        missing = int(df[column].isna().sum())
        rows.append({"variable": column, "missing": missing, "missing_pct": round(100 * missing / len(df), 1)})
    return pd.DataFrame(rows)


def class_distribution(series, classes=None):
    classes = classes or config.CLASSES
    counts = series.value_counts().reindex(classes, fill_value=0)
    return pd.DataFrame({
        "performance_class": classes,
        "records": counts.to_numpy(),
        "percent": np.round(100 * counts.to_numpy() / counts.sum(), 1),
    })
