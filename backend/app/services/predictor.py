"""Turns academic records into predictions, explanations, advice and alerts (3.12.3).

The trained pipeline (backend/artifacts/model.joblib) is loaded once and shared; a
retrain swaps it under a lock so requests never see a half-loaded model.
"""
import json
import math
import threading

import joblib
import pandas as pd
from sqlalchemy import select

from ml import risk
from ml.explain import Explainer

from .. import models as m
from ..settings import get_settings
from .recommendations import recommend

_lock = threading.Lock()
_predictor = None


class Predictor:
    def __init__(self, model_path, meta_path):
        self.model = joblib.load(model_path)
        self.meta = json.loads(meta_path.read_text())
        self.version = self.meta["version"]
        self.features = list(self.meta["features"])
        self.labels = self.meta["feature_labels"]
        self.classes = [str(c) for c in self.model.named_steps["clf"].classes_]
        self.explainer = Explainer(self.model, self.features)

    def frame(self, records):
        return pd.DataFrame([{f: getattr(r, f) for f in self.features} for r in records], columns=self.features)

    def predict(self, records):
        """One result per record: class probabilities, risk level, explanation and advice."""
        if not records:
            return []
        X = self.frame(records)
        proba = self.model.predict_proba(X)
        contributions = self.explainer.contributions(X)
        fail_k = self.explainer.classes.index("Fail")
        results = []
        for i in range(len(records)):
            probs = {c: round(float(p), 4) for c, p in zip(self.classes, proba[i])}
            predicted = max(probs, key=lambda c: probs[c])
            fail_probability = probs["Fail"]
            level = risk.risk_level(fail_probability, predicted)
            explanation = sorted(
                ({"feature": f, "label": self.labels[f], "value": _plain(X.iloc[i][f]),
                  "contribution": round(float(contributions[i, j, fail_k]), 4)} for j, f in enumerate(self.features)),
                key=lambda item: abs(item["contribution"]), reverse=True)
            results.append({
                "predicted_class": predicted,
                "confidence_score": probs[predicted],
                "fail_probability": fail_probability,
                "probabilities": probs,
                "risk_level": level,
                "explanation": explanation,
                "recommendations": recommend(explanation, level),
            })
        return results


def _plain(value):
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return value.item() if hasattr(value, "item") else value


def get_predictor() -> Predictor:
    global _predictor
    with _lock:
        if _predictor is None:
            settings = get_settings()
            _predictor = Predictor(settings.model_path, settings.model_meta_path)
        return _predictor


def reload_predictor() -> Predictor:
    global _predictor
    settings = get_settings()
    fresh = Predictor(settings.model_path, settings.model_meta_path)
    with _lock:
        _predictor = fresh
    return fresh


def describe(feature, label, value):
    """'CA score of 45%', 'Previous GPA of 2.05', 'Attendance not recorded'."""
    name = label.replace(" (%)", "")
    if value is None:
        return f"{name} not recorded"
    if isinstance(value, (int, float)):
        shown = f"{value:.2f}" if "gpa" in feature else f"{value:.0f}%"
        return f"{name} of {shown}"
    return f"{name} {value}"


def alert_message(student, record, result):
    top = next((e for e in result["explanation"] if e["contribution"] > 0), None)
    reason = f" Main factor: {describe(top['feature'], top['label'], top['value'])}." if top else ""
    return (f"{student.full_name} ({record.level}) is at {result['risk_level'].lower()} risk of failing "
            f"{record.semester.lower()} semester {record.session}: probability of Fail "
            f"{result['fail_probability']:.0%}.{reason}")


def _open_alert(db, record_id):
    return db.scalar(select(m.Alert).join(m.Prediction)
                     .where(m.Prediction.record_id == record_id, m.Alert.status != "Resolved")
                     .order_by(m.Alert.id.desc()))


def save_predictions(db, records, predictor=None):
    """Predict for the given records and store a Prediction for each.

    A record keeps at most one open alert. Re-scoring an at-risk record moves its open alert
    (status and intervention notes included) to the new prediction; a record that is no
    longer at risk has its open alert closed automatically. Returns (predictions, new alerts).
    """
    predictor = predictor or get_predictor()
    created, alerts = [], 0
    for record, result in zip(records, predictor.predict(records)):
        prediction = m.Prediction(student_id=record.student_id, record_id=record.id,
                                  model_version=predictor.version, **result)
        db.add(prediction)
        existing = _open_alert(db, record.id)
        alert_type = f"{result['risk_level']} risk"
        message = alert_message(record.student, record, result)
        if risk.needs_alert(result["risk_level"]):
            if existing:
                existing.prediction = prediction
                existing.alert_type, existing.message = alert_type, message
            else:
                prediction.alert = m.Alert(alert_type=alert_type, message=message)
                alerts += 1
        elif existing:
            note = f"Closed automatically: model {predictor.version} now rates the student low risk."
            existing.status = "Resolved"
            existing.action_taken = f"{existing.action_taken} {note}" if existing.action_taken else note
        created.append(prediction)
    db.commit()
    return created, alerts
