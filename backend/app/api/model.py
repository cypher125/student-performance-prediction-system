from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models as m
from ..db import get_db
from ..security import require_admin, require_staff
from ..services import retrain
from ..services.predictor import get_predictor

router = APIRouter(prefix="/api/model", tags=["Model"])


@router.get("", summary="The deployed model: version, test metrics and feature importance")
def model_info(_user: m.User = Depends(require_staff), db: Session = Depends(get_db)):
    meta = get_predictor().meta
    with_results = db.scalar(select(func.count()).select_from(m.AcademicRecord)
                             .where(m.AcademicRecord.gpa.is_not(None)))
    return {**meta, "records_available_for_retraining": with_results, "retrain": retrain.status()}


@router.post("/retrain", summary="Retrain on the records in the database (runs in the background)")
def start_retrain(_user: m.User = Depends(require_admin)):
    return retrain.start()


@router.get("/retrain", summary="Progress of the latest retraining")
def retrain_status(_user: m.User = Depends(require_admin)):
    return retrain.status()
