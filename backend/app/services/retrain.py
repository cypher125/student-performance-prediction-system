"""Retrain the model on the records in the database (3.12.4: administrators retrain with new data).

Uses the tuned settings saved with the current model, measures accuracy on a fresh
80/20 split, refits on every record with results, archives the previous model file and
its metadata, and swaps the new one in. Runs on a background thread; the status can be polled.
"""
import json
import shutil
import threading
from datetime import date, datetime, timezone

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sqlalchemy import select

from ml import config as ml_config
from ml import evaluation, models
from ml.grading import gpa_to_class

from .. import models as m
from ..db import SessionLocal
from ..settings import get_settings
from .predictor import reload_predictor

MIN_RECORDS = 200
_lock = threading.Lock()
_state = {"status": "idle", "message": "No retraining has run since the server started.",
          "started_at": None, "finished_at": None, "version": None}


def status():
    with _lock:
        return dict(_state)


def start():
    with _lock:
        if _state["status"] == "running":
            return dict(_state)
        _state.update(status="running", message="Retraining in progress…", finished_at=None,
                      started_at=datetime.now(timezone.utc).isoformat())
    threading.Thread(target=_run, daemon=True).start()
    return status()


def _run():
    try:
        with SessionLocal() as db:
            meta = retrain(db)
        update = {"status": "done", "version": meta["version"],
                  "message": (f"Model {meta['version']} trained on {meta['dataset']['records']:,} records; "
                              f"test accuracy {meta['test_metrics']['accuracy']:.2f}.")}
    except Exception as error:  # report any failure to the admin page
        update = {"status": "failed", "message": f"Retraining failed: {error}"}
    with _lock:
        _state.update(finished_at=datetime.now(timezone.utc).isoformat(), **update)


def _next_version(version):
    major, minor, patch = (int(p) for p in version.split("."))
    return f"{major}.{minor}.{patch + 1}"


def retrain(db):
    settings = get_settings()
    old = json.loads(settings.model_meta_path.read_text())
    features = old["features"]
    params = {f"clf__{k}": v for k, v in old["settings"].items()}
    records = db.scalars(select(m.AcademicRecord).where(m.AcademicRecord.gpa.is_not(None))).all()
    if len(records) < MIN_RECORDS:
        raise ValueError(f"At least {MIN_RECORDS} records with results are needed; found {len(records)}.")
    data = pd.DataFrame([{**{f: getattr(r, f) for f in features},
                          ml_config.TARGET: r.performance_class or gpa_to_class(r.gpa)} for r in records])
    X, y = data[features], data[ml_config.TARGET]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y,
                                                        random_state=ml_config.SEED)
    model = models.make_pipeline(models.SIM, models.PRIMARY, features=features, **params)
    model.fit(X_train, y_train)
    proba = evaluation.ordered_proba(model, X_test)
    metrics = evaluation.classification_metrics(y_test, model.predict(X_test), proba)
    model.fit(X, y)

    version = _next_version(old["version"])
    shutil.copy2(settings.model_path, settings.model_path.with_name(f"model_v{old['version']}.joblib"))
    shutil.copy2(settings.model_meta_path, settings.model_meta_path.with_name(f"model_meta_v{old['version']}.json"))
    joblib.dump(model, settings.model_path, compress=3)
    prep, clf = model.named_steps["prep"], model.named_steps["clf"]
    importance = dict.fromkeys(features, 0.0)
    for column, value in zip(prep.get_feature_names_out(), clf.feature_importances_):
        importance[models.source_feature(column, features)] += float(value)
    meta = {
        **old,
        "version": version,
        "trained_on": date.today().isoformat(),
        "dataset": {"file": "database records with results", "records": len(data), "kind": "database"},
        "test_metrics": {k: round(float(v), 6) for k, v in metrics.items()},
        "previous_version": old["version"],
        "feature_importance": [{"feature": f, "impurity": round(v, 4)} for f, v in
                               sorted(importance.items(), key=lambda kv: kv[1], reverse=True)],
    }
    settings.model_meta_path.write_text(json.dumps(meta, indent=2))
    reload_predictor()
    return meta
