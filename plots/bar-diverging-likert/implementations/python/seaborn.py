""" pyplots.ai
bar-diverging-likert: Likert Scale Diverging Bar Chart
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-04
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

# Colorblind-safe diverging palette via seaborn's color_palette
palette = sns.color_palette("RdBu", n_colors=5)
# Override neutral to warm tan — clearly distinct from cool blue agree tones
palette[2] = (0.68, 0.65, 0.58)
sns.set_palette(palette)

category_keys = ["strongly_disagree", "disagree", "neutral", "agree", "strongly_agree"]
category_names = ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]
colors = dict(zip(category_keys, palette, strict=True))

# Compute cumulative values for diverging stacked layout via sns.barplot overlay
# Each layer is painted back-to-front: outermost color first, covered by inner layers
half_n = df["neutral"] / 2

# Right side cumulative
df["r_sa"] = half_n + df["agree"] + df["strongly_agree"]
df["r_a"] = half_n + df["agree"]
df["r_n"] = half_n

# Left side cumulative (negative values)
df["l_sd"] = -(half_n + df["disagree"] + df["strongly_disagree"])
df["l_d"] = -(half_n + df["disagree"])
df["l_n"] = -half_n

# Question order: most positive at top (seaborn plots first item at top)
q_order = df["question"].tolist()[::-1]

fig, ax = plt.subplots(figsize=(16, 9))
bar_kw = {
    "y": "question",
    "order": q_order,
    "orient": "h",
    "ax": ax,
    "width": 0.65,
    "edgecolor": "white",
    "linewidth": 0.5,
    "errorbar": None,
}

# Right side: outermost (strongly_agree) painted first, overlaid by inner layers
sns.barplot(data=df, x="r_sa", color=colors["strongly_agree"], **bar_kw)
sns.barplot(data=df, x="r_a", color=colors["agree"], **bar_kw)
sns.barplot(data=df, x="r_n", color=colors["neutral"], **bar_kw)

# Left side: outermost (strongly_disagree) painted first, overlaid by inner layers
sns.barplot(data=df, x="l_sd", color=colors["strongly_disagree"], **bar_kw)
sns.barplot(data=df, x="l_d", color=colors["disagree"], **bar_kw)
sns.barplot(data=df, x="l_n", color=colors["neutral"], **bar_kw)

# Percentage labels inside segments (only where width >= 10%)
for _, row in df.iterrows():
    hn = row["neutral"] / 2
    sd_left = -hn - row["disagree"] - row["strongly_disagree"]
    d_left = -hn - row["disagree"]
    a_left = hn
    sa_left = hn + row["agree"]

    segments = [
        (sd_left + row["strongly_disagree"] / 2, row["strongly_disagree"], "white"),
        (d_left + row["disagree"] / 2, row["disagree"], "#333333"),
        (0, row["neutral"], "#444444"),
        (a_left + row["agree"] / 2, row["agree"], "#333333"),
        (sa_left + row["strongly_agree"] / 2, row["strongly_agree"], "white"),
    ]
    y_pos = q_order.index(row["question"])
    for x_center, value, text_color in segments:
        if value >= 10:
            ax.text(
                x_center,
                y_pos,
                f"{value}%",
                ha="center",
                va="center",
                fontsize=14,
                fontweight="medium",
                color=text_color,
            )

# Axis styling
ax.set_ylabel("")
ax.set_xlabel("Percentage", fontsize=20, labelpad=10)
ax.set_title(
    "Employee Engagement Survey · bar-diverging-likert · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=20
)
ax.tick_params(axis="y", labelsize=16)
ax.tick_params(axis="x", labelsize=16)
ax.axvline(0, color="#333333", linewidth=1.0, zorder=3)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{abs(int(x))}%"))
ax.xaxis.grid(True, alpha=0.15, linewidth=0.8)
ax.yaxis.grid(False)
ax.set_axisbelow(True)

# Emphasize extreme questions for data storytelling
for i, label in enumerate(ax.get_yticklabels()):
    if i == 0 or i == len(q_order) - 1:
        label.set_fontweight("bold")

# Remove top/right spines using seaborn utility
sns.despine(ax=ax)

# Legend using palette colors
legend_handles = [Patch(facecolor=colors[k], label=n) for k, n in zip(category_keys, category_names, strict=True)]
ax.legend(handles=legend_handles, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=5, fontsize=14, frameon=False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
