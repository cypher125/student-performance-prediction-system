import numpy as np
import pandas as pd
import pytest

from ml import config, simulate
from ml.grading import gpa_to_class


@pytest.fixture(scope="module")
def cohorts():
    return simulate.simulate_cohorts(np.random.default_rng(config.SEED))


@pytest.fixture(scope="module")
def history(cohorts):
    return cohorts[0]


def test_same_seed_gives_identical_data(cohorts):
    again = simulate.simulate_cohorts(np.random.default_rng(config.SEED))
    for first, second in zip(cohorts, again):
        pd.testing.assert_frame_equal(first, second)


def test_only_table_3_1_fields_are_written(history):
    # Hidden traits (ability, engagement) must never leak into the dataset.
    assert list(history.columns) == simulate.COLUMNS


def test_history_covers_the_study_scope(history):
    assert set(history["session"]) == set(config.SESSIONS)
    assert set(history["level"]) == set(config.LEVELS)
    assert set(history["semester"]) == set(config.SEMESTERS)
    assert len(history) >= 500  # minimum sample in 3.5


def test_one_record_per_student_semester(history):
    assert not history.duplicated(subset=["student_code", "level", "session", "semester"]).any()


def test_values_stay_in_range(history):
    for column in ("attendance_pct", "ca_score", "assignment_score", "exam_score"):
        assert history[column].between(0, 100).all(), column
    assert history["gpa"].between(0, 4).all()
    assert history["prior_gpa"].dropna().between(0, 4).all()


def test_prior_gpa_is_the_previous_semesters_gpa(history):
    ordered = history.assign(
        _sem=history["semester"].map({"First": 0, "Second": 1})
    ).sort_values(by=["student_code", "session", "_sem"])
    previous_gpa = ordered.groupby("student_code")["gpa"].shift(1)
    known = previous_gpa.notna()
    assert known.sum() > 0
    assert np.allclose(ordered.loc[known, "prior_gpa"], previous_gpa[known])


def test_first_semester_prior_gpa_rules(history):
    nd1_first = history[(history["level"] == "ND1") & (history["semester"] == "First")]
    hnd1_first = history[(history["level"] == "HND1") & (history["semester"] == "First")]
    assert nd1_first["prior_gpa"].isna().all()  # new ND students have no GPA yet
    assert hnd1_first["prior_gpa"].between(2.0, 4.0).all()  # final ND CGPA


def test_class_mix_is_plausible(history):
    shares = history["gpa"].map(gpa_to_class).value_counts(normalize=True)
    assert set(shares.index) == set(config.CLASSES)
    assert shares.min() >= 0.03
    assert shares.idxmax() == "Pass"


def test_current_semester_is_before_exams(cohorts):
    history, current, _ = cohorts
    assert list(current.columns) == simulate.CURRENT_COLUMNS  # no exam score or GPA yet
    assert set(current["session"]) == {"2025/2026"}
    assert set(current["semester"]) == {"First"}
    assert set(current["level"]) == set(config.LEVELS)
    assert current.loc[current["level"] == "ND1", "prior_gpa"].isna().all()
    # Continuing students' previous GPA is their last historical GPA.
    last = history[(history["session"] == "2024/2025") & (history["semester"] == "Second")]
    joined = current.merge(last[["student_code", "gpa"]], on="student_code")
    assert len(joined) > 0
    assert np.allclose(joined["prior_gpa"], joined["gpa"])


def test_directory_names_every_student_with_a_sim_matric_number(cohorts):
    history, current, directory = cohorts
    codes = set(history["student_code"]) | set(current["student_code"])
    assert set(directory["student_code"]) == codes
    assert directory["matric_number"].is_unique
    assert directory["matric_number"].str.startswith("SIM/").all()


def test_raw_export_has_the_documented_imperfections(history):
    raw = simulate.add_record_keeping_noise(history, np.random.default_rng(7))
    assert len(raw) > len(history)  # duplicates
    assert raw["attendance_pct"].isna().any()
    assert (~raw["level"].isin(config.LEVELS)).any()  # label variants such as "nd 1"
