"""pyplots.ai
bar-diverging-likert: Likert Scale Diverging Bar Chart
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-03-04
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Data
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

np.random.seed(42)
raw = np.random.dirichlet(np.ones(5), size=len(questions)) * 100
strongly_disagree = raw[:, 0]
disagree = raw[:, 1]
neutral = raw[:, 2]
agree = raw[:, 3]
strongly_agree = raw[:, 4]

df = pd.DataFrame(
    {
        "question": questions,
        "Strongly Disagree": strongly_disagree,
        "Disagree": disagree,
        "Neutral": neutral,
        "Agree": agree,
        "Strongly Agree": strongly_agree,
    }
)

net_agreement = (df["Agree"] + df["Strongly Agree"]) - (df["Disagree"] + df["Strongly Disagree"])
df = df.iloc[net_agreement.argsort()].reset_index(drop=True)

# Compute bar positions diverging from center
half_neutral = df["Neutral"] / 2
left_disagree = -(df["Strongly Disagree"] + df["Disagree"] + half_neutral)
left_strongly_disagree = left_disagree
left_disagree_start = -(df["Disagree"] + half_neutral)
left_neutral_start = -half_neutral
right_neutral_end = half_neutral
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
    ax.barh(
        y_pos,
        widths,
        left=starts,
        height=bar_height,
        color=colors[label],
        edgecolor="white",
        linewidth=0.5,
        label=label,
    )

# Percentage labels inside segments
for i in range(len(df)):
    for label, starts, widths in categories_order:
        w = widths.iloc[i] if hasattr(widths, "iloc") else widths[i]
        s = starts.iloc[i] if hasattr(starts, "iloc") else starts[i]
        if w >= 7:
            cx = s + w / 2
            text_color = "white" if label in ("Strongly Disagree", "Strongly Agree") else "#333333"
            ax.text(cx, i, f"{w:.0f}%", ha="center", va="center", fontsize=12, fontweight="bold", color=text_color)

# Center line
ax.axvline(x=0, color="#555555", linewidth=1.2, zorder=3)

# Style
ax.set_yticks(y_pos)
ax.set_yticklabels(df["question"], fontsize=16)
ax.set_xlabel("Percentage of Responses (%)", fontsize=20)
ax.set_title("bar-diverging-likert · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="x", labelsize=16)
ax.tick_params(axis="y", length=0)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)

handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=5, fontsize=14, frameon=False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
