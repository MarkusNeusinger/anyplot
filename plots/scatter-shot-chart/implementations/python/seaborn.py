"""anyplot.ai
scatter-shot-chart: Basketball Shot Chart
Library: seaborn 0.13.2 | Python 3.13.14
Quality: 83/100 | Created: 2026-06-21
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Arc


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — made shots: brand green (position 1); missed: semantic red anchor
COLOR_MADE = "#009E73"
COLOR_MISSED = "#AE3030"

COURT_COLOR = INK_SOFT

# NBA half-court geometry (feet, origin at basket center, y-positive toward half-court)
COURT_LEFT = -25.0
COURT_RIGHT = 25.0
COURT_BOTTOM = -5.25
COURT_TOP = 41.75

FT_LINE_Y = 13.75
FT_RADIUS = 6.0
RA_RADIUS = 4.0
THREE_RADIUS = 23.75
THREE_CORNER_X = 22.0
THREE_CORNER_Y = np.sqrt(THREE_RADIUS**2 - THREE_CORNER_X**2)

# Data — synthetic shot chart for a versatile NBA wing player
np.random.seed(42)

# At-rim attempts (0–3.5 ft): high make rate
n_rim = 80
rim_angles = np.random.uniform(0, np.pi, n_rim)
rim_dists = np.random.triangular(0.3, 1.5, 3.5, n_rim)
x_rim = rim_dists * np.cos(rim_angles)
y_rim = rim_dists * np.sin(rim_angles)
made_rim = np.random.random(n_rim) < 0.68

# Mid-range two-pointers (8–18 ft)
n_mid = 80
mid_angles = np.random.uniform(np.radians(8), np.radians(172), n_mid)
mid_dists = np.random.uniform(8, 18, n_mid)
x_mid = mid_dists * np.cos(mid_angles)
y_mid = mid_dists * np.sin(mid_angles)
made_mid = np.random.random(n_mid) < 0.42

# Three-point arc attempts (not corners)
n_arc3 = 120
arc3_angles = np.random.uniform(np.radians(28), np.radians(152), n_arc3)
arc3_dists = np.random.uniform(THREE_RADIUS, THREE_RADIUS + 3.5, n_arc3)
x_arc3 = np.clip(arc3_dists * np.cos(arc3_angles), COURT_LEFT + 0.5, COURT_RIGHT - 0.5)
y_arc3 = arc3_dists * np.sin(arc3_angles)
made_arc3 = np.random.random(n_arc3) < 0.36

# Corner three-pointers (both sides)
n_corner = 50
x_corner = np.concatenate(
    [np.random.uniform(22.5, 24.5, n_corner // 2), np.random.uniform(-24.5, -22.5, n_corner // 2)]
)
y_corner = np.random.uniform(-3.5, 6.0, n_corner)
made_corner = np.random.random(n_corner) < 0.40

x_all = np.concatenate([x_rim, x_mid, x_arc3, x_corner])
y_all = np.concatenate([y_rim, y_mid, y_arc3, y_corner])
made_all = np.concatenate([made_rim, made_mid, made_arc3, made_corner])

df = pd.DataFrame(
    {
        "x": x_all,
        "y": y_all,
        "Outcome": pd.Categorical(np.where(made_all, "Made", "Missed"), categories=["Made", "Missed"]),
    }
)

n_made = int(made_all.sum())
n_total = len(made_all)
fg_pct = n_made / n_total

# Plot — square canvas (2400 × 2400 px) matches the near-square half-court footprint
sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

fig, ax = plt.subplots(figsize=(6, 6), dpi=400)
ax.set_facecolor(PAGE_BG)

# Draw NBA half-court (standard 50 ft × 47 ft)
lw = 1.6

ax.add_patch(
    mpatches.Rectangle(
        (COURT_LEFT, COURT_BOTTOM), 50, 47, linewidth=lw, edgecolor=COURT_COLOR, facecolor="none", zorder=3
    )
)
ax.add_patch(
    mpatches.Rectangle((-8, COURT_BOTTOM), 16, 19, linewidth=lw, edgecolor=COURT_COLOR, facecolor="none", zorder=3)
)

# Free throw circle — upper arc solid, lower arc dashed
ax.add_patch(
    Arc(
        (0, FT_LINE_Y),
        2 * FT_RADIUS,
        2 * FT_RADIUS,
        angle=0,
        theta1=0,
        theta2=180,
        color=COURT_COLOR,
        linewidth=lw,
        zorder=3,
    )
)
ax.add_patch(
    Arc(
        (0, FT_LINE_Y),
        2 * FT_RADIUS,
        2 * FT_RADIUS,
        angle=0,
        theta1=180,
        theta2=360,
        color=COURT_COLOR,
        linewidth=lw,
        linestyle="--",
        zorder=3,
    )
)

# Restricted area arc
ax.add_patch(
    Arc((0, 0), 2 * RA_RADIUS, 2 * RA_RADIUS, angle=0, theta1=0, theta2=180, color=COURT_COLOR, linewidth=lw, zorder=3)
)

# Three-point line: arc + corner straight sections
theta1_three = np.degrees(np.arctan2(THREE_CORNER_Y, THREE_CORNER_X))
ax.add_patch(
    Arc(
        (0, 0),
        2 * THREE_RADIUS,
        2 * THREE_RADIUS,
        angle=0,
        theta1=theta1_three,
        theta2=180 - theta1_three,
        color=COURT_COLOR,
        linewidth=lw,
        zorder=3,
    )
)
ax.plot([THREE_CORNER_X, THREE_CORNER_X], [COURT_BOTTOM, THREE_CORNER_Y], color=COURT_COLOR, linewidth=lw, zorder=3)
ax.plot([-THREE_CORNER_X, -THREE_CORNER_X], [COURT_BOTTOM, THREE_CORNER_Y], color=COURT_COLOR, linewidth=lw, zorder=3)

# Backboard and basket
ax.plot([-3, 3], [-1.25, -1.25], color=COURT_COLOR, linewidth=lw * 1.5, zorder=3)
ax.add_patch(mpatches.Circle((0, 0), radius=0.75, linewidth=lw, edgecolor=COURT_COLOR, facecolor="none", zorder=3))

# KDE density fill — highlights made-shot hot zones (seaborn's signature statistical layer)
made_df = df[df["Outcome"] == "Made"]
sns.kdeplot(
    data=made_df, x="x", y="y", fill=True, levels=5, color=COLOR_MADE, alpha=0.09, bw_adjust=0.8, ax=ax, zorder=1
)
# KDE contour lines over the fill
sns.kdeplot(
    data=made_df,
    x="x",
    y="y",
    fill=False,
    levels=5,
    color=COLOR_MADE,
    alpha=0.38,
    linewidths=0.9,
    bw_adjust=0.8,
    ax=ax,
    zorder=2,
)

# Shot markers with dual encoding: hue (color) + style (shape) for CVD accessibility
palette = {"Made": COLOR_MADE, "Missed": COLOR_MISSED}
markers = {"Made": "o", "Missed": "X"}
sns.scatterplot(
    data=df,
    x="x",
    y="y",
    hue="Outcome",
    style="Outcome",
    markers=markers,
    palette=palette,
    s=40,
    alpha=0.55,
    edgecolors=PAGE_BG,
    linewidth=0.25,
    zorder=4,
    ax=ax,
)

# Style
ax.set_aspect("equal")
ax.set_xlim(COURT_LEFT - 0.8, COURT_RIGHT + 0.8)
ax.set_ylim(COURT_BOTTOM - 0.8, COURT_TOP + 0.8)
ax.set_xlabel("")
ax.set_ylabel("")
ax.tick_params(axis="both", which="both", bottom=False, left=False, labelbottom=False, labelleft=False)

for spine in ax.spines.values():
    spine.set_visible(False)

# Legend
legend = ax.legend(
    fontsize=9,
    title="Shot Outcome",
    title_fontsize=9,
    loc="upper right",
    markerscale=1.6,
    framealpha=0.9,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
)
legend.get_title().set_color(INK)
for text in legend.get_texts():
    text.set_color(INK_SOFT)

# Shooting stats — placed in the empty half-court area above the three-point arc
stats_text = f"{n_made}/{n_total} FGM\n{fg_pct:.1%} FG%"
ax.text(
    COURT_RIGHT - 2,
    COURT_TOP - 7,
    stats_text,
    ha="right",
    va="top",
    fontsize=8,
    color=INK_SOFT,
    zorder=5,
    bbox={"boxstyle": "round,pad=0.4", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.85},
)

title = "scatter-shot-chart · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=11, fontweight="medium", color=INK, pad=10)

fig.subplots_adjust(top=0.94, bottom=0.02, left=0.02, right=0.98)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
