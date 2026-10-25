"""Describe both datasets: tables and figures for Chapter 4's data section (3.17).

Every figure has a CSV twin in reports/tables, so no value lives only in a picture.
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import to_rgba

from . import config, plotstyle as ps
from .cleaning import class_distribution, missing_value_summary

SIM_LABELS = {
    "attendance_pct": "Attendance (%)",
    "ca_score": "CA score (%)",
    "assignment_score": "Assignment score (%)",
    "exam_score": "Exam score (%)",
    "prior_gpa": "Previous GPA",
    "gpa": "Semester GPA",
}
UCI_LABELS = {
    "absences": "Absences",
    "ca1_score": "First-period grade (%)",
    "ca2_score": "Second-period grade (%)",
    "past_failures": "Past failures",
    "study_time": "Weekly study time (band 1-4)",
    "final_score": "Final grade (%)",
}


def descriptive_stats(df, labels):
    rows = []
    for column, label in labels.items():
        s = df[column].dropna()
        rows.append({
            "variable": label, "n": len(s), "mean": s.mean(), "sd": s.std(), "min": s.min(),
            "q1": s.quantile(0.25), "median": s.median(), "q3": s.quantile(0.75), "max": s.max(),
        })
    return pd.DataFrame(rows).round(2)


def records_by_level_session(df):
    table = pd.crosstab(df["level"], df["session"], margins=True, margins_name="Total")
    order = [lvl for lvl in config.LEVELS if lvl in table.index] + ["Total"]
    return table.reindex(order)


def _save_table(df, name, index=False):
    config.TABLES_DIR.mkdir(parents=True, exist_ok=True)
    path = config.TABLES_DIR / f"{name}.csv"
    df.to_csv(path, index=index, encoding="utf-8-sig")  # utf-8-sig so Excel reads it correctly
    return path


def plot_class_distribution(dist, title, name):
    fig, ax = plt.subplots(figsize=(6.2, 3.4))
    xs = np.arange(len(dist))
    counts = dist["records"].to_numpy()
    ax.set_xlim(-0.6, len(dist) - 0.4)
    ax.set_ylim(0, counts.max() * 1.18)
    ps.style_axes(ax)
    ps.rounded_bars(ax, xs, counts)
    for x, count, pct in zip(xs, counts, dist["percent"]):
        ax.annotate(f"{count:,} ({pct:g}%)", (x, count), xytext=(0, 4), textcoords="offset points",
                    ha="center", va="bottom", color=ps.INK_SECONDARY, fontsize=9)
    ax.set_xticks(xs, dist["performance_class"])
    ax.set_ylabel("Records")
    ax.set_title(title)
    return ps.save(fig, name)


def plot_histograms(df, labels, title, name, ncols=3):
    columns = list(labels)
    nrows = int(np.ceil(len(columns) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(3.1 * ncols, 2.5 * nrows))
    for ax, column in zip(np.ravel(axes), columns):
        values = df[column].dropna()
        if np.allclose(values, np.round(values)):
            # Whole-number data: align bins to the values so no bar straddles two of them.
            step = max(1, int(np.ceil((values.max() - values.min() + 1) / 20)))
            if values.nunique() > 1:
                step = max(step, int(np.gcd.reduce(np.diff(np.unique(values)).astype(int))))
            bins = np.arange(values.min() - step / 2, values.max() + step, step)
        else:
            bins = 20
        ax.hist(values, bins=bins, color=ps.SERIES[0], edgecolor=ps.SURFACE, linewidth=1.2, zorder=2)
        ps.style_axes(ax)
        ax.set_title(labels[column], fontsize=9.5, fontweight="normal", color=ps.INK_SECONDARY)
        ax.set_ylabel("Records" if ax in np.ravel(axes)[::ncols] else "")
    for ax in np.ravel(axes)[len(columns):]:
        ax.set_visible(False)
    fig.suptitle(title, x=0.01, ha="left", fontsize=11, fontweight="semibold", color=ps.INK)
    fig.tight_layout()
    return ps.save(fig, name)


def plot_by_class(df, labels, title, name, classes):
    columns = list(labels)
    fig, axes = plt.subplots(1, len(columns), figsize=(2.6 * len(columns), 3.2), sharey=False)
    for ax, column in zip(np.ravel(axes), columns):
        groups = [df.loc[df[config.TARGET] == c, column].dropna() for c in classes]
        box = ax.boxplot(groups, patch_artist=True, widths=0.45, showfliers=True,
                         medianprops={"color": ps.INK, "linewidth": 1.4},
                         whiskerprops={"color": ps.MUTED, "linewidth": 1},
                         capprops={"color": ps.MUTED, "linewidth": 1},
                         flierprops={"marker": "o", "markersize": 2.5, "markerfacecolor": ps.MUTED,
                                     "markeredgecolor": "none", "alpha": 0.5})
        for patch in box["boxes"]:
            patch.set_facecolor(to_rgba(ps.SERIES[0], 0.15))
            patch.set_edgecolor(ps.SERIES[0])
            patch.set_linewidth(1.4)
        ax.set_xticks(range(1, len(classes) + 1), [c[:4] + "." if len(c) > 6 else c for c in classes],
                      fontsize=8.5)
        ps.style_axes(ax)
        ax.set_title(labels[column], fontsize=9.5, fontweight="normal", color=ps.INK_SECONDARY)
    fig.suptitle(title, x=0.01, ha="left", fontsize=11, fontweight="semibold", color=ps.INK)
    fig.tight_layout()
    return ps.save(fig, name)


def plot_correlation(df, labels, title, name):
    corr = df[list(labels)].corr(method="pearson")
    n = len(labels)
    fig, ax = plt.subplots(figsize=(1.05 * n + 1.6, 0.95 * n + 0.8))
    image = ax.imshow(corr.to_numpy(), cmap=ps.DIVERGING, vmin=-1, vmax=1)
    for i in range(n):
        for j in range(n):
            r = corr.iat[i, j]
            ax.text(j, i, f"{r:.2f}", ha="center", va="center", fontsize=8.5,
                    color="white" if abs(r) >= 0.6 else ps.INK)
    names = [labels[c] for c in labels]
    ax.set_xticks(range(n), names, rotation=35, ha="right")
    ax.set_yticks(range(n), names)
    ax.set_xticks(np.arange(-0.5, n), minor=True)
    ax.set_yticks(np.arange(-0.5, n), minor=True)
    ax.grid(which="minor", color=ps.SURFACE, linewidth=2)
    ax.tick_params(which="both", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    bar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.03)
    bar.outline.set_visible(False)
    bar.ax.tick_params(length=0, labelcolor=ps.INK_SECONDARY)
    bar.set_label("Pearson correlation", color=ps.INK_SECONDARY)
    ax.set_title(title)
    return ps.save(fig, name), corr.round(3)


def run(sim, uci_por, cleaning_log):
    """Write every data-description table and figure; return the output paths."""
    ps.apply()
    out = {}
    n_sim, n_uci = len(sim), len(uci_por)

    out["sim_cleaning"] = _save_table(pd.DataFrame(cleaning_log), "sim_cleaning_steps")
    out["sim_missing"] = _save_table(missing_value_summary(sim), "sim_missing_values")
    out["sim_composition"] = _save_table(records_by_level_session(sim), "sim_records_by_level_session",
                                         index=True)
    out["sim_stats"] = _save_table(descriptive_stats(sim, SIM_LABELS), "sim_descriptive_stats")
    sim_dist = class_distribution(sim[config.TARGET])
    out["sim_classes"] = _save_table(sim_dist, "sim_class_distribution")
    out["fig_sim_classes"] = plot_class_distribution(
        sim_dist, f"Performance classes, simulated YABATECH dataset (n = {n_sim:,})", "sim_class_distribution")
    out["fig_sim_hist"] = plot_histograms(
        sim, SIM_LABELS, f"Distribution of each variable, simulated dataset (n = {n_sim:,})",
        "sim_variable_distributions")
    early = {k: SIM_LABELS[k] for k in config.EARLY_NUMERIC_FEATURES}
    out["fig_sim_by_class"] = plot_by_class(
        sim, early, "Early-semester variables by performance class, simulated dataset",
        "sim_variables_by_class", config.CLASSES)
    out["fig_sim_corr"], sim_corr = plot_correlation(
        sim, SIM_LABELS, "Correlations between variables, simulated dataset", "sim_correlations")
    out["sim_corr"] = _save_table(sim_corr, "sim_correlations", index=True)

    out["uci_stats"] = _save_table(descriptive_stats(uci_por, UCI_LABELS), "uci_descriptive_stats")
    uci_dist = class_distribution(uci_por[config.TARGET])
    out["uci_classes"] = _save_table(uci_dist, "uci_class_distribution")
    out["fig_uci_classes"] = plot_class_distribution(
        uci_dist, f"Performance classes, UCI Student Performance dataset (n = {n_uci:,})",
        "uci_class_distribution")
    out["fig_uci_hist"] = plot_histograms(
        uci_por, UCI_LABELS, f"Distribution of each variable, UCI dataset (n = {n_uci:,})",
        "uci_variable_distributions")
    uci_box = {k: UCI_LABELS[k] for k in ("absences", "ca1_score", "ca2_score")}
    out["fig_uci_by_class"] = plot_by_class(
        uci_por, uci_box, "Attendance and assessment by performance class, UCI dataset",
        "uci_variables_by_class", config.CLASSES)
    out["fig_uci_corr"], uci_corr = plot_correlation(
        uci_por, UCI_LABELS, "Correlations between variables, UCI dataset", "uci_correlations")
    out["uci_corr"] = _save_table(uci_corr, "uci_correlations", index=True)
    return out
