""" pyplots.ai
bar-diverging-likert: Likert Scale Diverging Bar Chart
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-04
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd


# Data — hand-crafted realistic employee engagement survey responses
questions = [
    "I feel valued at work",
    "Communication is transparent",
    "Leadership inspires confidence",
    "Work-life balance is respected",
    "Career growth opportunities exist",
    "Team collaboration is effective",
    "Resources are adequate",
    "Feedback is constructive",
    "Company culture is positive",
    "Compensation is fair",
]

data = {
    "question": questions,
    "Strongly Disagree": [4, 8, 18, 6, 12, 3, 2, 7, 5, 15],
    "Disagree": [10, 15, 25, 12, 20, 8, 6, 14, 11, 22],
    "Neutral": [16, 20, 18, 18, 22, 14, 12, 20, 15, 20],
    "Agree": [42, 35, 24, 38, 28, 45, 48, 36, 40, 28],
    "Strongly Agree": [28, 22, 15, 26, 18, 30, 32, 23, 29, 15],
}

df = pd.DataFrame(data)

# Sort by net agreement
net_agreement = (df["Agree"] + df["Strongly Agree"]) - (df["Disagree"] + df["Strongly Disagree"])
df = df.iloc[net_agreement.argsort()].reset_index(drop=True)

# Compute bar positions diverging from center
half_neutral = df["Neutral"] / 2
left_strongly_disagree = -(df["Strongly Disagree"] + df["Disagree"] + half_neutral)
left_disagree_start = -(df["Disagree"] + half_neutral)
left_neutral_start = -half_neutral
right_agree_start = half_neutral
right_strongly_agree_start = half_neutral + df["Agree"]

# Colors — diverging red-to-blue with muted neutral
colors = {
    "Strongly Disagree": "#c0392b",
    "Disagree": "#e77a6d",
    "Neutral": "#b0b0b0",
    "Agree": "#6dacde",
    "Strongly Agree": "#2471a3",
}

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
y_pos = np.arange(len(df))
bar_height = 0.7

categories_order = [
    ("Strongly Disagree", left_strongly_disagree, df["Strongly Disagree"]),
    ("Disagree", left_disagree_start, df["Disagree"]),
    ("Neutral", left_neutral_start, df["Neutral"]),
    ("Agree", right_agree_start, df["Agree"]),
    ("Strongly Agree", right_strongly_agree_start, df["Strongly Agree"]),
]

for label, starts, widths in categories_order:
    bars = ax.barh(
        y_pos,
        widths,
        left=starts,
        height=bar_height,
        color=colors[label],
        edgecolor="white",
        linewidth=0.8,
        label=label,
        zorder=2,
    )

# Percentage labels inside segments
for i in range(len(df)):
    for label, starts, widths in categories_order:
        w = widths.iloc[i] if hasattr(widths, "iloc") else widths[i]
        s = starts.iloc[i] if hasattr(starts, "iloc") else starts[i]
        if w >= 7:
            cx = s + w / 2
            text_color = "white" if label in ("Strongly Disagree", "Strongly Agree") else "#333333"
            ax.text(
                cx, i, f"{w:.0f}%", ha="center", va="center", fontsize=14, fontweight="bold", color=text_color, zorder=4
            )

# Center line
ax.axvline(x=0, color="#444444", linewidth=1.5, zorder=3)

# Subtle x-axis grid for easier percentage reading
ax.xaxis.grid(True, alpha=0.15, linewidth=0.8, color="#888888", zorder=0)
ax.set_axisbelow(True)

# Custom tick formatter showing percentage symbol
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:+.0f}%" if x != 0 else "0%"))
ax.xaxis.set_major_locator(mticker.MultipleLocator(20))

# Style
ax.set_yticks(y_pos)
ax.set_yticklabels(df["question"], fontsize=16)
ax.set_xlabel("Percentage of Responses", fontsize=20)
ax.set_title("bar-diverging-likert · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=20)
ax.tick_params(axis="x", labelsize=16)
ax.tick_params(axis="y", length=0)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)

# Add net agreement annotation on right side using ax.annotate
for i in range(len(df)):
    net = (df["Agree"].iloc[i] + df["Strongly Agree"].iloc[i]) - (
        df["Disagree"].iloc[i] + df["Strongly Disagree"].iloc[i]
    )
    sign = "+" if net > 0 else ""
    color = "#2471a3" if net > 0 else "#c0392b"
    ax.annotate(
        f"{sign}{net}",
        xy=(1.02, i),
        xycoords=("axes fraction", "data"),
        fontsize=14,
        fontweight="bold",
        color=color,
        va="center",
        ha="left",
        annotation_clip=False,
    )

# Net agreement header
ax.annotate(
    "Net",
    xy=(1.02, len(df) - 0.5),
    xycoords=("axes fraction", "data"),
    fontsize=14,
    fontweight="bold",
    color="#555555",
    va="center",
    ha="left",
    annotation_clip=False,
)

# Legend
handles, labels = ax.get_legend_handles_labels()
ax.legend(
    handles,
    labels,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.08),
    ncol=5,
    fontsize=16,
    frameon=False,
    handlelength=1.5,
    columnspacing=1.5,
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
