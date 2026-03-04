"""pyplots.ai
bar-diverging-likert: Likert Scale Diverging Bar Chart
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-04
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import seaborn as sns
from matplotlib.patches import Patch


# Configure seaborn theme and context for consistent styling
sns.set_style("white")
sns.set_context("talk", font_scale=1.1)

# Data - Employee engagement survey (8 questions, 5-point Likert scale)
# Includes mix of positive and negative net agreement for diverging contrast
questions = [
    "Career growth opportunities",
    "Work-life balance",
    "Team collaboration",
    "Management communication",
    "Compensation & benefits",
    "Job security",
    "Training & development",
    "Workplace culture",
]

survey_data = {
    "question": questions,
    "strongly_disagree": [5, 8, 3, 14, 20, 4, 10, 6],
    "disagree": [10, 14, 7, 22, 28, 8, 18, 12],
    "neutral": [15, 18, 12, 20, 17, 14, 16, 16],
    "agree": [40, 35, 45, 28, 22, 42, 32, 38],
    "strongly_agree": [30, 25, 33, 16, 13, 32, 24, 28],
}

df = pd.DataFrame(survey_data)

# Sort by net agreement (positive minus negative)
df["net_agreement"] = df["agree"] + df["strongly_agree"] - df["disagree"] - df["strongly_disagree"]
df = df.sort_values("net_agreement").reset_index(drop=True)

# Generate diverging color palette using seaborn's HSL-based interpolation
pal = list(sns.diverging_palette(10, 220, s=75, l=55, n=5))
pal[2] = (0.72, 0.72, 0.72)  # Visible neutral gray (center="light" is near-white)
category_keys = ["strongly_disagree", "disagree", "neutral", "agree", "strongly_agree"]
category_names = ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]
colors = dict(zip(category_keys, pal, strict=True))

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
bar_height = 0.65

for idx, row in df.iterrows():
    half_neutral = row["neutral"] / 2

    # Left side: strongly disagree, disagree, half neutral
    sd_left = -half_neutral - row["disagree"] - row["strongly_disagree"]
    ax.barh(
        idx,
        row["strongly_disagree"],
        left=sd_left,
        height=bar_height,
        color=colors["strongly_disagree"],
        edgecolor="white",
        linewidth=0.5,
    )

    d_left = -half_neutral - row["disagree"]
    ax.barh(
        idx, row["disagree"], left=d_left, height=bar_height, color=colors["disagree"], edgecolor="white", linewidth=0.5
    )

    ax.barh(
        idx,
        half_neutral,
        left=-half_neutral,
        height=bar_height,
        color=colors["neutral"],
        edgecolor="white",
        linewidth=0.5,
    )

    # Right side: half neutral, agree, strongly agree
    ax.barh(idx, half_neutral, left=0, height=bar_height, color=colors["neutral"], edgecolor="white", linewidth=0.5)

    a_left = half_neutral
    ax.barh(idx, row["agree"], left=a_left, height=bar_height, color=colors["agree"], edgecolor="white", linewidth=0.5)

    sa_left = half_neutral + row["agree"]
    ax.barh(
        idx,
        row["strongly_agree"],
        left=sa_left,
        height=bar_height,
        color=colors["strongly_agree"],
        edgecolor="white",
        linewidth=0.5,
    )

    # Percentage labels inside segments (only where width >= 10%)
    segments = [
        (sd_left + row["strongly_disagree"] / 2, row["strongly_disagree"], "white"),
        (d_left + row["disagree"] / 2, row["disagree"], "#333333"),
        (0, row["neutral"], "#555555"),
        (a_left + row["agree"] / 2, row["agree"], "#333333"),
        (sa_left + row["strongly_agree"] / 2, row["strongly_agree"], "white"),
    ]
    for x_center, value, text_color in segments:
        if value >= 10:
            ax.text(
                x_center, idx, f"{value}%", ha="center", va="center", fontsize=14, fontweight="medium", color=text_color
            )

# Axis styling
ax.set_yticks(range(len(df)))
ax.set_yticklabels(df["question"], fontsize=16)
ax.set_xlabel("Percentage", fontsize=20, labelpad=10)
ax.set_title(
    "Employee Engagement Survey · bar-diverging-likert · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=20
)
ax.tick_params(axis="x", labelsize=16)
ax.axvline(0, color="#333333", linewidth=1.0, zorder=3)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{abs(int(x))}%"))
ax.xaxis.grid(True, alpha=0.15, linewidth=0.8)
ax.yaxis.grid(False)
ax.set_axisbelow(True)

# Remove spines using seaborn's despine utility
sns.despine(ax=ax)

# Legend using seaborn-generated palette colors
legend_elements = [Patch(facecolor=colors[k], label=n) for k, n in zip(category_keys, category_names, strict=True)]
ax.legend(handles=legend_elements, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=5, fontsize=14, frameon=False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
