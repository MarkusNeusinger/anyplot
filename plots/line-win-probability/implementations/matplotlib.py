"""pyplots.ai
line-win-probability: Win Probability Chart
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-20
"""

import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np


# Data - simulated NFL game: Eagles vs Cowboys
np.random.seed(42)

# Game plays (0 to ~120 plays)
n_plays = 120
plays = np.arange(n_plays + 1)

# Build win probability with realistic scoring events
win_prob = np.full(n_plays + 1, 0.50)

# Scoring events: (play_number, probability_shift, label)
scoring_events = [
    (8, 0.12, "PHI Field Goal (3-0)"),
    (22, -0.10, "DAL Touchdown (7-3)"),
    (35, 0.15, "PHI Touchdown (10-7)"),
    (48, 0.08, "PHI Field Goal (13-7)"),
    (58, -0.18, "DAL Touchdown (14-13)"),
    (72, 0.14, "PHI Touchdown (20-14)"),
    (85, -0.06, "DAL Field Goal (20-17)"),
    (95, 0.12, "PHI Touchdown (27-17)"),
    (110, -0.05, "DAL Field Goal (27-20)"),
]

# Generate smooth probability curve with scoring jumps
prob = 0.50
noise = np.random.normal(0, 0.012, n_plays + 1)
event_indices = {e[0]: (e[1], e[2]) for e in scoring_events}

for i in range(1, n_plays + 1):
    if i in event_indices:
        prob += event_indices[i][0]
    prob += noise[i]
    # Mean reversion toward current level
    prob = np.clip(prob, 0.02, 0.98)
    win_prob[i] = prob

# Force convergence to final outcome: Eagles win
for i in range(105, n_plays + 1):
    t = (i - 105) / (n_plays - 105)
    win_prob[i] = win_prob[105] * (1 - t**2) + 1.0 * t**2

# Quarter boundaries (roughly 30 plays each)
quarter_boundaries = [0, 30, 60, 90, n_plays]
quarter_labels = ["Q1", "Q2", "Q3", "Q4"]

# Colors
eagles_green = "#004C54"
cowboys_navy = "#003594"
baseline_color = "#444444"

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Fill above/below 50%
ax.fill_between(plays, win_prob, 0.5, where=(win_prob >= 0.5), color=eagles_green, alpha=0.3, interpolate=True)
ax.fill_between(plays, win_prob, 0.5, where=(win_prob < 0.5), color=cowboys_navy, alpha=0.45, interpolate=True)

# Win probability line - color changes based on which team leads
for i in range(len(plays) - 1):
    color = eagles_green if win_prob[i] >= 0.5 else cowboys_navy
    ax.plot(plays[i : i + 2], win_prob[i : i + 2], color=color, linewidth=3, zorder=3, solid_capstyle="round")

# 50% baseline
ax.axhline(y=0.5, color=baseline_color, linewidth=1.5, linestyle="--", alpha=0.5, zorder=2)

# Quarter dividers
for qb in quarter_boundaries[1:-1]:
    ax.axvline(x=qb, color="#999999", linewidth=1, linestyle=":", alpha=0.4)

# Quarter labels
for i, label in enumerate(quarter_labels):
    mid = (quarter_boundaries[i] + quarter_boundaries[i + 1]) / 2
    ax.text(mid, 0.03, label, ha="center", va="center", fontsize=16, color="#888888", fontweight="medium")

# Annotate key scoring events
annotation_events = [
    (8, "FG 3-0"),
    (22, "TD 7-3"),
    (35, "TD 10-7"),
    (58, "TD 14-13"),
    (72, "TD 20-14"),
    (95, "TD 27-17"),
]

for play_idx, label in annotation_events:
    wp = win_prob[play_idx]
    offset_y = 0.06 if wp >= 0.5 else -0.06
    txt = ax.annotate(
        label,
        xy=(play_idx, wp),
        xytext=(play_idx, wp + offset_y),
        fontsize=12,
        fontweight="bold",
        ha="center",
        va="center",
        color="#222222",
        arrowprops={"arrowstyle": "-", "color": "#999999", "linewidth": 0.8},
        zorder=4,
    )
    txt.set_path_effects([pe.withStroke(linewidth=3, foreground="white")])

# Scatter dots on scoring events for visibility
for play_idx, _ in annotation_events:
    ax.plot(
        play_idx,
        win_prob[play_idx],
        "o",
        color=eagles_green if win_prob[play_idx] >= 0.5 else cowboys_navy,
        markersize=7,
        zorder=5,
        markeredgecolor="white",
        markeredgewidth=1,
    )

# Style
ax.set_xlim(0, n_plays)
ax.set_ylim(0, 1)
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0%}"))

# Subtle y-axis gridlines for easier probability reading
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color="#888888")
ax.set_axisbelow(True)
ax.set_xlabel("Play Number", fontsize=20)
ax.set_ylabel("Win Probability", fontsize=20)
ax.set_title(
    "Eagles 27 – Cowboys 20 · line-win-probability · matplotlib · pyplots.ai", fontsize=24, fontweight="medium"
)
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Legend
eagles_patch = mpatches.Patch(color=eagles_green, alpha=0.4, label="Eagles")
cowboys_patch = mpatches.Patch(color=cowboys_navy, alpha=0.5, label="Cowboys")
ax.legend(handles=[eagles_patch, cowboys_patch], fontsize=16, loc="upper left", framealpha=0.8, edgecolor="none")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
