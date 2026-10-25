"""Early-warning rule: how a prediction becomes a risk level and an alert.

Risk is about failing (GPA below 2.00), the outcome intervention is meant to prevent.
It uses the model's probability of Fail, so a borderline student is flagged even
when Pass is the single most likely class.
"""
HIGH_RISK_PROBABILITY = 0.50
MEDIUM_RISK_PROBABILITY = 0.25
LEVELS = ["High", "Medium", "Low"]
ALERT_LEVELS = {"High", "Medium"}


def risk_level(fail_probability, predicted_class):
    if predicted_class == "Fail" or fail_probability >= HIGH_RISK_PROBABILITY:
        return "High"
    if fail_probability >= MEDIUM_RISK_PROBABILITY:
        return "Medium"
    return "Low"


def needs_alert(level):
    return level in ALERT_LEVELS
