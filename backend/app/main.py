"""Application entry point.

Run from the backend folder:  python -m uvicorn app.main:app --port 8000
Serves the REST API under /api, interactive API documentation at /docs, and, once the
frontend has been built (frontend/out), the web interface itself at /.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api import alerts, auth, dashboard, model, records, reports, students, users
from .db import create_tables
from .services.predictor import get_predictor
from .settings import get_settings

log = logging.getLogger("sapps")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_tables()
    try:
        predictor = get_predictor()
        log.info("Model %s loaded (%s)", predictor.version, ", ".join(predictor.features))
    except FileNotFoundError:
        log.warning("No trained model found: run `python -m ml.train_models` first.")
    yield


settings = get_settings()
app = FastAPI(
    title=f"{settings.app_name} API",
    version="1.0.0",
    description=("Predicts students' performance class (Distinction, Merit, Pass, Fail) from records available "
                 "before final examinations, explains each prediction with SHAP, and raises early-warning alerts."),
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

for module in (auth, dashboard, students, records, alerts, model, reports, users):
    app.include_router(module.router)


@app.get("/api/health", tags=["Health"], summary="Is the service up, and which model is loaded?")
def health():
    try:
        version = get_predictor().version
    except FileNotFoundError:
        version = None
    return {"status": "ok", "model_version": version}


if settings.frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=settings.frontend_dir, html=True), name="frontend")
