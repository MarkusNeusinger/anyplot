"""anyplot.ai
scatter-marginal: Scatter Plot with Marginal Distributions
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1 — a single-series plot uses it alone

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
    },
)

# Columns: set these to your table's column names
STUDY_TIME = "Daily study time (min)"  # role: x
EXAM_SCORE = "Exam score (points)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("students.csv")
np.random.seed(42)
n_points = 200
study_time = np.random.randn(n_points) * 15 + 50
df = pd.DataFrame({STUDY_TIME: study_time, EXAM_SCORE: 0.7 * study_time + np.random.randn(n_points) * 10 + 20})

# Plot: reads only df and the constants above — square canvas, 6 in × 400 dpi → 2400 × 2400
g = sns.jointplot(
    data=df,
    x=STUDY_TIME,
    y=EXAM_SCORE,
    kind="scatter",
    height=6,
    ratio=5,
    space=0.15,
    color=BRAND,
    marginal_kws={"bins": 25, "kde": True, "alpha": 0.45, "edgecolor": PAGE_BG, "linewidth": 0.5},
    joint_kws={"s": 60, "alpha": 0.65, "edgecolor": PAGE_BG, "linewidth": 0.5},
)
g.figure.set_dpi(400)

# Style
g.ax_joint.set_xlabel(STUDY_TIME, fontsize=10, color=INK)
g.ax_joint.set_ylabel(EXAM_SCORE, fontsize=10, color=INK)
g.ax_joint.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
g.ax_joint.grid(True, linewidth=0.6)
for ax in (g.ax_marg_x, g.ax_marg_y):
    ax.tick_params(axis="both", labelsize=7, colors=INK_SOFT)
sns.despine(ax=g.ax_joint)

g.figure.suptitle("scatter-marginal · python · seaborn · anyplot.ai", fontsize=12, color=INK)
g.figure.subplots_adjust(left=0.12, right=0.97, bottom=0.1, top=0.93)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
