from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .. import models as m
from ..db import get_db
from ..queries import alert_json
from ..schemas import AlertUpdate
from ..security import current_user, require_staff

router = APIRouter(prefix="/api/alerts", tags=["Early-warning alerts"])


def _query():
    return select(m.Alert).options(
        selectinload(m.Alert.prediction).selectinload(m.Prediction.student),
        selectinload(m.Alert.prediction).selectinload(m.Prediction.record),
        selectinload(m.Alert.acknowledged_by_user)).order_by(m.Alert.id.desc())


@router.get("", summary="Alerts; students see only their own")
def list_alerts(alert_status: str | None = None, risk: str | None = None,
                user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    query = _query()
    if user.role == "student":
        query = query.join(m.Prediction).where(m.Prediction.student_id == user.student_id)
    alerts = db.scalars(query).all()
    rows = [alert_json(a) for a in alerts
            if (alert_status is None or a.status == alert_status)
            and (risk is None or a.prediction.risk_level == risk)]
    return {"count": len(rows), "alerts": rows}


@router.patch("/{alert_id}", summary="Acknowledge or resolve an alert and record the intervention")
def update_alert(alert_id: int, body: AlertUpdate, user: m.User = Depends(require_staff),
                 db: Session = Depends(get_db)):
    alert = db.scalar(_query().where(m.Alert.id == alert_id))
    if alert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found.")
    action = body.action_taken.strip() if body.action_taken is not None else None
    if body.status == "Resolved" and not (action or (action is None and alert.action_taken)):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT,
                            "Describe the intervention before resolving the alert.")
    if body.status != "New" and alert.acknowledged_at is None:
        alert.acknowledged_at = m.utcnow()
        alert.acknowledged_by = user.id
    alert.status = body.status
    if action is not None:
        alert.action_taken = action or None
    db.commit()
    db.refresh(alert)
    return alert_json(alert)
