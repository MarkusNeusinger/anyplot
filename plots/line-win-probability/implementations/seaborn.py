""" pyplots.ai
line-win-probability: Win Probability Chart
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-20
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Seaborn theme and context for global styling
sns.set_theme(
    style="ticks",
    rc={
        "axes.facecolor": "#F7F9FC",
        "figure.facecolor": "#FFFFFF",
        "grid.color": "#D0D8E0",
        "grid.alpha": 0.3,
        "grid.linewidth": 0.6,
        "font.family": "sans-serif",
    },
)
sns.set_context("talk", font_scale=1.05, rc={"lines.linewidth": 2.8})

# Palette from seaborn
palette = sns.color_palette(["#306998", "#D4583B"])
home_color = palette[0]
away_color = palette[1]

# Data
np.random.seed(42)

plays = np.arange(0, 121)
win_prob = np.full(len(plays), 0.50)

events = {
    8: ("FG Home", 0.07),
    22: ("TD Away", -0.15),
    35: ("TD Home", 0.18),
    48: ("INT Home", 0.10),
    55: ("FG Away", -0.08),
    65: ("TD Home", 0.16),
    78: ("TD Away", -0.14),
    85: ("FG Home", 0.09),
    95: ("TD Away", -0.20),
    105: ("TD Home", 0.22),
    115: ("FG Home", 0.08),
}

for i in range(1, len(plays)):
    noise = np.random.normal(0, 0.015)
    if i in events:
        shift = events[i][1]
    else:
        shift = 0
    win_prob[i] = np.clip(win_prob[i - 1] + shift + noise, 0.02, 0.98)

win_prob[-1] = 0.95

df = pd.DataFrame({"play": plays, "win_probability": win_prob})

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

sns.lineplot(data=df, x="play", y="win_probability", color=home_color, linewidth=2.8, ax=ax)

ax.fill_between(plays, win_prob, 0.5, where=(win_prob >= 0.5), color=home_color, alpha=0.2, interpolate=True)
ax.fill_between(plays, win_prob, 0.5, where=(win_prob < 0.5), color=away_color, alpha=0.2, interpolate=True)

ax.axhline(y=0.5, color="#888888", linewidth=1.2, linestyle="--", alpha=0.5)

key_events = {
    22: ("TD Away\n7-3", away_color),
    35: ("TD Home\n10-7", home_color),
    65: ("TD Home\n20-14", home_color),
    95: ("TD Away\n23-27", away_color),
    105: ("TD Home\n30-27", home_color),
}

annotation_offsets = {22: (-8, 0.10), 35: (0, -0.10), 65: (8, 0.10), 95: (-12, 0.10), 105: (0, -0.12)}

for play_num, (label, color) in key_events.items():
    y_val = win_prob[play_num]
    x_off, y_off = annotation_offsets[play_num]
    ax.annotate(
        label,
        xy=(play_num, y_val),
        xytext=(play_num + x_off, y_val + y_off),
        fontsize=13,
        fontweight="bold",
        color=color,
        ha="center",
        va="center",
        arrowprops={"arrowstyle": "->", "color": color, "lw": 1.5, "connectionstyle": "arc3,rad=0.1"},
    )

sns.scatterplot(
    x=list(key_events),
    y=[win_prob[p] for p in key_events],
    color=[key_events[p][1] for p in key_events],
    s=100,
    zorder=5,
    edgecolor="white",
    linewidth=1.5,
    ax=ax,
    legend=False,
)

# Quarter markers
for q, label in [(30, "Q1"), (60, "Q2"), (90, "Q3"), (120, "Q4")]:
    ax.axvline(x=q, color="#C0C8D0", linewidth=0.8, linestyle=":", alpha=0.6)
    ax.text(q - 15, 0.025, label, fontsize=14, color="#8899AA", ha="center", fontweight="medium")

# Style
ax.set_xlabel("Play Number", fontsize=20)
ax.set_ylabel("Home Win Probability", fontsize=20)
ax.set_title("line-win-probability · seaborn · pyplots.ai\n", fontsize=24, fontweight="medium", pad=4)
ax.text(
    0.5,
    1.02,
    "NFL Game — Home vs Away  |  Lead changes and momentum shifts across 120 plays",
    transform=ax.transAxes,
    ha="center",
    fontsize=14,
    color="#667788",
    fontstyle="italic",
)
ax.tick_params(axis="both", labelsize=16)

ax.set_ylim(0, 1)
ax.set_xlim(0, 120)
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])

sns.despine(ax=ax)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.6)

home_patch = mpatches.Patch(color=home_color, alpha=0.4, label="Home")
away_patch = mpatches.Patch(color=away_color, alpha=0.4, label="Away")
ax.legend(handles=[home_patch, away_patch], fontsize=16, loc="upper left", frameon=False)

ax.text(
    118,
    0.015,
    "Final: Home 30 – Away 27",
    fontsize=15,
    ha="right",
    color="#556677",
    fontweight="semibold",
    fontstyle="italic",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "#E8EEF4", "edgecolor": "#C0C8D0", "alpha": 0.8},
)

# Save
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
