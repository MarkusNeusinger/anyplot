"""pyplots.ai
line-win-probability: Win Probability Chart
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-03-20
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


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

home_color = "#306998"
away_color = "#D4583B"

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

sns.lineplot(data=df, x="play", y="win_probability", color=home_color, linewidth=2.5, ax=ax)

ax.fill_between(plays, win_prob, 0.5, where=(win_prob >= 0.5), color=home_color, alpha=0.25, interpolate=True)
ax.fill_between(plays, win_prob, 0.5, where=(win_prob < 0.5), color=away_color, alpha=0.25, interpolate=True)

ax.axhline(y=0.5, color="#888888", linewidth=1.2, linestyle="--", alpha=0.6)

key_events = {
    22: ("TD Away\n7-3", away_color),
    35: ("TD Home\n10-7", home_color),
    65: ("TD Home\n20-14", home_color),
    95: ("TD Away\n23-27", away_color),
    105: ("TD Home\n30-27", home_color),
}

annotation_offsets = {22: (-5, 0.08), 35: (0, -0.08), 65: (0, -0.08), 95: (-5, 0.08), 105: (5, -0.08)}

for play_num, (label, color) in key_events.items():
    y_val = win_prob[play_num]
    x_off, y_off = annotation_offsets[play_num]
    ax.annotate(
        label,
        xy=(play_num, y_val),
        xytext=(play_num + x_off, y_val + y_off),
        fontsize=11,
        fontweight="bold",
        color=color,
        ha="center",
        va="center",
        arrowprops={"arrowstyle": "-", "color": color, "lw": 1.2},
    )

ax.scatter(
    list(key_events),
    [win_prob[p] for p in key_events],
    color=[key_events[p][1] for p in key_events],
    s=80,
    zorder=5,
    edgecolors="white",
    linewidth=1,
)

# Quarter markers
for q, label in [(30, "Q1"), (60, "Q2"), (90, "Q3"), (120, "Q4")]:
    ax.axvline(x=q, color="#cccccc", linewidth=0.8, linestyle=":", alpha=0.5)
    ax.text(q - 15, 0.03, label, fontsize=14, color="#999999", ha="center", fontweight="medium")

# Style
ax.set_xlabel("Play Number", fontsize=20)
ax.set_ylabel("Home Win Probability", fontsize=20)
ax.set_title("line-win-probability · seaborn · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)

ax.set_ylim(0, 1)
ax.set_xlim(0, 120)
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8)

home_patch = mpatches.Patch(color=home_color, alpha=0.4, label="Home")
away_patch = mpatches.Patch(color=away_color, alpha=0.4, label="Away")
ax.legend(handles=[home_patch, away_patch], fontsize=16, loc="upper left", frameon=False)

ax.text(118, -0.06, "Final: Home 30 – Away 27", fontsize=14, ha="right", color="#555555", fontstyle="italic")

# Save
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
