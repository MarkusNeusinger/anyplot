""" pyplots.ai
scatter-shot-chart: Basketball Shot Chart
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-20
"""

import matplotlib.patches as patches
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.path import Path


# Data
np.random.seed(42)

n_ft = 25
n_field = 325
n_shots = n_field + n_ft

# Field goal shot locations in feet relative to basket center at (0, 0)
x_field = np.concatenate(
    [
        np.random.normal(0, 3, 55),  # paint area shots
        np.random.normal(0, 1.5, 25),  # close to basket
        np.random.uniform(-8, 8, 50),  # mid-range middle
        np.random.normal(-15, 3, 35),  # left wing mid-range
        np.random.normal(15, 3, 35),  # right wing mid-range
        np.random.normal(-22, 1.5, 25),  # left corner three
        np.random.normal(22, 1.5, 25),  # right corner three
        np.random.normal(0, 8, 40),  # top of arc three
        np.random.normal(-12, 4, 18),  # left wing three
        np.random.normal(12, 4, 17),  # right wing three
    ]
)

y_field = np.concatenate(
    [
        np.random.uniform(0, 12, 55),  # paint
        np.random.uniform(0, 4, 25),  # close
        np.random.uniform(10, 18, 50),  # mid-range
        np.random.uniform(5, 15, 35),  # left wing mid
        np.random.uniform(5, 15, 35),  # right wing mid
        np.random.uniform(0, 8, 25),  # left corner
        np.random.uniform(0, 8, 25),  # right corner
        np.random.uniform(22, 30, 40),  # top of arc
        np.random.uniform(15, 25, 18),  # left wing three
        np.random.uniform(15, 25, 17),  # right wing three
    ]
)

# Free-throw shots clustered at the free-throw line (15 ft from backboard)
x_ft = np.random.normal(0, 0.8, n_ft)
y_ft = np.random.normal(14.0, 0.6, n_ft)

x = np.clip(np.concatenate([x_field, x_ft]), -24.5, 24.5)
y = np.clip(np.concatenate([y_field, y_ft]), 0, 40)

# Shot outcome — closer shots have higher make rate; free throws ~75%
distance = np.sqrt(x**2 + y**2)
make_prob = np.clip(0.65 - distance * 0.012, 0.25, 0.70)
# Free throws get a fixed ~75% make rate
make_prob[-n_ft:] = 0.75
made = np.random.random(n_shots) < make_prob

# Shot type based on distance from basket and free-throw designation
three_pt_dist = np.where(np.abs(x) >= 22, 22.0, 23.75)
shot_type = np.array(
    ["3-pointer" if d >= t else "2-pointer" for d, t in zip(distance, three_pt_dist, strict=False)], dtype=object
)
shot_type[-n_ft:] = "free-throw"

# Plot
fig, ax = plt.subplots(figsize=(12, 12))
fig.set_facecolor("#1a1a2e")
ax.set_facecolor("#2b2b40")

court_color = "#8899aa"
lw = 2.0

# Court geometry using PatchCollection for batch rendering
court_patches = [
    patches.Rectangle((-25, -5.25), 50, 47, linewidth=lw, edgecolor=court_color, facecolor="none"),
    patches.Circle((0, 0), 0.75, linewidth=lw, edgecolor="#ff6600", facecolor="none"),
    patches.Rectangle((-8, -5.25), 16, 19.25, linewidth=lw, edgecolor=court_color, facecolor="none"),
    patches.Arc((0, 14.0), 12, 12, angle=0, theta1=0, theta2=180, linewidth=lw, edgecolor=court_color),
    patches.Arc(
        (0, 14.0), 12, 12, angle=0, theta1=180, theta2=360, linewidth=lw, edgecolor=court_color, linestyle="--"
    ),
    patches.Arc((0, 0), 8, 8, angle=0, theta1=0, theta2=180, linewidth=lw, edgecolor=court_color),
    patches.Arc((0, 41.75), 12, 12, angle=0, theta1=180, theta2=360, linewidth=lw, edgecolor=court_color),
]
for p in court_patches:
    ax.add_patch(p)

# Backboard
ax.plot([-3, 3], [-1.0, -1.0], color=court_color, linewidth=3)

# Three-point line corners and arc
corner_y = 8.75
ax.plot([-22, -22], [-5.25, corner_y], color=court_color, linewidth=lw)
ax.plot([22, 22], [-5.25, corner_y], color=court_color, linewidth=lw)

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

# Subtle hexbin underlay showing shooting efficiency zones
zone_cmap = LinearSegmentedColormap.from_list("efficiency", ["#e76f51", "#3d3d55", "#2a9d8f"])
hb = ax.hexbin(
    x,
    y,
    C=made.astype(float),
    gridsize=15,
    cmap=zone_cmap,
    reduce_C_function=np.mean,
    alpha=0.12,
    extent=[-25, 25, -5, 42],
    mincnt=2,
    zorder=2,
    linewidths=0,
)

# Custom marker path for made shots (diamond shape — distinctive from default circle)
diamond_verts = [(-0.5, 0), (0, 0.7), (0.5, 0), (0, -0.7), (-0.5, 0)]
diamond_codes = [Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY]
diamond_marker = Path(diamond_verts, diamond_codes)

# Shot markers — colorblind-safe palette, sized for 350-point density
c_made = "#2a9d8f"
c_missed = "#e76f51"
c_ft = "#f4a261"

field_made = made & (shot_type != "free-throw")
field_missed = ~made & (shot_type != "free-throw")
ft_made = made & (shot_type == "free-throw")
ft_missed = ~made & (shot_type == "free-throw")

ax.scatter(
    x[field_missed], y[field_missed], s=45, marker="x", c=c_missed, alpha=0.45, linewidths=1.5, zorder=4, label="Missed"
)
ax.scatter(
    x[field_made],
    y[field_made],
    s=50,
    marker=diamond_marker,
    c=c_made,
    alpha=0.5,
    edgecolors="white",
    linewidth=0.4,
    zorder=5,
    label="Made",
)
# Free-throw shots with circle marker for visual distinction
ax.scatter(x[ft_missed], y[ft_missed], s=40, marker="x", c=c_missed, alpha=0.5, linewidths=1.5, zorder=4)
ax.scatter(
    x[ft_made],
    y[ft_made],
    s=45,
    marker="o",
    c=c_ft,
    alpha=0.6,
    edgecolors="white",
    linewidth=0.5,
    zorder=5,
    label="Free Throw",
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
    ncol=3,
    fontsize=18,
    framealpha=0.7,
    facecolor="#1a1a2e",
    edgecolor="#444444",
    labelcolor="#e0e0e0",
    bbox_to_anchor=(0.5, -0.03),
    markerscale=1.8,
    handletextpad=0.8,
)

# Shooting summary with zone breakdown
total = n_shots
makes = int(made.sum())
fg_pct = makes / total * 100
twos = shot_type == "2-pointer"
threes = shot_type == "3-pointer"
fts = shot_type == "free-throw"
fg2 = made[twos].sum() / twos.sum() * 100 if twos.sum() > 0 else 0
fg3 = made[threes].sum() / threes.sum() * 100 if threes.sum() > 0 else 0
ft_pct = made[fts].sum() / fts.sum() * 100 if fts.sum() > 0 else 0

summary = f"FG: {makes}/{total} ({fg_pct:.1f}%)  |  2PT: {fg2:.0f}%  |  3PT: {fg3:.0f}%  |  FT: {ft_pct:.0f}%"
ax.text(
    0,
    43.5,
    summary,
    fontsize=16,
    color="#cccccc",
    ha="center",
    va="top",
    path_effects=[pe.withStroke(linewidth=2, foreground="#1a1a2e")],
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
