"""Train, tune, evaluate and explain the models, then save the web app's model.

Run from the backend folder:  python -m ml.train_models
On a 2-CPU laptop it takes about 40 minutes. It writes tables and figures to reports/
and replaces the deployed model in backend/artifacts/ (copy that folder first).

Design (3.2, 3.10): an 80/20 stratified split with a fixed seed; every algorithm is
tuned by 5-fold stratified cross-validation on the training part only (macro F1 is
the tuning score, so every class counts, not just the large Pass class); the test
part is used once, for the final comparison.
"""
import hashlib
import json
import sys
from datetime import date

import joblib
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_validate, train_test_split

from . import config, evaluation as ev, hypotheses, models, plotstyle as ps, risk, uci
from .explain import Explainer
from .models import CANDIDATES, PRIMARY

ARTIFACTS_DIR = config.BACKEND_DIR / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "model.joblib"
META_PATH = ARTIFACTS_DIR / "model_meta.json"
TEST_SIZE = 0.20
# Feature selection keeps the smallest set whose CV macro F1 is within this of the best.
SELECTION_TOLERANCE = 0.01
MODEL_VERSION = "1.0.0"


def _cv():
    return StratifiedKFold(5, shuffle=True, random_state=config.SEED)


def _save(df, name, index=False):
    config.TABLES_DIR.mkdir(parents=True, exist_ok=True)
    # utf-8-sig so Excel opens the tables with the right characters
    df.to_csv(config.TABLES_DIR / f"{name}.csv", index=index, encoding="utf-8-sig")


def _prefixed(params):
    return {f"clf__{k}": v for k, v in params.items()}


def compare_algorithms(spec, X_train, y_train, X_test, y_test):
    results = {}
    for name, (_estimator, _scale, grid) in CANDIDATES.items():
        search = GridSearchCV(models.make_pipeline(spec, name), grid, cv=_cv(), n_jobs=1,
                              scoring={"accuracy": "accuracy", "f1_macro": "f1_macro"}, refit="f1_macro")
        search.fit(X_train, y_train)
        best, i = search.best_estimator_, search.best_index_
        proba = ev.ordered_proba(best, X_test)
        pred = best.predict(X_test)
        results[name] = {
            "model": best, "pred": pred, "proba": proba,
            "params": {k.removeprefix("clf__"): v for k, v in search.best_params_.items()},
            "metrics": ev.classification_metrics(y_test, pred, proba),
            "cv_accuracy": [search.cv_results_[f"split{f}_test_accuracy"][i] for f in range(5)],
            "cv_f1_macro": [search.cv_results_[f"split{f}_test_f1_macro"][i] for f in range(5)],
        }
        m = results[name]["metrics"]
        print(f"    {name:26s} test accuracy {m['accuracy']:.3f}   macro F1 {m['f1_macro']:.3f}")
    return results


def comparison_table(results):
    rows = []
    for name, r in results.items():
        rows.append({
            "model": name,
            **{k: round(float(v), 3) for k, v in r["metrics"].items()},
            "cv_accuracy_mean": round(np.mean(r["cv_accuracy"]), 3),
            "cv_accuracy_sd": round(np.std(r["cv_accuracy"], ddof=1), 3),
            "cv_f1_macro_mean": round(np.mean(r["cv_f1_macro"]), 3),
            "cv_f1_macro_sd": round(np.std(r["cv_f1_macro"], ddof=1), 3),
            "tuned_settings": "; ".join(f"{k}={v}" for k, v in r["params"].items()) or "defaults",
        })
    return pd.DataFrame(rows).sort_values("f1_macro", ascending=False).reset_index(drop=True)


def feature_importance(spec, rf, X_test, y_test, shap_fail):
    features = spec.features
    prep, clf = rf.named_steps["prep"], rf.named_steps["clf"]
    impurity = dict.fromkeys(features, 0.0)
    for column, value in zip(prep.get_feature_names_out(), clf.feature_importances_):
        impurity[models.source_feature(column, features)] += float(value)
    perm = permutation_importance(rf, X_test, y_test, scoring="f1_macro", n_repeats=20,
                                  random_state=config.SEED, n_jobs=1)
    table = pd.DataFrame({
        "feature": features,
        "label": [spec.labels[f] for f in features],
        "impurity": [impurity[f] for f in features],
        "permutation_mean": perm.importances_mean,
        "permutation_std": perm.importances_std,
        "shap_fail": np.abs(shap_fail).mean(axis=0),
    })
    for column in ("impurity", "permutation_mean", "shap_fail"):
        table[f"rank_{column}"] = table[column].rank(ascending=False, method="min").astype(int)
    return table.sort_values("impurity", ascending=False).round(4).reset_index(drop=True)


def feature_selection(spec, params, ranking, X_train, y_train):
    """Add features in order of importance; keep the smallest set close to the best CV score."""
    rows = []
    for k in range(1, len(ranking) + 1):
        subset = ranking[:k]
        pipeline = models.make_pipeline(spec, PRIMARY, features=subset, **_prefixed(params))
        scores = cross_validate(pipeline, X_train[subset], y_train, cv=_cv(), scoring="f1_macro")["test_score"]
        rows.append({"n_features": k, "features": ", ".join(spec.labels[f] for f in subset),
                     "cv_f1_macro_mean": round(scores.mean(), 4), "cv_f1_macro_sd": round(scores.std(ddof=1), 4)})
    table = pd.DataFrame(rows)
    best = table["cv_f1_macro_mean"].max()
    chosen = int(table.loc[table["cv_f1_macro_mean"] >= best - SELECTION_TOLERANCE, "n_features"].iloc[0])
    table["selected"] = table["n_features"] == chosen
    return table, ranking[:chosen]


def run_experiment(spec, df, id_column, h01_columns, h01_labels):
    """Everything Chapter 4 needs for one dataset. Returns a summary for the model card."""
    prefix = spec.key
    print(f"\n== {spec.title} ({len(df):,} records) ==")
    X, y = df[spec.features], df[config.TARGET]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, stratify=y, random_state=config.SEED)
    print(f"  Split: {len(X_train):,} training / {len(X_test):,} test records")

    print("  Tuning and comparing algorithms (5-fold CV on the training part):")
    results = compare_algorithms(spec, X_train, y_train, X_test, y_test)
    comparison = comparison_table(results)
    _save(comparison, f"{prefix}_model_comparison")
    ev.plot_model_comparison(comparison, f"Algorithm comparison, {spec.title} (test set)",
                             f"{prefix}_model_comparison")

    rf = results[PRIMARY]
    _save(ev.per_class_report(y_test, rf["pred"]), f"{prefix}_rf_classification_report")
    cm = confusion_matrix(y_test, rf["pred"], labels=config.CLASSES)
    _save(pd.DataFrame(cm, index=[f"actual {c}" for c in config.CLASSES],
                       columns=[f"predicted {c}" for c in config.CLASSES]), f"{prefix}_rf_confusion_matrix", index=True)
    ev.plot_confusion(cm, f"Random Forest confusion matrix, {spec.title}", f"{prefix}_rf_confusion_matrix")
    _, auc_table = ev.plot_roc(y_test, rf["proba"], f"Random Forest ROC curves (one class against the rest), "
                               f"{spec.title}", f"{prefix}_rf_roc_curves")
    _save(auc_table, f"{prefix}_rf_roc_auc")
    _save(pd.DataFrame({"fold": range(1, 6), "accuracy": np.round(rf["cv_accuracy"], 4),
                        "f1_macro": np.round(rf["cv_f1_macro"], 4)}), f"{prefix}_rf_cv_folds")
    n_trees = rf["model"].named_steps["clf"].n_estimators
    _save(pd.DataFrame([{"setting": k, "value": v} for k, v in rf["params"].items()]
                       + [{"setting": "n_estimators", "value": n_trees}]), f"{prefix}_rf_tuned_settings")
    at_risk, levels = ev.at_risk_detection(y_test, rf["pred"], rf["proba"])
    _save(at_risk, f"{prefix}_rf_at_risk_detection")

    print("  Explaining the Random Forest with SHAP")
    explainer = Explainer(rf["model"], spec.features)
    fail_k = explainer.classes.index("Fail")
    shap_fail = explainer.contributions(X_test)[:, :, fail_k]
    importance = feature_importance(spec, rf["model"], X_test, y_test, shap_fail)
    _save(importance, f"{prefix}_feature_importance")
    ev.plot_importance(importance, spec.labels, f"Which factors matter most? {spec.title}",
                       f"{prefix}_feature_importance")
    ev.plot_shap_beeswarm(shap_fail, X_test, spec.features, spec.labels,
                          f"SHAP summary for the Fail class, {spec.title} (test set)", f"{prefix}_shap_fail_summary")

    fail_p = rf["proba"][:, ev.FAIL]
    candidates = np.where((y_test.to_numpy() == "Fail") & (levels == "High"))[0]
    if len(candidates):
        pick = candidates[np.argsort(fail_p[candidates])[len(candidates) // 2]]
        row = X_test.iloc[[pick]]
        student = df.loc[X_test.index[pick], id_column]
        items = explainer.explain_row(row, "Fail")
        header = (f"Student {student}: predicted {rf['pred'][pick]}, probability of Fail {fail_p[pick]:.2f}, "
                  f"risk {levels[pick]}; actual class {y_test.iloc[pick]}")
        ev.plot_explanation(items, spec.labels, header, f"Why this student was flagged, {spec.title}",
                            f"{prefix}_shap_example_student")
        _save(pd.DataFrame(items).assign(label=lambda d: d["feature"].map(spec.labels)),
              f"{prefix}_shap_example_student")

    print("  Feature selection")
    ranking = list(importance.sort_values("impurity", ascending=False)["feature"])
    selection, selected = feature_selection(spec, rf["params"], ranking, X_train, y_train)
    _save(selection, f"{prefix}_feature_selection")
    ev.plot_selection(selection, f"Feature selection by importance, {spec.title}", f"{prefix}_feature_selection")

    print("  Hypothesis tests")
    h01, h01_verdict = hypotheses.test_h01(df, *h01_columns, labels=h01_labels)
    _save(h01, f"{prefix}_h01_tests")
    quick_rf = models.make_pipeline(spec, PRIMARY, **_prefixed(rf["params"]), clf__n_estimators=100)
    correct = int((rf["pred"] == y_test.to_numpy()).sum())
    h02, h02_verdict = hypotheses.test_h02(quick_rf, X_train, y_train, correct, len(y_test),
                                           y_train.value_counts(normalize=True).max())
    _save(h02, f"{prefix}_h02_tests")
    print(f"    {h01_verdict}; {h02_verdict}")

    return {"X_train": X_train, "X_test": X_test, "y_train": y_train, "y_test": y_test, "results": results,
            "comparison": comparison, "importance": importance, "selection": selection, "selected": selected,
            "at_risk": at_risk, "h01": h01_verdict, "h02": h02_verdict}


def _rf_test_metrics(spec, params, features, X_train, y_train, X_test, y_test):
    model = models.make_pipeline(spec, PRIMARY, features=features, **_prefixed(params))
    model.fit(X_train[features], y_train)
    proba = ev.ordered_proba(model, X_test[features])
    pred = model.predict(X_test[features])
    return model, pred, proba, ev.classification_metrics(y_test, pred, proba)


def extra_experiments(sim_run, uci_run, sim_df):
    """Why exam scores are excluded, and how the UCI results hold up."""
    params = sim_run["results"][PRIMARY]["params"]
    leaky = models.DatasetSpec("sim_exam", "simulated YABATECH dataset", models.SIM.numeric + ("exam_score",),
                               models.SIM.categorical, {**models.SIM.labels, "exam_score": "Exam score (%)"})
    X_train = sim_df.loc[sim_run["X_train"].index, leaky.features]
    X_test = sim_df.loc[sim_run["X_test"].index, leaky.features]
    rows = [{"model": "Early-warning features only (used by the system)",
             **{k: round(float(v), 3) for k, v in sim_run["results"][PRIMARY]["metrics"].items()}}]
    *_, metrics = _rf_test_metrics(leaky, params, leaky.features, X_train, sim_run["y_train"], X_test, sim_run["y_test"])
    rows.append({"model": "Adding the exam score (only known after exams)", **{k: round(float(v), 3) for k, v in metrics.items()}})
    _save(pd.DataFrame(rows), "sim_exam_score_leakage_check")

    params = uci_run["results"][PRIMARY]["params"]
    por = uci.prepare(uci.load_raw("por"), "por")
    mid = models.DatasetSpec("uci_mid", "UCI", tuple(uci.MID_FEATURES), (), {})
    rows = [{"experiment": "Portuguese course, early features (first-period grade)",
             **{k: round(float(v), 3) for k, v in uci_run["results"][PRIMARY]["metrics"].items()}}]
    *_, metrics = _rf_test_metrics(mid, params, mid.features, por.loc[uci_run["X_train"].index, mid.features],
                                   uci_run["y_train"], por.loc[uci_run["X_test"].index, mid.features], uci_run["y_test"])
    rows.append({"experiment": "Portuguese course, adding the second-period grade", **{k: round(float(v), 3) for k, v in metrics.items()}})
    mat = uci.prepare(uci.load_raw("mat"), "mat")
    Xm, ym = mat[models.UCI.features], mat[config.TARGET]
    Xa, Xb, ya, yb = train_test_split(Xm, ym, test_size=TEST_SIZE, stratify=ym, random_state=config.SEED)
    *_, metrics = _rf_test_metrics(models.UCI, params, models.UCI.features, Xa, ya, Xb, yb)
    rows.append({"experiment": "Mathematics course (395 students), early features: robustness check",
                 **{k: round(float(v), 3) for k, v in metrics.items()}})
    _save(pd.DataFrame(rows), "uci_additional_experiments")


def save_app_model(sim_run, sim_df):
    """Refit the tuned Random Forest on all simulated records and save it for the web app."""
    params = sim_run["results"][PRIMARY]["params"]
    features = sim_run["selected"]
    _, _, _, test_metrics = _rf_test_metrics(models.SIM, params, features, sim_run["X_train"], sim_run["y_train"],
                                             sim_run["X_test"], sim_run["y_test"])
    model = models.make_pipeline(models.SIM, PRIMARY, features=features, **_prefixed(params))
    model.fit(sim_df[features], sim_df[config.TARGET])
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH, compress=3)
    data_bytes = config.SIM_CLEAN_CSV.read_bytes()
    meta = {
        "version": MODEL_VERSION,
        "algorithm": "Random Forest (scikit-learn)",
        "trained_on": date.today().isoformat(),
        "dataset": {"file": config.SIM_CLEAN_CSV.name, "records": len(sim_df),
                    "sha256": hashlib.sha256(data_bytes).hexdigest(), "kind": "simulated"},
        "features": features,
        "feature_labels": {f: models.SIM.labels[f] for f in features},
        "classes": config.CLASSES,
        "settings": {**{k: (v if v is None or isinstance(v, (int, float, str)) else str(v)) for k, v in params.items()},
                     "n_estimators": model.named_steps["clf"].n_estimators},
        "test_metrics": {k: round(float(v), 6) for k, v in test_metrics.items()},
        "evaluation_note": ("Metrics come from the 80/20 held-out test split; the saved model was then refit on all "
                            "records."),
        "risk_rule": {"high_if_fail_probability_at_least": risk.HIGH_RISK_PROBABILITY,
                      "medium_if_fail_probability_at_least": risk.MEDIUM_RISK_PROBABILITY,
                      "alert_levels": sorted(risk.ALERT_LEVELS)},
        "feature_importance": sim_run["importance"][["feature", "impurity", "permutation_mean", "shap_fail"]]
        .to_dict(orient="records"),
    }
    META_PATH.write_text(json.dumps(meta, indent=2))
    print(f"\nSaved the app model -> {MODEL_PATH.relative_to(config.PROJECT_DIR)} "
          f"({MODEL_PATH.stat().st_size / 1e6:.1f} MB), features: {', '.join(features)}")
    return meta


def _quick_mode():
    """Tiny grids, 50 trees and 5 permutations: checks the whole pipeline in a few minutes."""
    hypotheses.N_PERMUTATIONS = 5
    for name, (estimator, scale, grid) in list(CANDIDATES.items()):
        if hasattr(estimator, "n_estimators"):
            estimator.set_params(n_estimators=50)
        CANDIDATES[name] = (estimator, scale, {k: v[:1] for k, v in grid.items()})


def main():
    if "--quick" in sys.argv:
        _quick_mode()
        print("QUICK MODE: smoke test only, not the study's results")
    ps.apply()
    sim_df = pd.read_csv(config.SIM_CLEAN_CSV)
    uci_df = pd.read_csv(config.UCI_PREPARED_CSV["por"])

    uci_run = run_experiment(models.UCI, uci_df, "student_id", ("absences", "ca1_score", "final_score"),
                             {"absences": "absences", "ca1_score": "first-period grade",
                              "final_score": "final grade"})
    sim_run = run_experiment(models.SIM, sim_df, "student_code", ("attendance_pct", "ca_score", "gpa"),
                             {"attendance_pct": "attendance", "ca_score": "CA score", "gpa": "semester GPA"})
    extra_experiments(sim_run, uci_run, sim_df)
    save_app_model(sim_run, sim_df)
    print(f"Tables and figures written to {config.REPORTS_DIR.relative_to(config.PROJECT_DIR)}")


if __name__ == "__main__":
    main()
