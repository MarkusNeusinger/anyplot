"""pyplots.ai
scatter-pitch-events: Soccer Pitch Event Map
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-20
"""

import matplotlib.patches as patches
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgba


# Data
np.random.seed(42)

n_passes = 70
n_shots = 25
n_tackles = 40
n_interceptions = 35

pass_x = np.random.uniform(10, 95, n_passes)
pass_y = np.random.uniform(5, 63, n_passes)
pass_dx = np.random.uniform(-15, 25, n_passes)
pass_dy = np.random.uniform(-15, 15, n_passes)
pass_end_x = np.clip(pass_x + pass_dx, 0, 105)
pass_end_y = np.clip(pass_y + pass_dy, 0, 68)
pass_success = np.random.choice([True, False], n_passes, p=[0.78, 0.22])

shot_x = np.random.uniform(70, 104, n_shots)
shot_y = np.random.uniform(15, 53, n_shots)
shot_dx = np.clip(105 - shot_x, 1, 35) * np.random.uniform(0.5, 1.0, n_shots)
shot_dy = (34 - shot_y) * np.random.uniform(-0.3, 0.3, n_shots)
shot_success = np.random.choice([True, False], n_shots, p=[0.35, 0.65])

tackle_x = np.random.uniform(5, 80, n_tackles)
tackle_y = np.random.uniform(5, 63, n_tackles)
tackle_success = np.random.choice([True, False], n_tackles, p=[0.65, 0.35])

intercept_x = np.random.uniform(15, 85, n_interceptions)
intercept_y = np.random.uniform(5, 63, n_interceptions)
intercept_success = np.random.choice([True, False], n_interceptions, p=[0.80, 0.20])

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
fig.set_facecolor("#1a1a2e")
ax.set_facecolor("#2d6a4f")

# Pitch outline and markings
pitch_color = "#e0e0e0"
lw = 2.0

ax.add_patch(patches.Rectangle((0, 0), 105, 68, linewidth=lw, edgecolor=pitch_color, facecolor="none"))
ax.plot([52.5, 52.5], [0, 68], color=pitch_color, linewidth=lw)
ax.add_patch(patches.Circle((52.5, 34), 9.15, linewidth=lw, edgecolor=pitch_color, facecolor="none"))
ax.plot(52.5, 34, "o", color=pitch_color, markersize=4)

# Left penalty area
ax.add_patch(patches.Rectangle((0, 13.84), 16.5, 40.32, linewidth=lw, edgecolor=pitch_color, facecolor="none"))
ax.add_patch(patches.Rectangle((0, 24.84), 5.5, 18.32, linewidth=lw, edgecolor=pitch_color, facecolor="none"))
ax.plot(11, 34, "o", color=pitch_color, markersize=4)
ax.add_patch(patches.Arc((11, 34), 18.3, 18.3, angle=0, theta1=-53, theta2=53, color=pitch_color, linewidth=lw))

# Right penalty area
ax.add_patch(patches.Rectangle((88.5, 13.84), 16.5, 40.32, linewidth=lw, edgecolor=pitch_color, facecolor="none"))
ax.add_patch(patches.Rectangle((99.5, 24.84), 5.5, 18.32, linewidth=lw, edgecolor=pitch_color, facecolor="none"))
ax.plot(94, 34, "o", color=pitch_color, markersize=4)
ax.add_patch(patches.Arc((94, 34), 18.3, 18.3, angle=0, theta1=127, theta2=233, color=pitch_color, linewidth=lw))

# Corner arcs
for cx, cy in [(0, 0), (0, 68), (105, 0), (105, 68)]:
    t1 = 0 if cx == 0 and cy == 0 else (270 if cx == 105 and cy == 0 else (90 if cx == 0 and cy == 68 else 180))
    ax.add_patch(patches.Arc((cx, cy), 2, 2, angle=0, theta1=t1, theta2=t1 + 90, color=pitch_color, linewidth=lw))

# Goals
ax.plot([0, 0], [30.34, 37.66], color="#ffffff", linewidth=4, solid_capstyle="round")
ax.plot([105, 105], [30.34, 37.66], color="#ffffff", linewidth=4, solid_capstyle="round")

# Attacking zone highlight (right third) — focal point for tactical storytelling
zone_highlight = patches.FancyBboxPatch(
    (70, 5), 33, 58, boxstyle="round,pad=2", facecolor="#ffaa00", alpha=0.06, edgecolor="none", zorder=1
)
ax.add_patch(zone_highlight)
ax.text(
    86.5,
    66,
    "Attacking Third",
    fontsize=18,
    color="#ffcc44",
    alpha=0.7,
    ha="center",
    va="top",
    fontweight="bold",
    path_effects=[pe.withStroke(linewidth=2, foreground="#1a1a2e")],
)

# Color palette (colorblind-safe: blue, magenta, gold, orange)
c_pass = "#48bfe3"
c_shot = "#f72585"
c_tackle = "#ffd166"
c_intercept = "#7b2d8e"

# Events - passes (arrows with origin markers)
for i in range(n_passes):
    alpha = 0.7 if pass_success[i] else 0.35
    ax.annotate(
        "",
        xy=(pass_end_x[i], pass_end_y[i]),
        xytext=(pass_x[i], pass_y[i]),
        arrowprops={"arrowstyle": "->", "color": c_pass, "lw": 1.2, "alpha": alpha},
    )
    ax.plot(
        pass_x[i], pass_y[i], "o", color=c_pass, markersize=6, alpha=alpha, markeredgecolor="white", markeredgewidth=0.4
    )

# Events - shots (arrows with star markers)
for i in range(n_shots):
    alpha = 0.9 if shot_success[i] else 0.3
    ax.annotate(
        "",
        xy=(shot_x[i] + shot_dx[i], shot_y[i] + shot_dy[i]),
        xytext=(shot_x[i], shot_y[i]),
        arrowprops={"arrowstyle": "-|>", "color": c_shot, "lw": 2.0, "alpha": alpha, "mutation_scale": 15},
    )
    ax.plot(
        shot_x[i],
        shot_y[i],
        "*",
        color=c_shot,
        markersize=16,
        alpha=alpha,
        markeredgecolor="white",
        markeredgewidth=0.5,
        path_effects=[pe.withStroke(linewidth=1, foreground="#1a1a2e")],
    )

# Events - tackles (triangles) — RGBA colors for per-point alpha in single call
tackle_rgba = np.array([to_rgba(c_tackle, a) for a in np.where(tackle_success, 0.8, 0.25)])
ax.scatter(tackle_x, tackle_y, marker="^", s=180, c=tackle_rgba, edgecolors="white", linewidth=0.5, zorder=5)

# Events - interceptions (diamonds)
intercept_rgba = np.array([to_rgba(c_intercept, a) for a in np.where(intercept_success, 0.85, 0.35)])
ax.scatter(intercept_x, intercept_y, marker="D", s=140, c=intercept_rgba, edgecolors="white", linewidth=0.5, zorder=5)

# Style
ax.set_xlim(-3, 108)
ax.set_ylim(-5, 73)
ax.set_aspect("equal")
ax.axis("off")

ax.set_title(
    "scatter-pitch-events · matplotlib · pyplots.ai",
    fontsize=24,
    fontweight="medium",
    color="#e0e0e0",
    pad=15,
    path_effects=[pe.withStroke(linewidth=3, foreground="#1a1a2e")],
)

# Legend
legend_elements = [
    plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=c_pass, markersize=10, label="Pass", linestyle="None"),
    plt.Line2D([0], [0], marker="*", color="w", markerfacecolor=c_shot, markersize=14, label="Shot", linestyle="None"),
    plt.Line2D(
        [0], [0], marker="^", color="w", markerfacecolor=c_tackle, markersize=10, label="Tackle", linestyle="None"
    ),
    plt.Line2D(
        [0],
        [0],
        marker="D",
        color="w",
        markerfacecolor=c_intercept,
        markersize=10,
        label="Interception",
        linestyle="None",
    ),
    plt.Line2D(
        [0],
        [0],
        marker="s",
        color="w",
        markerfacecolor="#aaaaaa",
        markersize=10,
        label="Successful (bright)",
        linestyle="None",
    ),
    plt.Line2D(
        [0],
        [0],
        marker="s",
        color="w",
        markerfacecolor="#555555",
        markersize=10,
        label="Unsuccessful (faded)",
        linestyle="None",
    ),
]
ax.legend(
    handles=legend_elements,
    loc="lower center",
    ncol=6,
    fontsize=16,
    framealpha=0.7,
    facecolor="#1a1a2e",
    edgecolor="#444444",
    labelcolor="#e0e0e0",
    bbox_to_anchor=(0.5, -0.04),
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
