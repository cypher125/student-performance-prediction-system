"""One look for every report figure.

Colours, ink and mark sizes follow the validated data-viz reference palette
(light mode, since the figures are printed in the project report).
"""
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.patches import PathPatch  # noqa: E402
from matplotlib.path import Path  # noqa: E402

from . import config  # noqa: E402

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
# Categorical slots 1-4, validated as a set. Slots 3-4 sit below 3:1 contrast, so charts
# using them always carry visible labels and a CSV table twin.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
DIVERGING = LinearSegmentedColormap.from_list(
    "blue_grey_red", ["#184f95", "#6da7ec", "#f0efec", "#ee8a89", "#b8302f"])
SEQUENTIAL = LinearSegmentedColormap.from_list(
    "blue_ramp", ["#f4f8fd", "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
# Polarity of a SHAP contribution: towards the class (warm) or away from it (cool).
TOWARD, AWAY = "#e34948", "#2a78d6"

DPI = 200
CSS_PX = DPI / 96  # device pixels per CSS pixel, so mark specs keep their screen size
BAR_MAX_PX = 24 * CSS_PX
RADIUS_PX = 4 * CSS_PX


def apply():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
        "font.size": 9.5,
        "axes.titlesize": 11,
        "axes.titleweight": "semibold",
        "axes.titlelocation": "left",
        "axes.titlecolor": INK,
        "axes.labelcolor": INK_SECONDARY,
        "axes.edgecolor": AXIS,
        "axes.linewidth": 0.8,
        "axes.facecolor": SURFACE,
        "figure.facecolor": SURFACE,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelcolor": INK_SECONDARY,
        "ytick.labelcolor": INK_SECONDARY,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "grid.linestyle": "-",
        "legend.frameon": False,
        "figure.dpi": DPI,
        "savefig.dpi": DPI,
    })


def style_axes(ax, grid="y"):
    """Recessive chrome: baseline only, hairline grid behind the data."""
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    if grid != "x":
        ax.spines["left"].set_visible(False)
    ax.tick_params(length=0, pad=4)
    if grid:
        ax.grid(axis=grid, zorder=0)
    ax.set_axisbelow(True)


def rounded_bars(ax, xs, heights, color=SERIES[0], max_width=0.6):
    """Columns from a zero baseline with 4px rounded data-ends, capped at 24px thick.

    Set the axis limits before calling: the rounding is computed in pixels.
    """
    ax.figure.canvas.draw()
    origin = ax.transData.transform((0, 0))
    unit = ax.transData.transform((1, 1))
    px_x, px_y = unit[0] - origin[0], unit[1] - origin[1]
    width = min(max_width, BAR_MAX_PX / px_x)
    for x, h in zip(xs, heights):
        if h <= 0:
            continue
        rx = min(RADIUS_PX / px_x, width / 2)
        ry = min(RADIUS_PX / px_y, h)
        x0, x1 = x - width / 2, x + width / 2
        verts = [(x0, 0), (x0, h - ry), (x0, h), (x0 + rx, h), (x1 - rx, h), (x1, h),
                 (x1, h - ry), (x1, 0), (x0, 0)]
        codes = [Path.MOVETO, Path.LINETO, Path.CURVE3, Path.CURVE3, Path.LINETO, Path.CURVE3,
                 Path.CURVE3, Path.LINETO, Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), facecolor=color, edgecolor="none", zorder=2))
    return width


def rounded_hbars(ax, ys, lengths, color=SERIES[0], max_height=0.6):
    """Horizontal bars from zero with 4px rounded data-ends (either sign), capped at 24px thick.

    Set the axis limits before calling: the rounding is computed in pixels.
    """
    ax.figure.canvas.draw()
    origin = ax.transData.transform((0, 0))
    unit = ax.transData.transform((1, 1))
    px_x, px_y = unit[0] - origin[0], abs(unit[1] - origin[1])
    height = min(max_height, BAR_MAX_PX / px_y)
    colors = color if isinstance(color, (list, tuple)) else [color] * len(ys)
    for y, length, c in zip(ys, lengths, colors):
        if length == 0:
            continue
        sign = 1 if length > 0 else -1
        rx = min(RADIUS_PX / px_x, abs(length))
        ry = min(RADIUS_PX / px_y, height / 2)
        y0, y1, end = y - height / 2, y + height / 2, length
        inner = end - sign * rx
        verts = [(0, y0), (inner, y0), (end, y0), (end, y0 + ry), (end, y1 - ry), (end, y1),
                 (inner, y1), (0, y1), (0, y0)]
        codes = [Path.MOVETO, Path.LINETO, Path.CURVE3, Path.CURVE3, Path.LINETO, Path.CURVE3,
                 Path.CURVE3, Path.LINETO, Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), facecolor=c, edgecolor="none", zorder=2))
    return height


def save(fig, name):
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = config.FIGURES_DIR / f"{name}.png"
    fig.savefig(path, bbox_inches="tight", pad_inches=0.15, facecolor=SURFACE)
    plt.close(fig)
    return path
