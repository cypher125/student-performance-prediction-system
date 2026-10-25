from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .. import models as m
from ..db import get_db
from ..queries import (alert_json, latest_predictions, prediction_json, record_json, records_chronological,
                       student_json)
from ..schemas import StudentIn
from ..security import current_user, require_staff
from ..settings import get_settings

router = APIRouter(prefix="/api/students", tags=["Students"])
RISK_ORDER = {"High": 0, "Medium": 1, "Low": 2, None: 3}


@router.get("", summary="Students with their current-semester prediction")
def list_students(search: str = "", level: str | None = None, risk: str | None = None,
                  scope: str = Query("current", pattern="^(current|all)$"),
                  _user: m.User = Depends(require_staff), db: Session = Depends(get_db)):
    settings = get_settings()
    latest = {p.student_id: p for p in latest_predictions(db)}
    students = db.scalars(select(m.Student).options(selectinload(m.Student.records))).all()
    term = search.strip().lower()
    rows = []
    for student in students:
        records = records_chronological(student)
        current = next((r for r in records if r.session == settings.current_session
                        and r.semester == settings.current_semester), None)
        if scope == "current" and current is None:
            continue
        prediction = latest.get(student.id)
        if level and student.level != level:
            continue
        if risk and (prediction is None or prediction.risk_level != risk):
            continue
        if term and term not in f"{student.student_code} {student.matric_number} {student.full_name}".lower():
            continue
        last_result = next((r for r in reversed(records) if r.gpa is not None), None)
        rows.append({
            **student_json(student),
            "current_record": record_json(current) if current else None,
            "last_gpa": last_result.gpa if last_result else None,
            "prediction": prediction_json(prediction, full=False) if prediction else None,
            "alert_status": prediction.alert.status if prediction and prediction.alert else None,
        })
    rows.sort(key=lambda r: (RISK_ORDER[r["prediction"]["risk_level"] if r["prediction"] else None],
                             -(r["prediction"]["fail_probability"] if r["prediction"] else 0), r["code"]))
    return {"count": len(rows), "students": rows}


@router.get("/{code}", summary="One student's records, predictions and alerts")
def get_student(code: str, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    student = db.scalar(select(m.Student).where(m.Student.student_code == code.upper()).options(
        selectinload(m.Student.records),
        selectinload(m.Student.predictions).selectinload(m.Prediction.alert)))
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found.")
    if user.role == "student" and user.student_id != student.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only view your own record.")
    predictions = sorted(student.predictions, key=lambda p: p.id, reverse=True)
    return {
        "student": student_json(student),
        "records": [record_json(r) for r in records_chronological(student)],
        "predictions": [prediction_json(p) for p in predictions],
        "alerts": [alert_json(p.alert) for p in predictions if p.alert],
    }


@router.post("", status_code=status.HTTP_201_CREATED, summary="Register a new student")
def create_student(body: StudentIn, _user: m.User = Depends(require_staff), db: Session = Depends(get_db)):
    matric = body.matric_number.strip().upper()
    if db.scalar(select(m.Student).where(m.Student.matric_number == matric)):
        raise HTTPException(status.HTTP_409_CONFLICT, f"A student with matric number {matric} already exists.")
    codes = db.scalars(select(m.Student.student_code)).all()
    next_number = max((int(c[1:]) for c in codes if c[1:].isdigit()), default=0) + 1
    student = m.Student(student_code=f"S{next_number:04d}", matric_number=matric,
                        first_name=body.first_name.strip(), last_name=body.last_name.strip(),
                        programme="HND" if body.level.startswith("HND") else "ND", level=body.level,
                        session=body.session, entry_session=body.session)
    db.add(student)
    db.commit()
    return student_json(student)
