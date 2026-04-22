""" pyplots.ai
funnel-meta-analysis: Meta-Analysis Funnel Plot for Publication Bias
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-15
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D


# Seaborn theme and context — use seaborn's palette system for cohesive colors
funnel_palette = sns.light_palette("#306998", n_colors=6, as_cmap=False)
sns.set_theme(
    style="ticks", rc={"axes.grid": True, "grid.alpha": 0.12, "grid.linewidth": 0.6, "font.family": "sans-serif"}
)
sns.set_context("talk", font_scale=1.05, rc={"lines.linewidth": 2})

# Data
np.random.seed(42)

studies = [
    "Adams 2018",
    "Baker 2019",
    "Chen 2017",
    "Diaz 2020",
    "Evans 2016",
    "Fischer 2021",
    "Garcia 2019",
    "Hughes 2018",
    "Ibrahim 2020",
    "Jones 2017",
    "Kim 2021",
    "Lee 2019",
    "Martinez 2020",
    "Novak 2018",
    "O'Brien 2022",
]

n_studies = len(studies)
true_effect = -0.35

std_errors = np.concatenate(
    [np.random.uniform(0.05, 0.15, 5), np.random.uniform(0.15, 0.30, 6), np.random.uniform(0.30, 0.50, 4)]
)

effect_sizes = true_effect + np.random.normal(0, 1, n_studies) * std_errors
effect_sizes[-2] += 0.25
effect_sizes[-1] += 0.30

summary_effect = np.average(effect_sizes, weights=1 / std_errors**2)
weights = 1 / std_errors**2

df = pd.DataFrame({"effect_size": effect_sizes, "std_error": std_errors, "study": studies, "weight": weights})

# Classify studies by precision tier for seaborn hue-based styling
df["precision"] = pd.cut(
    df["std_error"], bins=[0, 0.15, 0.30, 1.0], labels=["High precision", "Moderate precision", "Low precision"]
)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

se_range = np.linspace(0, 0.55, 300)
ci_left = summary_effect - 1.96 * se_range
ci_right = summary_effect + 1.96 * se_range

ax.fill_betweenx(se_range, ci_left, ci_right, color=funnel_palette[1], alpha=0.25)
ax.plot(ci_left, se_range, color=funnel_palette[3], linewidth=1.5, linestyle="--", alpha=0.6)
ax.plot(ci_right, se_range, color=funnel_palette[3], linewidth=1.5, linestyle="--", alpha=0.6)

ax.axvline(x=summary_effect, color="#306998", linewidth=2.5, alpha=0.8, label=f"Summary effect ({summary_effect:.2f})")
ax.axvline(x=0, color="#888888", linewidth=1.5, linestyle=":", alpha=0.5, label="Null effect (0)")

# Use seaborn scatterplot with hue for precision tiers — distinctive seaborn feature
tier_palette = sns.color_palette([funnel_palette[5], funnel_palette[3], funnel_palette[2]])
sns.scatterplot(
    data=df,
    x="effect_size",
    y="std_error",
    hue="precision",
    size="weight",
    sizes=(120, 470),
    palette=tier_palette,
    edgecolor="white",
    linewidth=1.2,
    alpha=0.85,
    zorder=5,
    ax=ax,
    legend=False,
)

# Seaborn rugplot on x-axis to show effect size distribution — distinctive feature
sns.rugplot(data=df, x="effect_size", height=0.015, color="#306998", alpha=0.5, ax=ax)

# Annotate outlier studies (lower-right asymmetric points) to strengthen storytelling
outliers = df.nlargest(2, "std_error")
for _, row in outliers.iterrows():
    ax.annotate(
        row["study"],
        xy=(row["effect_size"], row["std_error"]),
        xytext=(12, -4),
        textcoords="offset points",
        fontsize=13,
        fontstyle="italic",
        color="#555555",
        alpha=0.9,
    )

# Style
ax.invert_yaxis()
ax.set_xlabel("Log Odds Ratio (Drug vs Placebo)", fontsize=20)
ax.set_ylabel("Standard Error", fontsize=20)
ax.set_title("funnel-meta-analysis · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=16)
ax.tick_params(axis="both", labelsize=16)

# Center the funnel by setting symmetric x-limits around the summary effect
x_margin = max(abs(df["effect_size"].min() - summary_effect), abs(df["effect_size"].max() - summary_effect)) * 1.5
ax.set_xlim(summary_effect - x_margin, summary_effect + x_margin)

sns.despine(ax=ax)

legend_elements = [
    Line2D([0], [0], color="#306998", linewidth=2.5, alpha=0.8, label=f"Summary effect ({summary_effect:.2f})"),
    Line2D([0], [0], color="#888888", linewidth=1.5, linestyle=":", alpha=0.5, label="Null effect (0)"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor=funnel_palette[5], markersize=10, label="High precision"),
    Line2D(
        [0], [0], marker="o", color="w", markerfacecolor=funnel_palette[3], markersize=9, label="Moderate precision"
    ),
    Line2D([0], [0], marker="o", color="w", markerfacecolor=funnel_palette[2], markersize=8, label="Low precision"),
]
ax.legend(handles=legend_elements, fontsize=14, frameon=False, loc="lower left")

# Save
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
