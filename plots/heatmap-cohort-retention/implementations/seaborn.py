"""pyplots.ai
heatmap-cohort-retention: Cohort Retention Heatmap
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-03-16
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data
np.random.seed(42)

cohort_labels = [
    "Jan 2024",
    "Feb 2024",
    "Mar 2024",
    "Apr 2024",
    "May 2024",
    "Jun 2024",
    "Jul 2024",
    "Aug 2024",
    "Sep 2024",
    "Oct 2024",
]
n_cohorts = len(cohort_labels)
n_periods = n_cohorts
cohort_sizes = np.random.randint(800, 2500, size=n_cohorts)

retention_data = np.full((n_cohorts, n_periods), np.nan)
for i in range(n_cohorts):
    max_periods = n_periods - i
    retention_data[i, 0] = 100.0
    base_decay = np.random.uniform(0.72, 0.85)
    for j in range(1, max_periods):
        prev = retention_data[i, j - 1]
        decay = base_decay + np.random.uniform(-0.03, 0.03)
        decay = min(decay, 0.98)
        retention_data[i, j] = round(prev * decay, 1)

period_labels = [f"Month {i}" for i in range(n_periods)]
df_heatmap = pd.DataFrame(retention_data, index=cohort_labels, columns=period_labels)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

mask = df_heatmap.isna()

sns.heatmap(
    df_heatmap,
    mask=mask,
    annot=True,
    fmt=".0f",
    cmap="YlGnBu",
    vmin=0,
    vmax=100,
    linewidths=2,
    linecolor="white",
    ax=ax,
    annot_kws={"fontsize": 13, "fontweight": "medium"},
    cbar_kws={"label": "Retention %", "shrink": 0.8},
    square=False,
)

# Style
y_labels = [f"{label}  (n={size:,})" for label, size in zip(cohort_labels, cohort_sizes, strict=True)]
ax.set_yticklabels(y_labels, rotation=0, fontsize=14)
ax.set_xticklabels(period_labels, rotation=0, fontsize=14)
ax.set_xlabel("Periods Since Signup", fontsize=20)
ax.set_ylabel("Signup Cohort", fontsize=20)
ax.set_title("heatmap-cohort-retention · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=20)

cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=14)
cbar.set_label("Retention %", fontsize=16)

ax.xaxis.tick_top()
ax.xaxis.set_label_position("top")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
