"""Grading rules shared by the simulator, the model pipeline and the web app.

Course grades follow the NBTE scale used by Nigerian polytechnics. Semester GPA
maps onto the study's four performance classes at the NBTE classification
cut-offs: Distinction >= 3.50, Merit 3.00-3.49 (Upper Credit), Pass 2.00-2.99
(Lower Credit and Pass), Fail < 2.00.
"""
import numpy as np

# (lowest score in band, letter grade, grade point), highest band first.
NBTE_SCALE = [
    (75, "A", 4.00),
    (70, "AB", 3.50),
    (65, "B", 3.25),
    (60, "BC", 3.00),
    (55, "C", 2.75),
    (50, "CD", 2.50),
    (45, "D", 2.25),
    (40, "E", 2.00),
    (0, "F", 0.00),
]

GPA_CLASS_BANDS = [(3.50, "Distinction"), (3.00, "Merit"), (2.00, "Pass"), (0.00, "Fail")]

# Portuguese 0-20 scale used by Cortez & Silva (2008), merged into the same four classes.
UCI_CLASS_BANDS = [(16, "Distinction"), (14, "Merit"), (10, "Pass"), (0, "Fail")]


def round_half_up(x):
    """Round like a mark sheet does (69.5 -> 70), not banker's rounding."""
    return np.floor(np.asarray(x, dtype=float) + 0.5)


def grade_points(total_scores):
    """Grade point for each course total (0-100) on the NBTE scale."""
    scores = round_half_up(total_scores)
    points = np.zeros_like(scores, dtype=float)
    for low, _letter, point in reversed(NBTE_SCALE):
        points = np.where(scores >= low, point, points)
    return points


def letter_grade(total_score):
    score = float(round_half_up(total_score))
    for low, letter, _point in NBTE_SCALE:
        if score >= low:
            return letter
    return "F"


def semester_gpa(total_scores, credit_units):
    """Credit-weighted GPA for one semester, to two decimal places."""
    points = grade_points(total_scores)
    units = np.asarray(credit_units, dtype=float)
    return round(float(np.sum(points * units) / np.sum(units)), 2)


def gpa_to_class(gpa):
    """Performance class for a semester GPA; None when the GPA is missing."""
    if gpa is None or (isinstance(gpa, float) and np.isnan(gpa)):
        return None
    gpa = round(float(gpa), 2)
    for cutoff, label in GPA_CLASS_BANDS:
        if gpa >= cutoff:
            return label
    return "Fail"


def uci_grade_to_class(g3):
    """Performance class for a UCI final grade on the 0-20 scale."""
    g3 = int(g3)
    for cutoff, label in UCI_CLASS_BANDS:
        if g3 >= cutoff:
            return label
    return "Fail"
