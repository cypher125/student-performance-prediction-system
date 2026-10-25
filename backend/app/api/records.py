from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .. import models as m
from ..db import get_db
from ..queries import prediction_json, record_json
from ..schemas import RecordIn
from ..security import require_staff
from ..services import importer
from ..services.predictor import get_predictor, save_predictions
from ..settings import get_settings

router = APIRouter(prefix="/api", tags=["Records and predictions"])
MAX_UPLOAD_BYTES = 2 * 1024 * 1024


@router.get("/records/template", summary="Download the CSV upload template")
def template(_user: m.User = Depends(require_staff)):
    return Response(importer.template_csv(), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="records_template.csv"'})


@router.post("/records/upload", summary="Upload a CSV of semester records; predicts for records without results")
def upload(file: UploadFile = File(...), _user: m.User = Depends(require_staff),
           db: Session = Depends(get_db)):
    # A plain function, so FastAPI runs the parsing and scoring in its threadpool
    # instead of blocking every other request.
    content = file.file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "The file is larger than 2 MB.")
    try:
        return importer.import_csv(db, content)
    except ValueError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from None


@router.post("/records", summary="Enter one record by hand; predicts if it has no results yet")
def create_record(body: RecordIn, _user: m.User = Depends(require_staff), db: Session = Depends(get_db)):
    try:
        student, clean = importer.validate(db, body.model_dump())
    except importer.RowError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT,
                            {"field": error.field, "message": error.message}) from None
    record, created = importer.save_record(db, student, clean, source="manual")
    db.commit()
    prediction = None
    if record.gpa is None:
        saved, _ = save_predictions(db, [record])
        prediction = prediction_json(saved[0])
    return {"record": record_json(record), "created": created, "prediction": prediction}


@router.post("/predictions/run", summary="Predict for current-semester records not yet scored by the current model")
def run_predictions(_user: m.User = Depends(require_staff), db: Session = Depends(get_db)):
    settings = get_settings()
    version = get_predictor().version
    records = db.scalars(select(m.AcademicRecord).where(
        m.AcademicRecord.session == settings.current_session, m.AcademicRecord.semester == settings.current_semester,
        m.AcademicRecord.gpa.is_(None)).options(selectinload(m.AcademicRecord.predictions),
                                                selectinload(m.AcademicRecord.student))).all()
    pending = [r for r in records if not any(p.model_version == version for p in r.predictions)]
    saved, alerts = save_predictions(db, pending) if pending else ([], 0)
    return {"records_checked": len(records), "predictions_made": len(saved), "alerts_raised": alerts,
            "model_version": version}
