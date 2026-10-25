"""Shared queries and the JSON shapes the API returns."""
from datetime import timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from . import models as m
from .settings import get_settings

SEMESTER_ORDER = {"First": 0, "Second": 1}


def iso(value):
    """ISO time with its UTC offset. SQLite returns stored UTC times without one, so the
    browser would otherwise show them as local time."""
    if not value:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def student_json(student: m.Student):
    return {
        "code": student.student_code, "matric_number": student.matric_number,
        "first_name": student.first_name, "last_name": student.last_name, "full_name": student.full_name,
        "department": student.department, "programme": student.programme, "level": student.level,
        "session": student.session, "entry_session": student.entry_session,
    }


def record_json(record: m.AcademicRecord):
    return {
        "id": record.id, "level": record.level, "session": record.session, "semester": record.semester,
        "attendance_pct": record.attendance_pct, "ca_score": record.ca_score,
        "assignment_score": record.assignment_score, "prior_gpa": record.prior_gpa,
        "exam_score": record.exam_score, "gpa": record.gpa, "performance_class": record.performance_class,
        "has_results": record.gpa is not None, "source": record.source,
    }


def prediction_json(prediction: m.Prediction, full=True):
    out = {
        "id": prediction.id, "record_id": prediction.record_id, "predicted_class": prediction.predicted_class,
        "confidence_score": prediction.confidence_score, "fail_probability": prediction.fail_probability,
        "risk_level": prediction.risk_level, "model_version": prediction.model_version,
        "created_at": iso(prediction.created_at),
    }
    if full:
        out.update(probabilities=prediction.probabilities, explanation=prediction.explanation,
                   recommendations=prediction.recommendations)
    else:
        top = next((e for e in prediction.explanation if e["contribution"] > 0), None)
        out["top_factor"] = top["label"] if top else None
    return out


def alert_json(alert: m.Alert):
    prediction = alert.prediction
    student = prediction.student
    record = prediction.record
    return {
        "id": alert.id, "alert_type": alert.alert_type, "message": alert.message, "status": alert.status,
        "sent_at": iso(alert.sent_at), "acknowledged_at": iso(alert.acknowledged_at),
        "acknowledged_by": alert.acknowledged_by_user.full_name if alert.acknowledged_by_user else None,
        "action_taken": alert.action_taken,
        "student": {"code": student.student_code, "full_name": student.full_name, "level": record.level},
        "risk_level": prediction.risk_level, "fail_probability": prediction.fail_probability,
        "session": record.session, "semester": record.semester,
    }


def latest_predictions(db: Session, session_name=None, semester=None):
    """Newest prediction per record for one session and semester (default: the current one)."""
    settings = get_settings()
    session_name = session_name or settings.current_session
    semester = semester or settings.current_semester
    rows = db.scalars(
        select(m.Prediction).join(m.AcademicRecord)
        .where(m.AcademicRecord.session == session_name, m.AcademicRecord.semester == semester)
        .options(selectinload(m.Prediction.student), selectinload(m.Prediction.record),
                 selectinload(m.Prediction.alert))
        .order_by(m.Prediction.id.desc())
    ).all()
    newest = {}
    for prediction in rows:
        newest.setdefault(prediction.record_id, prediction)
    return list(newest.values())


def records_chronological(student: m.Student):
    return sorted(student.records, key=lambda r: (r.session, SEMESTER_ORDER.get(r.semester, 0)))
