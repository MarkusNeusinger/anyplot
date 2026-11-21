""" anyplot.ai
box-horizontal: Horizontal Box Plot
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-21
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: first series is always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
COURSE = "Course"  # role: categories
SCORE = "Final exam score (points)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
rng = np.random.default_rng(42)
course_profiles = {
    # course: (mean, std, students)
    "Introduction to Organic Chemistry": (68, 12, 90),
    "Linear Algebra for Engineers": (72, 15, 85),
    "Principles of Macroeconomics": (76, 9, 95),
    "Modern European History": (81, 8, 80),
    "Advanced Statistical Methods": (64, 17, 70),
    "Creative Writing Workshop": (86, 6, 60),
}
df = pd.concat(
    [
        pd.DataFrame({COURSE: course, SCORE: np.clip(rng.normal(mean, std, n), 0, 100).round(1)})
        for course, (mean, std, n) in course_profiles.items()
    ],
    ignore_index=True,
)

# Plot: reads only df and the constants above
course_order = df.groupby(COURSE)[SCORE].median().sort_values().index.tolist()

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
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

sns.boxplot(
    data=df,
    x=SCORE,
    y=COURSE,
    order=course_order,
    color=IMPRINT_PALETTE[0],
    linewidth=1.2,
    width=0.6,
    boxprops={"edgecolor": INK_SOFT},
    whiskerprops={"color": INK_SOFT},
    capprops={"color": INK_SOFT},
    medianprops={"color": INK, "linewidth": 2.2},
    flierprops={"marker": "o", "markersize": 4, "markerfacecolor": IMPRINT_PALETTE[0], "markeredgecolor": INK_SOFT},
    ax=ax,
)

ax.set_title("box-horizontal · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(SCORE, fontsize=10, color=INK)
ax.set_ylabel(COURSE, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

sns.despine(ax=ax)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

ax.xaxis.grid(True, alpha=0.10, linewidth=0.6, color=INK)
ax.yaxis.grid(False)

fig.subplots_adjust(left=0.30, right=0.97, top=0.91, bottom=0.14)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
