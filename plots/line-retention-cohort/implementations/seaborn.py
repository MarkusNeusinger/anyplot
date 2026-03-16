"""pyplots.ai
line-retention-cohort: User Retention Curve by Cohort
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-16
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data
np.random.seed(42)

cohorts = {"Jan 2025": 1245, "Feb 2025": 1380, "Mar 2025": 1510, "Apr 2025": 1420, "May 2025": 1605}

weeks = np.arange(0, 13)
records = []

decay_rates = [0.18, 0.16, 0.14, 0.12, 0.10]
floors = [8, 10, 14, 18, 22]

endpoint_values = {}

for (cohort_label, cohort_size), decay, floor in zip(cohorts.items(), decay_rates, floors, strict=True):
    retention = 100 * np.exp(-decay * weeks) + floor * (1 - np.exp(-0.3 * weeks))
    retention[0] = 100.0
    retention = np.clip(retention, 0, 100)
    noise = np.random.normal(0, 0.8, len(weeks))
    noise[0] = 0
    retention = np.clip(retention + noise, 0, 100)
    label = f"{cohort_label} (n={cohort_size:,})"
    endpoint_values[label] = retention[-1]
    for w, r in zip(weeks, retention, strict=True):
        records.append({"week": w, "retention": r, "cohort": label})

df = pd.DataFrame(records)

# Custom palette starting with Python Blue
palette = ["#306998", "#E8922A", "#3A9E78", "#D94F4F", "#8B6DB0"]

# Plot - use seaborn style, context, and hue-based grouping
sns.set_theme(
    style="whitegrid",
    font="sans-serif",
    rc={
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "grid.alpha": 0.12,
        "grid.linewidth": 0.6,
        "axes.grid.axis": "y",
        "axes.facecolor": "#FAFAFA",
        "figure.facecolor": "white",
        "font.family": "sans-serif",
    },
)
sns.set_context("talk", font_scale=1.1)

fig, ax = plt.subplots(figsize=(16, 9))

sns.lineplot(
    data=df,
    x="week",
    y="retention",
    hue="cohort",
    style="cohort",
    markers=True,
    dashes=False,
    palette=palette,
    linewidth=2.5,
    markersize=8,
    ax=ax,
)

# Progressive emphasis: older cohorts thinner/lighter, newer bolder
cohort_labels = df["cohort"].unique()
for i, line in enumerate(ax.lines[: len(cohort_labels)]):
    weight = 1.5 + i * 0.5
    line.set_linewidth(weight)
    line.set_markersize(5 + i * 1.5)
    line.set_alpha(0.45 + i * 0.13)

# 20% reference line
ax.axhline(y=20, color="#AAAAAA", linestyle="--", linewidth=1.0, alpha=0.6, zorder=1)
ax.text(12.3, 15, "20% target", fontsize=14, color="#999999", va="center", fontstyle="italic")

# Endpoint annotations for data storytelling
sorted_endpoints = sorted(endpoint_values.items(), key=lambda x: list(endpoint_values.keys()).index(x[0]))
placed_positions = []
for i, (_label, val) in enumerate(sorted_endpoints):
    color = palette[i]
    # Avoid overlap with other annotations by nudging
    pos = val
    for prev in placed_positions:
        if abs(pos - prev) < 4:
            pos = prev + 4 if pos >= prev else prev - 4
    placed_positions.append(pos)
    ax.annotate(
        f"{val:.0f}%",
        xy=(12, val),
        xytext=(12.6, pos),
        fontsize=13,
        fontweight="bold",
        color=color,
        va="center",
        ha="left",
    )

# Style
ax.set_title("line-retention-cohort · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=24, color="#333333")
ax.set_xlabel("Weeks Since Signup", fontsize=20, color="#555555", labelpad=12)
ax.set_ylabel("Retained Users (%)", fontsize=20, color="#555555", labelpad=12)
ax.tick_params(axis="both", labelsize=16, colors="#666666")

ax.set_xlim(-0.3, 13.5)
ax.set_ylim(0, 108)
ax.set_xticks(weeks)

# Use sns.despine for seaborn-idiomatic spine removal
sns.despine(ax=ax, left=True, bottom=False)

legend = ax.legend(
    fontsize=13,
    frameon=True,
    fancybox=True,
    framealpha=0.85,
    edgecolor="#DDDDDD",
    loc="upper right",
    title="Signup Cohort",
    title_fontsize=15,
)
legend.get_title().set_fontweight("semibold")
legend.get_frame().set_linewidth(0.5)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
