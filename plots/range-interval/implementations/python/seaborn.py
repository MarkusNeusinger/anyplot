""" anyplot.ai
range-interval: Range Interval Chart
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-22
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette, canonical order — first series is always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

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
    },
)

# Constants
JOB_TITLE = "Job Title"  # role: category
MIN_SALARY = "Min Salary (thousands USD)"  # role: min_value
MAX_SALARY = "Max Salary (thousands USD)"  # role: max_value

# Data: salary ranges by job title in the tech industry (thousands USD)
df = pd.DataFrame(
    {
        JOB_TITLE: [
            "Junior Developer",
            "Senior Developer",
            "DevOps Engineer",
            "Data Scientist",
            "Product Manager",
            "UX Designer",
            "QA Engineer",
            "Engineering Manager",
        ],
        MIN_SALARY: [65, 95, 85, 75, 80, 70, 60, 100],
        MAX_SALARY: [95, 160, 140, 130, 150, 120, 100, 180],
    }
)

# Plot
POSITION = "Position"
df[POSITION] = range(len(df))
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

# Range bars floating between the minimum and maximum of each category
ax.vlines(
    df[POSITION],
    df[MIN_SALARY],
    df[MAX_SALARY],
    color=IMPRINT_PALETTE[0],
    linewidth=7,
    alpha=0.85,
    capstyle="round",
    zorder=2,
)

# Markers exactly on the two bounds
sns.scatterplot(
    data=df,
    x=POSITION,
    y=MIN_SALARY,
    color=IMPRINT_PALETTE[0],
    s=80,
    edgecolor=PAGE_BG,
    linewidth=1,
    ax=ax,
    zorder=3,
    legend=False,
)
sns.scatterplot(
    data=df,
    x=POSITION,
    y=MAX_SALARY,
    color=IMPRINT_PALETTE[1],
    s=80,
    edgecolor=PAGE_BG,
    linewidth=1,
    ax=ax,
    zorder=3,
    legend=False,
)

ax.set_xticks(df[POSITION])
ax.set_xticklabels(df[JOB_TITLE], rotation=30, ha="right")
ax.set_xlabel(JOB_TITLE, fontsize=10)
ax.set_ylabel("Annual Salary (thousands USD)", fontsize=10)
ax.set_title("range-interval · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium")
ax.tick_params(axis="both", labelsize=8)

sns.despine(ax=ax)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
