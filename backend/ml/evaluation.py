"""Metrics, tables and figures for the model experiments (3.17, 3.18)."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import Normalize
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support,
                             precision_score, recall_score, roc_auc_score, roc_curve)
from sklearn.preprocessing import label_binarize

from . import config, plotstyle as ps, risk

CLASSES = config.CLASSES
FAIL = CLASSES.index("Fail")


def ordered_proba(model, X):
    """Class probabilities with columns in the study's order (Distinction ... Fail)."""
    proba = model.predict_proba(X)
    order = [list(model.classes_).index(c) for c in CLASSES]
    return proba[:, order]


def classification_metrics(y_true, y_pred, proba):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    actual_fail, predicted_fail = y_true == "Fail", y_pred == "Fail"
    out = {"accuracy": accuracy_score(y_true, y_pred)}
    for avg in ("macro", "weighted"):
        out[f"precision_{avg}"] = precision_score(y_true, y_pred, labels=CLASSES, average=avg, zero_division=0)
        out[f"recall_{avg}"] = recall_score(y_true, y_pred, labels=CLASSES, average=avg, zero_division=0)
        out[f"f1_{avg}"] = f1_score(y_true, y_pred, labels=CLASSES, average=avg, zero_division=0)
    out["roc_auc_ovr_macro"] = roc_auc_score(label_binarize(y_true, classes=CLASSES), proba, average="macro")
    out["fail_precision"] = precision_score(actual_fail, predicted_fail, zero_division=0)
    out["fail_recall"] = recall_score(actual_fail, predicted_fail, zero_division=0)
    out["fail_roc_auc"] = roc_auc_score(actual_fail, proba[:, FAIL])
    return out


def per_class_report(y_true, y_pred):
    p, r, f, s = precision_recall_fscore_support(y_true, y_pred, labels=CLASSES, zero_division=0)
    return pd.DataFrame({"class": CLASSES, "precision": p, "recall": r, "f1": f, "support": s}).round(3)


def at_risk_detection(y_true, y_pred, proba):
    """How well the early-warning rule (ml/risk.py) catches the students who actually failed."""
    fail_p = proba[:, FAIL]
    levels = np.array([risk.risk_level(p, c) for p, c in zip(fail_p, y_pred)])
    actual = np.asarray(y_true) == "Fail"
    rows = []
    for rule, flagged in (("High risk only", levels == "High"),
                          ("High or Medium risk (alert raised)", np.isin(levels, list(risk.ALERT_LEVELS)))):
        caught = int((flagged & actual).sum())
        rows.append({
            "flag_rule": rule,
            "students_flagged": int(flagged.sum()),
            "share_flagged_pct": round(100 * flagged.mean(), 1),
            "failing_students_caught": caught,
            "failing_students_total": int(actual.sum()),
            "recall": round(caught / actual.sum(), 3) if actual.any() else np.nan,
            "precision": round(caught / flagged.sum(), 3) if flagged.any() else np.nan,
        })
    return pd.DataFrame(rows), levels


# ---------- figures ----------

def plot_model_comparison(table, title, name):
    """Test accuracy and macro-F1 for every algorithm, best at the top."""
    t = table.sort_values("f1_macro").reset_index(drop=True)
    n = len(t)
    fig, ax = plt.subplots(figsize=(7.2, 0.62 * n + 1.2))
    ax.set_xlim(0, 1.0)
    ax.set_ylim(-0.7, n - 0.3)
    ps.style_axes(ax, grid="x")
    ys = np.arange(n)
    offset = 0.17
    ps.rounded_hbars(ax, ys + offset, t["f1_macro"], color=ps.SERIES[0], max_height=0.3)
    ps.rounded_hbars(ax, ys - offset, t["accuracy"], color=ps.SERIES[1], max_height=0.3)
    for y, value in zip(ys, t["f1_macro"]):
        ax.annotate(f"{value:.2f}", (value, y + offset), xytext=(4, 0), textcoords="offset points",
                    va="center", fontsize=8.5, color=ps.INK_SECONDARY)
    ax.set_yticks(ys, t["model"])
    ax.set_xlabel("Score on the held-out test set (0 to 1)")
    handles = [plt.Line2D([], [], color=c, lw=6, solid_capstyle="round") for c in ps.SERIES[:2]]
    ax.legend(handles, ["Macro F1-score", "Accuracy"], loc="lower right", ncol=2, fontsize=8.5)
    ax.set_title(title)
    return ps.save(fig, name)


def plot_confusion(cm, title, name):
    fig, ax = plt.subplots(figsize=(5.4, 4.6))
    row_pct = cm / cm.sum(axis=1, keepdims=True).clip(min=1)
    ax.imshow(row_pct, cmap=ps.SEQUENTIAL, vmin=0, vmax=1)
    for i in range(len(CLASSES)):
        for j in range(len(CLASSES)):
            ax.text(j, i, f"{cm[i, j]}\n{100 * row_pct[i, j]:.0f}%", ha="center", va="center", fontsize=9,
                    color="white" if row_pct[i, j] >= 0.5 else ps.INK)
    ax.set_xticks(range(len(CLASSES)), CLASSES)
    ax.set_yticks(range(len(CLASSES)), CLASSES)
    ax.set_xlabel("Predicted class")
    ax.set_ylabel("Actual class")
    ax.set_xticks(np.arange(-0.5, len(CLASSES)), minor=True)
    ax.set_yticks(np.arange(-0.5, len(CLASSES)), minor=True)
    ax.grid(which="minor", color=ps.SURFACE, linewidth=2)
    ax.tick_params(which="both", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title(title)
    return ps.save(fig, name)


def plot_roc(y_true, proba, title, name):
    fig, ax = plt.subplots(figsize=(5.6, 4.8))
    ps.style_axes(ax, grid="both")
    ax.spines["left"].set_visible(True)
    ax.plot([0, 1], [0, 1], color=ps.AXIS, lw=1, zorder=1)
    rows = []
    for k, cls in enumerate(CLASSES):
        actual = np.asarray(y_true) == cls
        fpr, tpr, _ = roc_curve(actual, proba[:, k])
        auc = roc_auc_score(actual, proba[:, k])
        rows.append({"class": cls, "roc_auc": round(auc, 3)})
        ax.plot(fpr, tpr, color=ps.SERIES[k], lw=2, solid_capstyle="round", label=f"{cls} (AUC {auc:.2f})", zorder=3)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.01)
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.legend(loc="lower right", fontsize=8.5)
    ax.set_title(title)
    return ps.save(fig, name), pd.DataFrame(rows)


def plot_importance(importance, labels, title, name):
    """Three views of feature importance side by side, each sorted, one colour each."""
    panels = [("impurity", "Random Forest impurity importance"),
              ("permutation_mean", "Permutation importance (drop in macro F1)"),
              ("shap_fail", "Mean |SHAP| for the Fail class")]
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 0.5 * len(importance) + 1.6))
    for ax, (column, panel_title) in zip(axes, panels):
        t = importance.sort_values(column).reset_index(drop=True)
        ys = np.arange(len(t))
        top = max(t[column].max(), 1e-9)
        ax.set_xlim(0, top * 1.28)
        ax.set_ylim(-0.6, len(t) - 0.4)
        ps.style_axes(ax, grid="x")
        ps.rounded_hbars(ax, ys, t[column].clip(lower=0), color=ps.SERIES[0])
        if column == "permutation_mean":
            ax.errorbar(t[column].clip(lower=0), ys, xerr=t["permutation_std"], fmt="none",
                        ecolor=ps.MUTED, elinewidth=1, capsize=2, zorder=3)
        reach = t[column].clip(lower=0) + (t["permutation_std"] if column == "permutation_mean" else 0)
        for y, value, end in zip(ys, t[column], reach):
            ax.annotate(f"{value:.3f}", (end, y), xytext=(6, 0), textcoords="offset points",
                        va="center", fontsize=8, color=ps.INK_SECONDARY)
        ax.set_yticks(ys, [labels[f] for f in t["feature"]])
        ax.set_title(panel_title, fontsize=9.5, fontweight="normal", color=ps.INK_SECONDARY)
    fig.suptitle(title, x=0.01, ha="left", fontsize=11, fontweight="semibold", color=ps.INK)
    fig.tight_layout()
    return ps.save(fig, name)


def plot_selection(selection, title, name):
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    ps.style_axes(ax)
    k = selection["n_features"]
    mean, sd = selection["cv_f1_macro_mean"], selection["cv_f1_macro_sd"]
    ax.fill_between(k, mean - sd, mean + sd, color=ps.SERIES[0], alpha=0.10, linewidth=0, zorder=1)
    ax.plot(k, mean, color=ps.SERIES[0], lw=2, marker="o", markersize=6, markeredgecolor=ps.SURFACE,
            markeredgewidth=2, zorder=3)
    chosen = selection[selection["selected"]].iloc[0]
    ax.annotate(f"Selected: {int(chosen['n_features'])} features ({chosen['cv_f1_macro_mean']:.3f})",
                (chosen["n_features"], chosen["cv_f1_macro_mean"]), xytext=(0, 12),
                textcoords="offset points", ha="center", fontsize=8.5, color=ps.INK_SECONDARY)
    ax.set_xticks(k)
    ax.set_xlabel("Number of features used (most important first)")
    ax.set_ylabel("Cross-validated macro F1")
    ax.set_title(title)
    return ps.save(fig, name)


def plot_shap_beeswarm(contrib, X, features, labels, title, name, seed=config.SEED):
    """Each dot is one test student: SHAP effect on P(Fail), shaded by the feature's value."""
    rng = np.random.default_rng(seed)
    order = np.argsort(np.abs(contrib).mean(axis=0))
    fig, ax = plt.subplots(figsize=(7.2, 0.62 * len(features) + 1.4))
    ps.style_axes(ax, grid="x")
    ax.axvline(0, color=ps.AXIS, lw=1, zorder=1)
    for row, j in enumerate(order):
        feature = features[j]
        raw = X[feature]
        values = pd.to_numeric(raw, errors="coerce") if feature != "level" else raw.map(
            {lvl: i for i, lvl in enumerate(config.LEVELS)})
        values = values.astype(float)
        norm = Normalize(np.nanmin(values), np.nanmax(values) if np.nanmax(values) > np.nanmin(values) else np.nanmin(values) + 1)
        colors = [ps.MUTED if np.isnan(v) else ps.SEQUENTIAL(0.15 + 0.85 * norm(v)) for v in values]
        jitter = rng.uniform(-0.28, 0.28, len(values))
        ax.scatter(contrib[:, j], row + jitter, c=colors, s=14, linewidths=0.4, edgecolors=ps.SURFACE, zorder=2)
    ax.set_yticks(range(len(order)), [labels[features[j]] for j in order])
    ax.set_xlabel("SHAP value: effect on the probability of Fail")
    sm = plt.cm.ScalarMappable(cmap=ps.SEQUENTIAL, norm=Normalize(0, 1))
    bar = fig.colorbar(sm, ax=ax, fraction=0.04, pad=0.02, ticks=[0, 1])
    bar.ax.set_yticklabels(["Low", "High"])
    bar.outline.set_visible(False)
    bar.ax.tick_params(length=0, labelcolor=ps.INK_SECONDARY)
    bar.set_label("Feature value", color=ps.INK_SECONDARY)
    ax.set_title(title)
    return ps.save(fig, name)


def plot_explanation(items, labels, header, title, name):
    """One student's explanation: bars push the probability of Fail up (red) or down (blue)."""
    items = list(reversed(items))  # largest effect at the top
    contributions = np.array([i["contribution"] for i in items])
    fig, ax = plt.subplots(figsize=(7.2, 0.55 * len(items) + 1.5))
    span = max(np.abs(contributions).max(), 1e-6) * 1.45
    ax.set_xlim(-span, span)
    ax.set_ylim(-0.6, len(items) - 0.4)
    ps.style_axes(ax, grid="x")
    ax.axvline(0, color=ps.AXIS, lw=1, zorder=1)
    colors = [ps.TOWARD if c > 0 else ps.AWAY for c in contributions]
    ps.rounded_hbars(ax, np.arange(len(items)), contributions, color=colors)
    for y, item in enumerate(items):
        c = item["contribution"]
        ax.annotate(f"{c:+.3f}", (c, y), xytext=(6 if c >= 0 else -6, 0), textcoords="offset points",
                    ha="left" if c >= 0 else "right", va="center", fontsize=8.5, color=ps.INK_SECONDARY)
    ticks = []
    for item in items:
        value = item["value"]
        if value is None:
            shown = "missing"
        elif isinstance(value, (int, float)):
            shown = f"{value:.2f}" if "gpa" in item["feature"] else f"{value:g}"
        else:
            shown = value
        ticks.append(f"{labels[item['feature']]} = {shown}")
    ax.set_yticks(range(len(items)), ticks)
    ax.set_xlabel("Effect on the probability of Fail (red raises it, blue lowers it)")
    fig.suptitle(title, x=0.01, ha="left", fontsize=11, fontweight="semibold", color=ps.INK)
    ax.set_title(header, fontsize=9, fontweight="normal", color=ps.INK_SECONDARY)
    fig.tight_layout()
    return ps.save(fig, name)
