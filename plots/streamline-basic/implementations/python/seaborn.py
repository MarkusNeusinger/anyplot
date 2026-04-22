""" pyplots.ai
streamline-basic: Basic Streamline Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import FancyArrowPatch


# Set seed for reproducibility
np.random.seed(42)

# Vortex flow field: u = -y, v = x (creates circular streamlines)
# Velocity magnitude = distance from center

# Generate streamlines using Euler integration
streamlines_data = []
arrow_data = []  # Store arrow positions for flow direction indicators
streamline_id = 0

# Starting points at different radii - removed innermost radius to eliminate overlap artifacts
radii = [0.8, 1.2, 1.6, 2.0, 2.4, 2.8]
# Use fewer streamlines at inner radii to prevent crowding
n_per_radius_map = {0.8: 3, 1.2: 4, 1.6: 5, 2.0: 5, 2.4: 6, 2.8: 6}
dt = 0.03
max_steps = 250

for r in radii:
    n_per_radius = n_per_radius_map[r]
    for i in range(n_per_radius):
        angle = 2 * np.pi * i / n_per_radius + (r * 0.15)
        x = r * np.cos(angle)
        y = r * np.sin(angle)
        streamline_points = []

        # Trace streamline using Euler integration
        for step in range(max_steps):
            # Check bounds first
            if abs(x) > 3.2 or abs(y) > 3.2:
                break

            # Vector field: circular vortex (u = -y, v = x)
            u = -y
            v = x
            speed = np.sqrt(u**2 + v**2)

            if speed < 1e-6:
                break

            # Store point with velocity magnitude (= radius in vortex)
            vel_mag = np.sqrt(x**2 + y**2)
            streamlines_data.append(
                {
                    "x": float(x),
                    "y": float(y),
                    "streamline_id": streamline_id,
                    "order": step,
                    "velocity": float(vel_mag),
                }
            )
            streamline_points.append((x, y, u, v, vel_mag))

            # Normalize and step
            x = x + dt * u / speed
            y = y + dt * v / speed

        # Store arrow position at midpoint of each streamline
        if len(streamline_points) > 20:
            mid_idx = len(streamline_points) // 2
            px, py, pu, pv, pvel = streamline_points[mid_idx]
            arrow_data.append({"x": px, "y": py, "u": pu, "v": pv, "velocity": pvel, "radius": r})

        streamline_id += 1

# Create DataFrame
df = pd.DataFrame(streamlines_data)
arrows_df = pd.DataFrame(arrow_data)

# Compute average velocity per streamline for color encoding
avg_velocity = df.groupby("streamline_id")["velocity"].mean().reset_index()
avg_velocity.columns = ["streamline_id", "avg_velocity"]
df = df.merge(avg_velocity, on="streamline_id")

# Create velocity bins for categorical legend - seaborn-centric approach
velocity_bins = pd.qcut(df["avg_velocity"], q=6, duplicates="drop")
df["Speed Range"] = velocity_bins.apply(lambda x: f"{x.left:.1f}-{x.right:.1f} m/s")

# Set seaborn style with custom aesthetics
sns.set_theme(
    style="whitegrid", rc={"axes.labelsize": 20, "axes.titlesize": 24, "xtick.labelsize": 16, "ytick.labelsize": 16}
)
sns.set_context("talk", font_scale=1.2)

# Create square figure to better utilize canvas for equal aspect ratio plot
fig, ax = plt.subplots(figsize=(12, 12))

# Use seaborn color_palette to create viridis colors for continuous mapping
palette = sns.color_palette("viridis", as_cmap=True)
norm = plt.Normalize(df["avg_velocity"].min(), df["avg_velocity"].max())

# Plot streamlines using seaborn's lineplot with hue for velocity
# Each streamline is a separate unit, colored by average velocity
sns.lineplot(
    data=df,
    x="x",
    y="y",
    hue="avg_velocity",
    units="streamline_id",
    estimator=None,
    sort=False,
    linewidth=2.5,
    alpha=0.85,
    palette="viridis",
    legend=False,
    ax=ax,
)

# Add arrowheads to show flow direction
cmap = plt.cm.viridis
for _, arrow in arrows_df.iterrows():
    px, py = arrow["x"], arrow["y"]
    pu, pv = arrow["u"], arrow["v"]
    speed = np.sqrt(pu**2 + pv**2)
    # Normalize direction
    dx = 0.15 * pu / speed
    dy = 0.15 * pv / speed
    color = cmap(norm(arrow["velocity"]))
    arrow_patch = FancyArrowPatch(
        (px - dx / 2, py - dy / 2),
        (px + dx / 2, py + dy / 2),
        arrowstyle="->,head_width=4,head_length=4",
        color=color,
        linewidth=2,
        mutation_scale=1,
        zorder=10,
    )
    ax.add_patch(arrow_patch)

# Add colorbar manually (seaborn lineplot doesn't auto-create one for continuous hue)
sm = plt.cm.ScalarMappable(cmap="viridis", norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, shrink=0.8, aspect=20)
cbar.set_label("Flow Speed (m/s)", fontsize=20)
cbar.ax.tick_params(labelsize=16)

# Use seaborn despine for cleaner appearance
sns.despine(ax=ax, left=False, bottom=False)

# Styling with units explicitly in axis labels
ax.set(xlabel="X Position (m)", ylabel="Y Position (m)")
ax.set_title("streamline-basic · seaborn · pyplots.ai", fontsize=24, fontweight="bold")
ax.tick_params(axis="both", labelsize=16)
ax.set_aspect("equal")
ax.set_xlim(-3.5, 3.5)
ax.set_ylim(-3.5, 3.5)
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
