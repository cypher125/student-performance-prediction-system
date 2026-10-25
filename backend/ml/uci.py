"""Prepare the UCI Student Performance dataset (Cortez & Silva, 2008).

This is the study's real-data source. Its fields map onto the study's variables:

  UCI field   Study variable    Meaning
  absences    absences          number of school absences (the attendance indicator)
  G1 (0-20)   ca1_score (%)     first-period grade: the early continuous assessment
  G2 (0-20)   ca2_score (%)     second-period grade: a later continuous assessment
  failures    past_failures     past class failures (prior academic history)
  studytime   study_time        weekly study time, 1 (<2 h) to 4 (>10 h)
  G3 (0-20)   final_score (%)   final grade, which gives performance_class

Classes use the Portuguese 0-20 scale: Distinction 16-20, Merit 14-15,
Pass 10-13, Fail 0-9 (Cortez & Silva's five levels with 10-11 and 12-13 merged).
"""
import pandas as pd

from . import config
from .grading import uci_grade_to_class

COURSE_FILES = {"por": "student-por.csv", "mat": "student-mat.csv"}
# Known by the end of the first period, before the final grade (H02).
EARLY_FEATURES = ["absences", "ca1_score", "past_failures", "study_time"]
# Adds the second-period grade: later in the year, closer to the final grade.
MID_FEATURES = EARLY_FEATURES + ["ca2_score"]


def load_raw(course="por"):
    return pd.read_csv(config.RAW_UCI_DIR / COURSE_FILES[course], sep=";")


def prepare(raw, course="por"):
    prefix = {"por": "P", "mat": "M"}[course]
    grades = raw[["G1", "G2", "G3"]].astype(int)
    out = pd.DataFrame({
        "student_id": [f"{prefix}{i:04d}" for i in range(1, len(raw) + 1)],
        "school": raw["school"],
        "absences": raw["absences"].astype(int),
        "ca1_score": grades["G1"] * 5,
        "ca2_score": grades["G2"] * 5,
        "past_failures": raw["failures"].astype(int),
        "study_time": raw["studytime"].astype(int),
        "final_score": grades["G3"] * 5,
        "G1": grades["G1"],
        "G2": grades["G2"],
        "G3": grades["G3"],
    })
    out[config.TARGET] = grades["G3"].map(uci_grade_to_class)
    return out
