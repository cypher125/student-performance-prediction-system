from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ml import config as ml_config
from ml import risk

from .. import models as m
from ..db import get_db
from ..queries import (alert_json, latest_predictions, prediction_json, record_json, records_chronological,
                       student_json)
from ..security import current_user
from ..services.predictor import get_predictor
from ..settings import get_settings

router = APIRouter(prefix="/api", tags=["Dashboard"])


def _mean(values):
    values = [v for v in values if v is not None]
    return round(sum(values) / len(values), 1) if values else None


def staff_dashboard(db: Session):
    settings = get_settings()
    predictions = latest_predictions(db)
    by_risk = Counter(p.risk_level for p in predictions)
    by_class = Counter(p.predicted_class for p in predictions)
    by_level = {level: Counter(p.risk_level for p in predictions if p.record.level == level)
                for level in ml_config.LEVELS}
    factors = Counter()
    for p in predictions:
        if p.risk_level in risk.ALERT_LEVELS:
            top = next((e for e in p.explanation if e["contribution"] > 0), None)
            if top:
                factors[top["label"]] += 1
    alert_counts = dict(db.execute(select(m.Alert.status, func.count()).group_by(m.Alert.status)).all())
    recent = db.scalars(select(m.Alert).order_by(m.Alert.id.desc()).limit(6)
                        .options(selectinload(m.Alert.prediction))).all()
    records = [p.record for p in predictions]
    meta = get_predictor().meta
    return {
        "role": "staff",
        "session": settings.current_session, "semester": settings.current_semester,
        "students_assessed": len(predictions),
        "risk_counts": {level: by_risk.get(level, 0) for level in risk.LEVELS},
        "predicted_class_counts": {c: by_class.get(c, 0) for c in ml_config.CLASSES},
        "risk_by_level": [{"level": level, **{r: by_level[level].get(r, 0) for r in risk.LEVELS}}
                          for level in ml_config.LEVELS],
        "top_risk_factors": [{"factor": f, "students": n} for f, n in factors.most_common()],
        "alert_counts": {s: alert_counts.get(s, 0) for s in m.ALERT_STATUSES},
        "averages": {"attendance_pct": _mean(r.attendance_pct for r in records),
                     "ca_score": _mean(r.ca_score for r in records),
                     "assignment_score": _mean(r.assignment_score for r in records)},
        "recent_alerts": [alert_json(a) for a in recent],
        "model": {"version": meta["version"], "accuracy": meta["test_metrics"]["accuracy"],
                  "f1_macro": meta["test_metrics"]["f1_macro"],
                  "fail_recall": meta["test_metrics"]["fail_recall"], "trained_on": meta["trained_on"]},
    }


def student_dashboard(db: Session, user: m.User):
    if user.student_id is None:
        raise HTTPException(404, "This account is not linked to a student record.")
    student = db.scalar(select(m.Student).where(m.Student.id == user.student_id).options(
        selectinload(m.Student.records), selectinload(m.Student.predictions).selectinload(m.Prediction.alert)))
    predictions = sorted(student.predictions, key=lambda p: p.id, reverse=True)
    alerts = [p.alert for p in predictions if p.alert]
    records = records_chronological(student)
    return {
        "role": "student",
        "student": student_json(student),
        "latest_prediction": prediction_json(predictions[0]) if predictions else None,
        "current_record": record_json(records[-1]) if records else None,
        "history": [record_json(r) for r in records if r.gpa is not None],
        "alerts": [alert_json(a) for a in alerts],
    }


@router.get("/dashboard", summary="Dashboard data for the signed-in user")
def dashboard(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    return student_dashboard(db, user) if user.role == "student" else staff_dashboard(db)
