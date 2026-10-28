import csv
import io
from collections import Counter

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ml import config as ml_config
from ml import risk

from .. import models as m
from ..db import get_db
from ..queries import latest_predictions
from ..security import require_staff
from ..services.predictor import AUTO_CLOSE_NOTE
from ..settings import get_settings

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/summary", summary="Summary report for the current semester")
def summary(_user: m.User = Depends(require_staff), db: Session = Depends(get_db)):
    settings = get_settings()
    predictions = latest_predictions(db)
    table = []
    for level in ml_config.LEVELS:
        group = [p for p in predictions if p.record.level == level]
        counts = Counter(p.risk_level for p in group)
        table.append({"level": level, "students": len(group), **{r: counts.get(r, 0) for r in risk.LEVELS},
                      "at_risk_pct": round(100 * (counts["High"] + counts["Medium"]) / len(group), 1) if group else 0})
    # This semester's alerts only; an intervention is a note written by staff, not the automatic closing note.
    alerts = db.scalars(select(m.Alert).join(m.Prediction, m.Alert.prediction_id == m.Prediction.id)
                        .join(m.AcademicRecord, m.Prediction.record_id == m.AcademicRecord.id)
                        .where(m.AcademicRecord.session == settings.current_session,
                               m.AcademicRecord.semester == settings.current_semester)).all()
    return {
        "session": settings.current_session, "semester": settings.current_semester,
        "students_assessed": len(predictions),
        "by_level": table,
        "predicted_classes": dict(Counter(p.predicted_class for p in predictions)),
        "alerts": {s: sum(a.status == s for a in alerts) for s in m.ALERT_STATUSES},
        "interventions_recorded": sum(bool(a.action_taken) and not a.action_taken.startswith(AUTO_CLOSE_NOTE)
                                      for a in alerts),
    }


@router.get("/predictions.csv", summary="Export the current semester's predictions as CSV")
def export_predictions(_user: m.User = Depends(require_staff), db: Session = Depends(get_db)):
    settings = get_settings()
    rows = sorted(latest_predictions(db), key=lambda p: (-p.fail_probability, p.student.student_code))
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["student_code", "matric_number", "name", "level", "attendance_pct", "ca_score",
                     "assignment_score", "prior_gpa", "predicted_class", "fail_probability", "risk_level",
                     "main_factor", "alert_status", "model_version"])
    for p in rows:
        top = next((e["label"] for e in p.explanation if e["contribution"] > 0), "")
        r = p.record
        writer.writerow([p.student.student_code, p.student.matric_number, p.student.full_name, r.level,
                         r.attendance_pct, r.ca_score, r.assignment_score, r.prior_gpa, p.predicted_class,
                         round(p.fail_probability, 3), p.risk_level, top,
                         p.alert.status if p.alert else "", p.model_version])
    name = f"predictions_{settings.current_session.replace('/', '-')}_{settings.current_semester.lower()}.csv"
    return Response(buffer.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="{name}"'})
