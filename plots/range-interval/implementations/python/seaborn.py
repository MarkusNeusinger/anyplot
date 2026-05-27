""" anyplot.ai
range-interval: Range Interval Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-18
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1 — ALWAYS first series
SECONDARY = "#C475FD"  # Okabe-Ito position 2

# Data - Salary ranges by job title in tech industry
np.random.seed(42)
job_titles = [
    "Junior Developer",
    "Senior Developer",
    "DevOps Engineer",
    "Data Scientist",
    "Product Manager",
    "UX Designer",
    "QA Engineer",
    "Engineering Manager",
]

# Realistic salary ranges (in thousands USD)
min_salaries = np.array([65, 95, 85, 75, 80, 70, 60, 100])
max_salaries = np.array([95, 160, 140, 130, 150, 120, 100, 180])

# Create DataFrame for plotting
df = pd.DataFrame(
    {"Job Title": job_titles, "Min Salary": min_salaries, "Max Salary": max_salaries, "idx": range(len(job_titles))}
)

# Create plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Draw vertical range bars connecting min and max salaries
for i, row in df.iterrows():
    ax.plot(
        [i, i],
        [row["Min Salary"], row["Max Salary"]],
        color=BRAND,
        linewidth=14,
        alpha=0.85,
        solid_capstyle="round",
        zorder=2,
    )

# Add min/max markers
sns.scatterplot(
    data=df, x="idx", y="Min Salary", color=BRAND, s=300, edgecolor=PAGE_BG, linewidth=2, ax=ax, zorder=3, legend=False
)

sns.scatterplot(
    data=df,
    x="idx",
    y="Max Salary",
    color=SECONDARY,
    s=300,
    edgecolor=PAGE_BG,
    linewidth=2,
    ax=ax,
    zorder=3,
    legend=False,
)

# Configure axes
ax.set_xticks(range(len(job_titles)))
ax.set_xticklabels(job_titles, rotation=45, ha="right")
ax.set_xlabel("Job Title", fontsize=20, color=INK)
ax.set_ylabel("Annual Salary (thousands USD)", fontsize=20, color=INK)
ax.set_title("range-interval · python · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Style spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(INK_SOFT)

# Grid styling
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
