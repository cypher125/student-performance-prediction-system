import pytest

from ml import config, uci


@pytest.mark.parametrize("course, students", [("por", 649), ("mat", 395)])
def test_prepare_keeps_every_student(course, students):
    df = uci.prepare(uci.load_raw(course), course)
    assert len(df) == students
    assert df["student_id"].is_unique
    assert df[config.TARGET].isin(config.CLASSES).all()


def test_grades_are_rescaled_to_percent():
    df = uci.prepare(uci.load_raw("por"), "por")
    assert (df["ca1_score"] == df["G1"] * 5).all()
    assert (df["ca2_score"] == df["G2"] * 5).all()
    assert (df["final_score"] == df["G3"] * 5).all()


def test_class_boundaries_follow_the_0_to_20_scale():
    df = uci.prepare(uci.load_raw("por"), "por")
    assert set(df.loc[df["G3"] >= 16, config.TARGET]) == {"Distinction"}
    assert set(df.loc[df["G3"].between(14, 15), config.TARGET]) == {"Merit"}
    assert set(df.loc[df["G3"].between(10, 13), config.TARGET]) == {"Pass"}
    assert set(df.loc[df["G3"] <= 9, config.TARGET]) == {"Fail"}
