import math

import numpy as np
import pandas as pd
import pytest

from ml import config, simulate
from ml.cleaning import (ID_COLUMNS, clean_records, normalize_level, normalize_semester,
                         normalize_session)


@pytest.mark.parametrize("raw, expected", [
    ("ND1", "ND1"), ("nd 1", "ND1"), ("HND-2", "HND2"), ("Hnd1", "HND1"), ("ND3", None), (math.nan, None),
])
def test_normalize_level(raw, expected):
    assert normalize_level(raw) == expected


@pytest.mark.parametrize("raw, expected", [
    ("First", "First"), ("1st", "First"), ("FIRST", "First"), ("second semester", "Second"),
    ("2nd", "Second"), ("third", None), (None, None),
])
def test_normalize_semester(raw, expected):
    assert normalize_semester(raw) == expected


@pytest.mark.parametrize("raw, expected", [
    ("2021/2022", "2021/2022"), ("2021/22", "2021/2022"), ("2021-2022", "2021/2022"),
    ("2021 / 2022", "2021/2022"), ("2021/2023", None), ("session", None),
])
def test_normalize_session(raw, expected):
    assert normalize_session(raw) == expected


def _row(code, **overrides):
    row = {"student_code": code, "level": "ND2", "session": "2022/2023", "semester": "First",
           "attendance_pct": 80.0, "ca_score": 60.0, "assignment_score": 65.0, "exam_score": 50.0,
           "gpa": 2.75, "prior_gpa": 2.5}
    row.update(overrides)
    return row


def test_clean_records_fixes_each_problem():
    raw = pd.DataFrame([
        _row("S0001"),
        _row("s0001 ", level="nd 2", semester="1st", session="2022/23"),  # same record, messy labels
        _row("S0002", attendance_pct=833.0),                              # typo: blanked, row kept
        _row("S0003", gpa=np.nan),                                        # no outcome: removed
        _row("S0004", attendance_pct=np.nan, assignment_score=np.nan),    # two key gaps: removed
        _row("S0005", level="ND3"),                                       # unknown level: removed
        _row("S0006", gpa=3.6),
    ])
    clean, log = clean_records(raw)

    assert list(clean["student_code"]) == ["S0001", "S0002", "S0006"]
    assert math.isnan(clean.loc[1, "attendance_pct"])
    assert list(clean[config.TARGET]) == ["Pass", "Pass", "Distinction"]
    affected = {step["step"]: step["records_affected"] for step in log}
    assert affected["Duplicate records removed (same student, level, session and semester)"] == 1
    assert log[-1]["records_remaining"] == 3


def test_noise_then_cleaning_recovers_the_source_values():
    rng = np.random.default_rng(1)
    records = simulate.simulate_cohorts(rng)[0]
    raw = simulate.add_record_keeping_noise(records, rng)
    clean, _ = clean_records(raw)

    assert len(clean) < len(raw)
    assert not clean.duplicated(subset=ID_COLUMNS).any()
    assert clean["gpa"].between(0, 4).all()
    assert clean["attendance_pct"].dropna().between(0, 100).all()
    merged = clean.merge(records, on=ID_COLUMNS, suffixes=("", "_source"))
    assert len(merged) == len(clean)  # every clean record traces back to a source record
    for column in ("ca_score", "exam_score", "gpa"):
        known = merged[column].notna()
        assert np.allclose(merged.loc[known, column], merged.loc[known, f"{column}_source"]), column
