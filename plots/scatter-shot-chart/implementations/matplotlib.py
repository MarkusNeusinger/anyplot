""" pyplots.ai
scatter-shot-chart: Basketball Shot Chart
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-20
"""

import matplotlib.patches as patches
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np


# Data
np.random.seed(42)

n_shots = 350

# Shot locations in feet relative to basket center at (0, 0)
# x: sideline (-25 to 25), y: baseline toward half-court (0 to ~42)
x = np.concatenate(
    [
        np.random.normal(0, 3, 60),  # paint area shots
        np.random.normal(0, 1.5, 30),  # close to basket
        np.random.uniform(-8, 8, 50),  # mid-range middle
        np.random.normal(-15, 3, 35),  # left wing mid-range
        np.random.normal(15, 3, 35),  # right wing mid-range
        np.random.normal(-22, 1.5, 30),  # left corner three
        np.random.normal(22, 1.5, 30),  # right corner three
        np.random.normal(0, 8, 40),  # top of arc three
        np.random.normal(-12, 4, 20),  # left wing three
        np.random.normal(12, 4, 20),  # right wing three
    ]
)

y = np.concatenate(
    [
        np.random.uniform(0, 12, 60),  # paint
        np.random.uniform(0, 4, 30),  # close
        np.random.uniform(10, 18, 50),  # mid-range
        np.random.uniform(5, 15, 35),  # left wing mid
        np.random.uniform(5, 15, 35),  # right wing mid
        np.random.uniform(0, 8, 30),  # left corner
        np.random.uniform(0, 8, 30),  # right corner
        np.random.uniform(22, 30, 40),  # top of arc
        np.random.uniform(15, 25, 20),  # left wing three
        np.random.uniform(15, 25, 20),  # right wing three
    ]
)

# Clip to court bounds
x = np.clip(x, -24.5, 24.5)
y = np.clip(y, 0, 40)

# Shot outcome — closer shots have higher make rate
distance = np.sqrt(x**2 + y**2)
make_prob = np.clip(0.65 - distance * 0.012, 0.25, 0.70)
made = np.random.random(n_shots) < make_prob

# Shot type based on distance from basket
three_pt_dist = np.where(np.abs(x) >= 22, 22.0, 23.75)
shot_type = np.where(distance >= three_pt_dist, "3-pointer", "2-pointer")

# Plot
fig, ax = plt.subplots(figsize=(12, 12))
fig.set_facecolor("#1a1a2e")
ax.set_facecolor("#2b2b40")

court_color = "#8899aa"
lw = 2.0

# Court outline (half-court)
ax.add_patch(patches.Rectangle((-25, -5.25), 50, 47, linewidth=lw, edgecolor=court_color, facecolor="none"))

# Basket and backboard
ax.add_patch(patches.Circle((0, 0), 0.75, linewidth=lw, edgecolor="#ff6600", facecolor="none"))
ax.plot([-3, 3], [-1.0, -1.0], color=court_color, linewidth=3)

# Paint / key area (16ft wide, from baseline to free-throw line)
paint_bottom = -5.25
paint_top = 14.0
ax.add_patch(
    patches.Rectangle(
        (-8, paint_bottom), 16, paint_top - paint_bottom, linewidth=lw, edgecolor=court_color, facecolor="none"
    )
)

# Free-throw circle (6ft radius)
ax.add_patch(patches.Arc((0, 14.0), 12, 12, angle=0, theta1=0, theta2=180, linewidth=lw, edgecolor=court_color))
ax.add_patch(
    patches.Arc((0, 14.0), 12, 12, angle=0, theta1=180, theta2=360, linewidth=lw, edgecolor=court_color, linestyle="--")
)

# Restricted area arc (4ft radius)
ax.add_patch(patches.Arc((0, 0), 8, 8, angle=0, theta1=0, theta2=180, linewidth=lw, edgecolor=court_color))

# Three-point line
# Corner straight portions (22ft from basket, extending 14ft from baseline)
corner_y = 8.75  # 14ft from baseline minus 5.25ft basket offset
ax.plot([-22, -22], [-5.25, corner_y], color=court_color, linewidth=lw)
ax.plot([22, 22], [-5.25, corner_y], color=court_color, linewidth=lw)

# Three-point arc (23.75ft radius from basket center)
three_arc_angle = np.degrees(np.arccos(22.0 / 23.75))
ax.add_patch(
    patches.Arc(
        (0, 0),
        47.5,
        47.5,
        angle=90,
        theta1=-90 + three_arc_angle,
        theta2=90 - three_arc_angle,
        linewidth=lw,
        edgecolor=court_color,
    )
)

# Half-court line
ax.plot([-25, 25], [41.75, 41.75], color=court_color, linewidth=lw)

# Half-court center circle (visible part)
ax.add_patch(patches.Arc((0, 41.75), 12, 12, angle=0, theta1=180, theta2=360, linewidth=lw, edgecolor=court_color))

# Shot markers — colorblind-safe palette
c_made = "#2a9d8f"  # teal green
c_missed = "#e76f51"  # coral orange

made_mask = made
missed_mask = ~made

ax.scatter(
    x[missed_mask], y[missed_mask], s=120, marker="x", c=c_missed, alpha=0.55, linewidths=2, zorder=4, label="Missed"
)
ax.scatter(
    x[made_mask],
    y[made_mask],
    s=150,
    marker="o",
    c=c_made,
    alpha=0.7,
    edgecolors="white",
    linewidth=0.5,
    zorder=5,
    label="Made",
)

# Style
ax.set_xlim(-27, 27)
ax.set_ylim(-7, 44)
ax.set_aspect("equal")
ax.axis("off")

ax.set_title(
    "scatter-shot-chart · matplotlib · pyplots.ai",
    fontsize=24,
    fontweight="medium",
    color="#e0e0e0",
    pad=15,
    path_effects=[pe.withStroke(linewidth=3, foreground="#1a1a2e")],
)

# Legend
legend = ax.legend(
    loc="lower center",
    ncol=2,
    fontsize=18,
    framealpha=0.7,
    facecolor="#1a1a2e",
    edgecolor="#444444",
    labelcolor="#e0e0e0",
    bbox_to_anchor=(0.5, -0.03),
    markerscale=1.5,
    handletextpad=0.8,
)

# Shooting summary text
total = n_shots
makes = made.sum()
fg_pct = makes / total * 100
ax.text(
    -24,
    43,
    f"FG: {makes}/{total} ({fg_pct:.1f}%)",
    fontsize=18,
    color="#cccccc",
    va="top",
    path_effects=[pe.withStroke(linewidth=2, foreground="#1a1a2e")],
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
