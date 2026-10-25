"""Validate and save academic records from a CSV upload or the manual entry form (3.12.3).

Uses the same label rules as the data pipeline (ml/cleaning.py), so "nd 1", "1st" and
"2025/26" are understood. Every rejected row comes back with its row number, the field
and a plain-language reason.
"""
import io
import math

import pandas as pd
from sqlalchemy import select

from ml.cleaning import KEY_PREDICTORS, normalize_level, normalize_semester, normalize_session
from ml.grading import gpa_to_class

from .. import models as m
from .predictor import save_predictions

NUMERIC_RANGES = {
    "attendance_pct": (0, 100), "ca_score": (0, 100), "assignment_score": (0, 100),
    "exam_score": (0, 100), "prior_gpa": (0, 4), "gpa": (0, 4),
}
ALIASES = {
    "code": "student_code", "student": "student_code", "matric": "matric_number", "matric_no": "matric_number",
    "attendance": "attendance_pct", "attendance_%": "attendance_pct", "attendance_(%)": "attendance_pct",
    "ca": "ca_score", "ca_score_(%)": "ca_score", "assignment": "assignment_score",
    "exam": "exam_score", "previous_gpa": "prior_gpa", "semester_gpa": "gpa",
}
TEMPLATE_COLUMNS = ["student_code", "level", "session", "semester", "attendance_pct", "ca_score",
                    "assignment_score", "prior_gpa"]


def template_csv():
    example = ["S0001", "ND2", "2025/2026", "First", "82.5", "61", "70", "2.75"]
    return ",".join(TEMPLATE_COLUMNS) + "\n" + ",".join(example) + "\n"


def _number(raw):
    if raw is None:
        return None
    if isinstance(raw, float) and math.isnan(raw):
        return None
    text = str(raw).strip().rstrip("%")
    if text == "":
        return None
    return float(text)


class RowError(Exception):
    def __init__(self, field, message):
        super().__init__(message)
        self.field, self.message = field, message


def validate(db, row):
    """Check one row (a dict) and return clean values plus the matching student; raise RowError if invalid."""
    code = str(row.get("student_code") or "").strip().upper()
    matric = str(row.get("matric_number") or "").strip().upper()
    student = None
    if code:
        student = db.scalar(select(m.Student).where(m.Student.student_code == code))
    if student is None and matric:
        student = db.scalar(select(m.Student).where(m.Student.matric_number == matric))
    if student is None:
        who = code or matric or "(blank)"
        raise RowError("student_code", f"Student {who} is not registered. Add the student first.")

    clean = {}
    for field, normalise, allowed in (("level", normalize_level, "ND1, ND2, HND1 or HND2"),
                                      ("semester", normalize_semester, "First or Second"),
                                      ("session", normalize_session, "a session such as 2025/2026")):
        value = normalise(row.get(field))
        if value is None:
            raise RowError(field, f"'{row.get(field)}' is not valid; use {allowed}.")
        clean[field] = value

    for field, (low, high) in NUMERIC_RANGES.items():
        try:
            value = _number(row.get(field))
        except ValueError:
            raise RowError(field, f"'{row.get(field)}' is not a number.") from None
        if value is not None and not low <= value <= high:
            raise RowError(field, f"{value:g} is outside the allowed range {low}-{high}.")
        clean[field] = value

    missing = [f for f in KEY_PREDICTORS if clean[f] is None]
    if len(missing) >= 2:
        raise RowError(missing[0], "At least two of attendance, CA score and assignment score are needed.")

    if clean["prior_gpa"] is None:
        clean["prior_gpa"] = _previous_gpa(db, student, clean["session"], clean["semester"])
    clean["performance_class"] = gpa_to_class(clean["gpa"]) if clean["gpa"] is not None else None
    return student, clean


def _previous_gpa(db, student, session, semester):
    """Fill a missing previous GPA from the student's last record with a result."""
    order = {"First": 0, "Second": 1}
    current = (session, order[semester])
    best = None
    for record in student.records:
        key = (record.session, order.get(record.semester, 0))
        if record.gpa is not None and key < current and (best is None or key > best[0]):
            best = (key, record.gpa)
    return best[1] if best else None


def save_record(db, student, clean, source):
    """Insert or update the student's record for that session and semester."""
    record = db.scalar(select(m.AcademicRecord).where(
        m.AcademicRecord.student_id == student.id, m.AcademicRecord.session == clean["session"],
        m.AcademicRecord.semester == clean["semester"]))
    created = record is None
    if created:
        # Through the relationship, so later rows in the same upload see it (previous-GPA fill).
        record = m.AcademicRecord(student=student, source=source, **clean)
        db.add(record)
    else:
        # A blank cell means "not given", never "erase": stored values, results included, are kept.
        for field, value in clean.items():
            if value is not None and field != "performance_class":
                setattr(record, field, value)
        record.performance_class = gpa_to_class(record.gpa) if record.gpa is not None else None
        record.source = source
    if clean["session"] >= student.session:  # an old result must not move the student back a level
        student.level, student.session = clean["level"], clean["session"]
    db.flush()
    return record, created


def import_csv(db, content: bytes):
    try:
        frame = pd.read_csv(io.BytesIO(content), dtype=str, keep_default_na=False)
    except Exception as error:  # unreadable or empty file
        raise ValueError(f"The file could not be read as CSV: {error}") from None
    frame.columns = [ALIASES.get(c, c) for c in
                     (str(c).strip().lower().replace(" ", "_") for c in frame.columns)]
    if "student_code" not in frame.columns and "matric_number" not in frame.columns:
        raise ValueError("The file needs a student_code or matric_number column. Download the template to see the format.")

    errors, to_predict = [], {}  # keyed by record id: a repeated row is scored once
    created = updated = 0
    for index, row in frame.iterrows():
        line = int(index) + 2  # row 1 is the header
        try:
            student, clean = validate(db, row.to_dict())
        except RowError as error:
            errors.append({"row": line, "field": error.field, "message": error.message})
            continue
        record, is_new = save_record(db, student, clean, source="upload")
        created += is_new
        updated += not is_new
        if record.gpa is None:
            to_predict[record.id] = record
        else:
            to_predict.pop(record.id, None)
    db.commit()
    predictions, alerts = save_predictions(db, list(to_predict.values())) if to_predict else ([], 0)
    return {
        "rows_received": len(frame), "rows_accepted": len(frame) - len(errors), "rows_rejected": len(errors),
        "records_created": created, "records_updated": updated,
        "predictions_made": len(predictions), "alerts_raised": alerts, "errors": errors,
    }
