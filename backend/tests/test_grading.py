import math

import pytest

from ml.grading import gpa_to_class, grade_points, letter_grade, semester_gpa, uci_grade_to_class


@pytest.mark.parametrize("score, point, letter", [
    (100, 4.00, "A"), (75, 4.00, "A"), (74.5, 4.00, "A"), (74.4, 3.50, "AB"), (70, 3.50, "AB"),
    (69, 3.25, "B"), (65, 3.25, "B"), (64, 3.00, "BC"), (60, 3.00, "BC"), (55, 2.75, "C"),
    (50, 2.50, "CD"), (45, 2.25, "D"), (40, 2.00, "E"), (39.5, 2.00, "E"), (39.4, 0.00, "F"),
    (0, 0.00, "F"),
])
def test_nbte_scale(score, point, letter):
    assert grade_points([score])[0] == point
    assert letter_grade(score) == letter


def test_semester_gpa_weights_by_credit_units():
    # (4.00 x 3 + 0.00 x 1) / 4 units
    assert semester_gpa([80, 30], [3, 1]) == 3.00


@pytest.mark.parametrize("gpa, label", [
    (4.00, "Distinction"), (3.50, "Distinction"), (3.495, "Distinction"), (3.49, "Merit"),
    (3.00, "Merit"), (2.99, "Pass"), (2.00, "Pass"), (1.99, "Fail"), (0.00, "Fail"),
])
def test_gpa_to_class_uses_nbte_cutoffs(gpa, label):
    assert gpa_to_class(gpa) == label


def test_missing_gpa_has_no_class():
    assert gpa_to_class(math.nan) is None
    assert gpa_to_class(None) is None


@pytest.mark.parametrize("g3, label", [
    (20, "Distinction"), (16, "Distinction"), (15, "Merit"), (14, "Merit"), (13, "Pass"),
    (10, "Pass"), (9, "Fail"), (0, "Fail"),
])
def test_uci_grade_to_class(g3, label):
    assert uci_grade_to_class(g3) == label
