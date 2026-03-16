"""pyplots.ai
line-retention-cohort: User Retention Curve by Cohort
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-16
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

for (cohort_label, cohort_size), decay, floor in zip(cohorts.items(), decay_rates, floors, strict=True):
    retention = 100 * np.exp(-decay * weeks) + floor * (1 - np.exp(-0.3 * weeks))
    retention[0] = 100.0
    retention = np.clip(retention, 0, 100)
    noise = np.random.normal(0, 0.8, len(weeks))
    noise[0] = 0
    retention = np.clip(retention + noise, 0, 100)
    for w, r in zip(weeks, retention, strict=True):
        records.append({"week": w, "retention": r, "cohort": f"{cohort_label} (n={cohort_size:,})"})

df = pd.DataFrame(records)

# Plot - use seaborn style, context, and hue-based grouping
sns.set_theme(
    style="whitegrid",
    rc={
        "axes.spines.top": False,
        "axes.spines.right": False,
        "grid.alpha": 0.15,
        "grid.linewidth": 0.8,
        "axes.grid.axis": "y",
    },
)
sns.set_context("talk", font_scale=1.1)

palette = sns.color_palette("colorblind", n_colors=5)

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

cohort_labels = df["cohort"].unique()
for i, line in enumerate(ax.lines[: len(cohort_labels)]):
    weight = 1.5 + i * 0.4
    line.set_linewidth(weight)
    line.set_markersize(5 + i * 1.5)
    line.set_alpha(0.5 + i * 0.12)

ax.axhline(y=20, color="#888888", linestyle="--", linewidth=1.2, alpha=0.5, zorder=1)
ax.text(12.3, 20, "20% target", fontsize=13, color="#888888", va="center", fontstyle="italic")

# Style
ax.set_title("line-retention-cohort · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=20)
ax.set_xlabel("Weeks Since Signup", fontsize=20)
ax.set_ylabel("Retained Users (%)", fontsize=20)
ax.tick_params(axis="both", labelsize=16)

ax.set_xlim(-0.3, 12.5)
ax.set_ylim(0, 105)
ax.set_xticks(weeks)

legend = ax.legend(fontsize=14, frameon=False, loc="upper right", title="Signup Cohort", title_fontsize=15)
legend.get_title().set_fontweight("semibold")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
