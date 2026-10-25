"""Model definitions shared by the experiments and the web app.

Every model is a scikit-learn Pipeline: preprocessing (fill gaps with the training
median plus a "was missing" flag, then scale or one-hot encode where the algorithm
needs it) followed by the classifier. The same steps run in training, evaluation
and the live system, so nothing learned from test data leaks into training.
"""
from dataclasses import dataclass

from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from . import config, uci

# Random Forest builds trees on threads (no extra memory); the machine has 2 CPUs.
N_JOBS = 2


@dataclass(frozen=True)
class DatasetSpec:
    key: str
    title: str
    numeric: tuple
    categorical: tuple
    labels: dict

    @property
    def features(self):
        return list(self.numeric) + list(self.categorical)


SIM = DatasetSpec(
    key="sim",
    title="simulated YABATECH dataset",
    numeric=tuple(config.EARLY_NUMERIC_FEATURES),
    categorical=tuple(config.EARLY_CATEGORICAL_FEATURES),
    labels={"attendance_pct": "Attendance (%)", "ca_score": "CA score (%)",
            "assignment_score": "Assignment score (%)", "prior_gpa": "Previous GPA", "level": "Level"},
)
UCI = DatasetSpec(
    key="uci",
    title="UCI Student Performance dataset",
    numeric=tuple(uci.EARLY_FEATURES),
    categorical=(),
    labels={"absences": "Absences", "ca1_score": "First-period grade (%)",
            "past_failures": "Past failures", "study_time": "Weekly study time"},
)


def preprocessor(spec, scale, features=None):
    features = features or spec.features
    numeric = [f for f in spec.numeric if f in features]
    categorical = [f for f in spec.categorical if f in features]
    steps: list[tuple] = [("impute", SimpleImputer(strategy="median", add_indicator=True))]
    if scale:
        steps.append(("scale", StandardScaler()))
    transformers: list[tuple] = [("num", Pipeline(steps), numeric)]
    if categorical:
        transformers.append(("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical))
    return ColumnTransformer(transformers, verbose_feature_names_out=False)


def source_feature(transformed_name, features):
    """Map a transformed column (e.g. 'missingindicator_prior_gpa', 'level_ND1') to its input feature."""
    name = transformed_name.removeprefix("missingindicator_")
    if name in features:
        return name
    for feature in features:
        if name.startswith(f"{feature}_"):
            return feature
    return name


# name -> (classifier, needs scaling, hyperparameter grid searched with 5-fold CV)
CANDIDATES = {
    "Random Forest": (
        RandomForestClassifier(n_estimators=300, random_state=config.SEED, n_jobs=N_JOBS),
        False,
        {"clf__max_depth": [None, 10], "clf__min_samples_leaf": [1, 3, 5],
         "clf__max_features": ["sqrt", 0.6], "clf__class_weight": [None, "balanced"]},
    ),
    "Logistic Regression": (LogisticRegression(max_iter=3000), True, {"clf__C": [0.1, 1.0, 10.0]}),
    "Decision Tree": (
        DecisionTreeClassifier(random_state=config.SEED),
        False,
        {"clf__max_depth": [3, 5, 8, None], "clf__min_samples_leaf": [1, 5, 10]},
    ),
    "Naive Bayes": (GaussianNB(), True, {}),
    # scikit-learn 1.9 deprecates SVC(probability=True); calibrating the SVM gives the class probabilities.
    "Support Vector Machine": (
        CalibratedClassifierCV(SVC(random_state=config.SEED), ensemble=False),
        True,
        {"clf__estimator__C": [0.5, 1.0, 5.0]},
    ),
    "k-Nearest Neighbours": (
        KNeighborsClassifier(), True, {"clf__n_neighbors": [5, 11, 21], "clf__weights": ["uniform", "distance"]},
    ),
    "Majority-class baseline": (DummyClassifier(strategy="most_frequent"), False, {}),
}
PRIMARY = "Random Forest"


def make_pipeline(spec, name, features=None, **params):
    estimator, scale, _grid = CANDIDATES[name]
    pipeline = Pipeline([("prep", preprocessor(spec, scale, features)), ("clf", clone(estimator))])
    return pipeline.set_params(**params) if params else pipeline
