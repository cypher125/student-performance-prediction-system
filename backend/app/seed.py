"""Load the simulated data into the database and create demo accounts.

Run from the backend folder:
    python -m app.seed           fill an empty database
    python -m app.seed --reset   delete the database first, then fill it

Everything loaded is SIMULATED (see docs/datasets.md); names are fictional and every
matric number starts with SIM/.
"""
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import func, select

from ml import config as ml_config

from . import models as m
from .db import SessionLocal, create_tables, engine
from .security import hash_password
from .services.predictor import save_predictions
from .settings import get_settings

STAFF = [
    ("admin", "System Administrator", "admin", "Admin@2026"),
    ("lecturer", "Dr. Funmilayo Adeyemi", "lecturer", "Lecturer@2026"),
    ("adviser", "Mr. Chinedu Eze", "adviser", "Adviser@2026"),
]
STUDENT_PASSWORD = "Student@2026"


def _value(v):
    return None if pd.isna(v) else float(v)


def seed():
    settings = get_settings()
    directory = pd.read_csv(ml_config.SIM_DIRECTORY_CSV)
    history = pd.read_csv(ml_config.SIM_CLEAN_CSV)
    current = pd.read_csv(ml_config.SIM_CURRENT_CSV)

    with SessionLocal() as db:
        if db.scalar(select(func.count()).select_from(m.Student)):
            sys.exit("The database already has data. Run `python -m app.seed --reset` to start again.")

        latest = {}  # newest level and session per student
        for frame in (history, current):
            for row in frame.itertuples():
                key = (row.session, 0 if row.semester == "First" else 1)
                if row.student_code not in latest or key >= latest[row.student_code][0]:
                    latest[row.student_code] = (key, row.level, row.session)
        students = {}
        for row in directory.itertuples():
            if row.student_code not in latest:
                continue
            _, level, session = latest[row.student_code]
            students[row.student_code] = m.Student(
                student_code=row.student_code, matric_number=row.matric_number, first_name=row.first_name,
                last_name=row.last_name, department=row.department, programme=row.programme, level=level,
                session=session, entry_session=row.entry_session)
        db.add_all(students.values())
        db.flush()

        for row in history.itertuples():
            db.add(m.AcademicRecord(
                student_id=students[row.student_code].id, level=row.level, session=row.session,
                semester=row.semester, attendance_pct=_value(row.attendance_pct), ca_score=_value(row.ca_score),
                assignment_score=_value(row.assignment_score), prior_gpa=_value(row.prior_gpa),
                exam_score=_value(row.exam_score), gpa=_value(row.gpa),
                performance_class=row.performance_class, source="seed"))
        current_records = []
        for row in current.itertuples():
            record = m.AcademicRecord(
                student_id=students[row.student_code].id, level=row.level, session=row.session,
                semester=row.semester, attendance_pct=_value(row.attendance_pct), ca_score=_value(row.ca_score),
                assignment_score=_value(row.assignment_score), prior_gpa=_value(row.prior_gpa), source="seed")
            db.add(record)
            current_records.append(record)

        for username, name, role, password in STAFF:
            db.add(m.User(username=username, full_name=name, role=role, password_hash=hash_password(password),
                          email=f"{username}@demo.sapps.local"))
        student_hash = hash_password(STUDENT_PASSWORD)  # one hash shared by the demo student accounts
        current_codes = set(current["student_code"])
        for code in sorted(current_codes):
            student = students[code]
            db.add(m.User(username=code.lower(), full_name=student.full_name, role="student",
                          password_hash=student_hash, student_id=student.id))
        db.commit()

        for record in current_records:
            db.refresh(record)
        print(f"Predicting for {len(current_records)} current-semester records ({settings.current_session}, "
              f"{settings.current_semester} semester)…", flush=True)
        predictions, alerts = save_predictions(db, current_records)

        print(f"Students: {len(students):,}  Records: {len(history) + len(current):,}  "
              f"Predictions: {len(predictions)}  Alerts: {alerts}")
        print("\nDemo sign-in details:")
        for username, _name, role, password in STAFF:
            print(f"  {role:9s} username {username:9s} password {password}")
        example = sorted(current_codes)[0].lower()
        print(f"  student   username = student code in lower case, e.g. {example}; password {STUDENT_PASSWORD}")


def main():
    url = get_settings().database_url
    if "--reset" in sys.argv and url.startswith("sqlite:///"):
        engine.dispose()
        Path(url.removeprefix("sqlite:///")).unlink(missing_ok=True)
    create_tables()
    seed()


if __name__ == "__main__":
    main()
