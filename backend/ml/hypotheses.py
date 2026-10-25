"""Statistical tests of the study's hypotheses (1.6) at the 5% significance level.

H01: there is no significant relationship between attendance, CA scores and final
performance. Tests: Spearman correlation of each with the final outcome; a multiple
linear regression of the final outcome on both (overall F-test); Kruskal-Wallis
tests of each across the four performance classes. H01 is rejected when the
regression F-test is significant.

H02: a machine-learning model cannot accurately predict performance categories from
early-semester data. "Accurately" is made testable in two ways. The Random Forest
must beat chance: a permutation test compares its cross-validated accuracy with 100
runs on shuffled labels. It must also beat the majority-class baseline on the test
set: a one-sided binomial test. H02 is rejected only when both are significant.
"""
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.model_selection import StratifiedKFold, permutation_test_score

from . import config

ALPHA = 0.05
N_PERMUTATIONS = 100


def _decision(p_value):
    return "Reject H0" if p_value < ALPHA else "Do not reject H0"


def test_h01(df, attendance, ca, outcome, labels):
    """labels maps each column name to the words used in the table."""
    data = df[[attendance, ca, outcome, config.TARGET]].dropna()
    n = len(data)
    rows = []
    for column in (attendance, ca):
        rho, p = stats.spearmanr(data[column], data[outcome])
        rows.append({"test": f"Spearman correlation: {labels[column]} and {labels[outcome]}",
                     "statistic": rho, "p_value": p, "n": n})

    X = np.column_stack([np.ones(n), data[attendance], data[ca]])
    y = data[outcome].to_numpy(dtype=float)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    residual = y - X @ beta
    r2 = 1 - (residual @ residual) / np.sum((y - y.mean()) ** 2)
    k = 2
    f_stat = (r2 / k) / ((1 - r2) / (n - k - 1))
    p_regression = stats.f.sf(f_stat, k, n - k - 1)
    rows.append({"test": (f"Multiple regression of {labels[outcome]} on {labels[attendance]} and "
                          f"{labels[ca]}: overall F-test (R-squared = {r2:.3f}; coefficients "
                          f"{beta[1]:+.4f} and {beta[2]:+.4f})"),
                 "statistic": f_stat, "p_value": p_regression, "n": n})

    for column in (attendance, ca):
        groups = [data.loc[data[config.TARGET] == c, column] for c in config.CLASSES
                  if (data[config.TARGET] == c).any()]
        h_stat, p = stats.kruskal(*groups)
        rows.append({"test": f"Kruskal-Wallis: {labels[column]} across the performance classes",
                     "statistic": h_stat, "p_value": p, "n": n})

    table = pd.DataFrame(rows)
    table["decision"] = table["p_value"].map(_decision)
    verdict = "Reject H01" if p_regression < ALPHA else "Do not reject H01"
    return table, verdict


def test_h02(model, X_train, y_train, test_correct, test_n, majority_share):
    cv = StratifiedKFold(5, shuffle=True, random_state=config.SEED)
    score, permuted, p_perm = permutation_test_score(
        model, X_train, y_train, cv=cv, n_permutations=N_PERMUTATIONS, scoring="accuracy",
        random_state=config.SEED, n_jobs=1)
    binomial = stats.binomtest(int(test_correct), int(test_n), float(majority_share), alternative="greater")
    rows = [
        {"test": (f"Permutation test: cross-validated accuracy against {N_PERMUTATIONS} runs on "
                  "shuffled labels"),
         "model_value": score, "reference_value": float(np.mean(permuted)), "p_value": p_perm},
        {"test": "One-sided binomial test: test-set accuracy against the majority-class rate",
         "model_value": test_correct / test_n, "reference_value": majority_share, "p_value": binomial.pvalue},
    ]
    table = pd.DataFrame(rows)
    table["decision"] = table["p_value"].map(_decision)
    verdict = "Reject H02" if (table["p_value"] < ALPHA).all() else "Do not reject H02"
    return table, verdict
