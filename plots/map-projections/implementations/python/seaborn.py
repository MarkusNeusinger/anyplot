""" pyplots.ai
map-projections: World Map with Different Projections
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-20
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


# Set seaborn theme
sns.set_theme(style="whitegrid", context="talk", font_scale=1.0)

# Simplified world coastline polygons (major continents outline)
# Coordinates in degrees (longitude, latitude)
coastlines_data = [
    # North America
    [
        (-168, 66),
        (-141, 70),
        (-130, 70),
        (-120, 60),
        (-125, 50),
        (-125, 40),
        (-117, 33),
        (-105, 25),
        (-97, 26),
        (-82, 25),
        (-81, 30),
        (-75, 35),
        (-70, 42),
        (-67, 45),
        (-60, 47),
        (-55, 52),
        (-60, 60),
        (-65, 68),
        (-80, 70),
        (-100, 73),
        (-120, 75),
        (-145, 72),
        (-168, 66),
    ],
    # South America
    [
        (-82, 10),
        (-77, 0),
        (-80, -5),
        (-70, -15),
        (-60, -5),
        (-50, 0),
        (-35, -5),
        (-40, -23),
        (-55, -35),
        (-68, -55),
        (-75, -50),
        (-75, -40),
        (-70, -20),
        (-80, -5),
        (-82, 10),
    ],
    # Europe
    [
        (-10, 36),
        (-10, 45),
        (-5, 48),
        (0, 52),
        (5, 55),
        (10, 58),
        (20, 60),
        (28, 70),
        (35, 70),
        (30, 60),
        (25, 55),
        (20, 50),
        (15, 45),
        (20, 40),
        (25, 35),
        (35, 35),
        (28, 42),
        (20, 38),
        (10, 38),
        (-10, 36),
    ],
    # Africa
    [
        (-17, 15),
        (-17, 28),
        (-5, 36),
        (10, 38),
        (20, 33),
        (35, 30),
        (45, 12),
        (52, 12),
        (45, 0),
        (42, -10),
        (35, -25),
        (25, -34),
        (18, -35),
        (12, -20),
        (15, -5),
        (5, 5),
        (-10, 5),
        (-17, 15),
    ],
    # Asia
    [
        (35, 30),
        (45, 42),
        (52, 45),
        (70, 42),
        (80, 30),
        (75, 15),
        (90, 22),
        (100, 15),
        (105, 22),
        (110, 5),
        (120, 25),
        (130, 35),
        (140, 45),
        (145, 55),
        (135, 70),
        (100, 78),
        (70, 75),
        (50, 70),
        (30, 70),
        (35, 50),
        (45, 45),
        (35, 30),
    ],
    # Australia
    [
        (113, -22),
        (120, -18),
        (135, -12),
        (145, -15),
        (152, -25),
        (150, -38),
        (140, -38),
        (130, -33),
        (115, -35),
        (113, -22),
    ],
]

# Robinson lookup table (latitude in degrees -> scale factors)
robinson_table = np.array(
    [
        [0, 1.0000, 0.0000],
        [5, 0.9986, 0.0620],
        [10, 0.9954, 0.1240],
        [15, 0.9900, 0.1860],
        [20, 0.9822, 0.2480],
        [25, 0.9730, 0.3100],
        [30, 0.9600, 0.3720],
        [35, 0.9427, 0.4340],
        [40, 0.9216, 0.4958],
        [45, 0.8962, 0.5571],
        [50, 0.8679, 0.6176],
        [55, 0.8350, 0.6769],
        [60, 0.7986, 0.7346],
        [65, 0.7597, 0.7903],
        [70, 0.7186, 0.8435],
        [75, 0.6732, 0.8936],
        [80, 0.6213, 0.9394],
        [85, 0.5722, 0.9761],
        [90, 0.5322, 1.0000],
    ]
)

# Create 2x2 subplot figure for comparing projections
fig, axes = plt.subplots(2, 2, figsize=(16, 9))
axes = axes.flatten()

# Projection names and their configurations
projection_names = ["Mercator", "Mollweide", "Robinson", "Sinusoidal"]
projection_ylims = [(-3.0, 3.0), (-1.6, 1.6), (-1.5, 1.5), (-1.8, 1.8)]
projection_aspects = [1.5, 2.0, 1.8, 2.0]

# Tissot indicatrix positions
tissot_lons = [-120, -60, 0, 60, 120]
tissot_lats = [-45, 0, 45]

# Process each projection
for idx, (proj_name, ylim, aspect) in enumerate(
    zip(projection_names, projection_ylims, projection_aspects, strict=True)
):
    ax = axes[idx]

    # Set ocean background
    ax.set_facecolor("#d4e8f7")

    # Prepare data for graticule lines using seaborn
    graticule_data = []

    # Longitude lines (meridians) - every 30 degrees
    for lon in range(-180, 181, 30):
        lats_line = np.linspace(-85, 85, 100)
        lons_line = np.full_like(lats_line, float(lon))

        # Apply projection based on projection type
        if proj_name == "Mercator":
            x = np.radians(lons_line)
            lat_clamped = np.clip(lats_line, -85, 85)
            y = np.log(np.tan(np.pi / 4 + np.radians(lat_clamped) / 2))
        elif proj_name == "Mollweide":
            lon_rad = np.radians(lons_line)
            lat_rad = np.radians(lats_line)
            theta = lat_rad.copy()
            for _ in range(10):
                delta = -(2 * theta + np.sin(2 * theta) - np.pi * np.sin(lat_rad)) / (2 + 2 * np.cos(2 * theta) + 1e-10)
                theta = theta + delta
            x = (2 * np.sqrt(2) / np.pi) * lon_rad * np.cos(theta)
            y = np.sqrt(2) * np.sin(theta)
        elif proj_name == "Robinson":
            abs_lat = np.abs(lats_line)
            x_scale = np.interp(abs_lat, robinson_table[:, 0], robinson_table[:, 1])
            y_scale = np.interp(abs_lat, robinson_table[:, 0], robinson_table[:, 2])
            x = 0.8487 * np.radians(lons_line) * x_scale
            y = 1.3523 * y_scale * np.sign(lats_line)
        else:  # Sinusoidal
            lat_rad = np.radians(lats_line)
            x = np.radians(lons_line) * np.cos(lat_rad)
            y = lat_rad

        for i in range(len(x)):
            graticule_data.append({"x": x[i], "y": y[i], "line_id": f"lon_{lon}"})

    # Latitude lines (parallels) - every 30 degrees
    for lat in range(-60, 61, 30):
        lons_line = np.linspace(-180, 180, 200)
        lats_line = np.full_like(lons_line, float(lat))

        # Apply projection
        if proj_name == "Mercator":
            x = np.radians(lons_line)
            lat_clamped = np.clip(lats_line, -85, 85)
            y = np.log(np.tan(np.pi / 4 + np.radians(lat_clamped) / 2))
        elif proj_name == "Mollweide":
            lon_rad = np.radians(lons_line)
            lat_rad = np.radians(lats_line)
            theta = lat_rad.copy()
            for _ in range(10):
                delta = -(2 * theta + np.sin(2 * theta) - np.pi * np.sin(lat_rad)) / (2 + 2 * np.cos(2 * theta) + 1e-10)
                theta = theta + delta
            x = (2 * np.sqrt(2) / np.pi) * lon_rad * np.cos(theta)
            y = np.sqrt(2) * np.sin(theta)
        elif proj_name == "Robinson":
            abs_lat = np.abs(lats_line)
            x_scale = np.interp(abs_lat, robinson_table[:, 0], robinson_table[:, 1])
            y_scale = np.interp(abs_lat, robinson_table[:, 0], robinson_table[:, 2])
            x = 0.8487 * np.radians(lons_line) * x_scale
            y = 1.3523 * y_scale * np.sign(lats_line)
        else:  # Sinusoidal
            lat_rad = np.radians(lats_line)
            x = np.radians(lons_line) * np.cos(lat_rad)
            y = lat_rad

        for i in range(len(x)):
            graticule_data.append({"x": x[i], "y": y[i], "line_id": f"lat_{lat}"})

    # Draw graticule using seaborn lineplot
    graticule_df = pd.DataFrame(graticule_data)
    sns.lineplot(
        data=graticule_df,
        x="x",
        y="y",
        hue="line_id",
        palette=["#888888"] * len(graticule_df["line_id"].unique()),
        linewidth=0.8,
        alpha=0.85,
        legend=False,
        ax=ax,
    )

    # Draw coastlines with projection
    for coastline in coastlines_data:
        lons = np.array([p[0] for p in coastline])
        lats = np.array([p[1] for p in coastline])

        # Apply projection
        if proj_name == "Mercator":
            x = np.radians(lons)
            lat_clamped = np.clip(lats, -85, 85)
            y = np.log(np.tan(np.pi / 4 + np.radians(lat_clamped) / 2))
        elif proj_name == "Mollweide":
            lon_rad = np.radians(lons)
            lat_rad = np.radians(lats)
            theta = lat_rad.copy()
            for _ in range(10):
                delta = -(2 * theta + np.sin(2 * theta) - np.pi * np.sin(lat_rad)) / (2 + 2 * np.cos(2 * theta) + 1e-10)
                theta = theta + delta
            x = (2 * np.sqrt(2) / np.pi) * lon_rad * np.cos(theta)
            y = np.sqrt(2) * np.sin(theta)
        elif proj_name == "Robinson":
            abs_lat = np.abs(lats)
            x_scale = np.interp(abs_lat, robinson_table[:, 0], robinson_table[:, 1])
            y_scale = np.interp(abs_lat, robinson_table[:, 0], robinson_table[:, 2])
            x = 0.8487 * np.radians(lons) * x_scale
            y = 1.3523 * y_scale * np.sign(lats)
        else:  # Sinusoidal
            lat_rad = np.radians(lats)
            x = np.radians(lons) * np.cos(lat_rad)
            y = lat_rad

        ax.fill(x, y, color="#c8d8c8", edgecolor="#306998", linewidth=1.2, alpha=0.9, zorder=2)

    # Draw Tissot indicatrices using seaborn scatterplot for centers
    tissot_centers = []
    for t_lon in tissot_lons:
        for t_lat in tissot_lats:
            if proj_name == "Mercator" and abs(t_lat) > 75:
                continue

            # Create small circle in geographic coordinates
            angles = np.linspace(0, 2 * np.pi, 50)
            radius = 8  # degrees
            circle_lons = t_lon + radius * np.cos(angles) / np.cos(np.radians(t_lat))
            circle_lats = t_lat + radius * np.sin(angles)
            circle_lats = np.clip(circle_lats, -85, 85)

            # Apply projection to circle
            if proj_name == "Mercator":
                cx = np.radians(circle_lons)
                cy = np.log(np.tan(np.pi / 4 + np.radians(circle_lats) / 2))
            elif proj_name == "Mollweide":
                lon_rad = np.radians(circle_lons)
                lat_rad = np.radians(circle_lats)
                theta = lat_rad.copy()
                for _ in range(10):
                    delta = -(2 * theta + np.sin(2 * theta) - np.pi * np.sin(lat_rad)) / (
                        2 + 2 * np.cos(2 * theta) + 1e-10
                    )
                    theta = theta + delta
                cx = (2 * np.sqrt(2) / np.pi) * lon_rad * np.cos(theta)
                cy = np.sqrt(2) * np.sin(theta)
            elif proj_name == "Robinson":
                abs_lat = np.abs(circle_lats)
                x_scale = np.interp(abs_lat, robinson_table[:, 0], robinson_table[:, 1])
                y_scale = np.interp(abs_lat, robinson_table[:, 0], robinson_table[:, 2])
                cx = 0.8487 * np.radians(circle_lons) * x_scale
                cy = 1.3523 * y_scale * np.sign(circle_lats)
            else:  # Sinusoidal
                lat_rad = np.radians(circle_lats)
                cx = np.radians(circle_lons) * np.cos(lat_rad)
                cy = lat_rad

            ax.fill(cx, cy, color="#FFD43B", edgecolor="#b8940a", linewidth=1.0, alpha=0.5, zorder=3)

            # Collect center point for seaborn scatterplot
            center_x = np.mean(cx)
            center_y = np.mean(cy)
            tissot_centers.append({"x": center_x, "y": center_y})

    # Plot Tissot centers with seaborn scatterplot
    if tissot_centers:
        tissot_df = pd.DataFrame(tissot_centers)
        sns.scatterplot(data=tissot_df, x="x", y="y", color="#b8940a", s=20, marker=".", legend=False, ax=ax, zorder=4)

    # Styling
    ax.set_title(proj_name, fontsize=20, fontweight="bold", pad=8)
    ax.set_xlim(-3.5, 3.5)
    ax.set_ylim(ylim)
    ax.set_aspect(aspect)

    # Add latitude labels on the left side for all projections
    for lat_val in [-60, -30, 0, 30, 60]:
        if proj_name == "Mercator":
            y_pos = np.log(np.tan(np.pi / 4 + np.radians(lat_val) / 2))
        elif proj_name == "Robinson":
            y_scale = np.interp(abs(lat_val), robinson_table[:, 0], robinson_table[:, 2])
            y_pos = 1.3523 * y_scale * np.sign(lat_val)
        elif proj_name == "Mollweide":
            lat_rad = np.radians(lat_val)
            theta = lat_rad
            for _ in range(10):
                delta = -(2 * theta + np.sin(2 * theta) - np.pi * np.sin(lat_rad)) / (2 + 2 * np.cos(2 * theta) + 1e-10)
                theta = theta + delta
            y_pos = np.sqrt(2) * np.sin(theta)
        else:  # Sinusoidal
            y_pos = np.radians(lat_val)
        if ylim[0] <= y_pos <= ylim[1]:
            ax.text(-3.4, y_pos, f"{lat_val}°", fontsize=9, ha="right", va="center", color="#444444")

    # Add longitude labels at the bottom for all projections
    for lon_val in [-120, -60, 0, 60, 120]:
        if proj_name == "Mercator":
            x_pos = np.radians(lon_val)
        elif proj_name == "Robinson":
            x_scale = np.interp(0, robinson_table[:, 0], robinson_table[:, 1])
            x_pos = 0.8487 * np.radians(lon_val) * x_scale
        elif proj_name == "Mollweide":
            x_pos = (2 * np.sqrt(2) / np.pi) * np.radians(lon_val)
        else:  # Sinusoidal
            x_pos = np.radians(lon_val)
        ax.text(x_pos, ylim[0] + 0.12, f"{lon_val}°", fontsize=9, ha="center", va="bottom", color="#444444")

    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("")
    ax.set_ylabel("")

    # Add subtle border
    for spine in ax.spines.values():
        spine.set_edgecolor("#888888")
        spine.set_linewidth(1.5)

# Main title
fig.suptitle("map-projections · seaborn · pyplots.ai", fontsize=26, fontweight="bold", y=0.98)

# Add legend for Tissot indicatrices and graticule
legend_elements = [
    Patch(facecolor="#FFD43B", edgecolor="#b8940a", alpha=0.5, label="Tissot Indicatrix (distortion)"),
    Patch(facecolor="#c8d8c8", edgecolor="#306998", alpha=0.9, label="Land"),
    Line2D([0], [0], color="#888888", linewidth=0.8, alpha=0.85, label="Graticule (30° intervals)"),
]
fig.legend(
    handles=legend_elements,
    loc="lower center",
    ncol=3,
    fontsize=12,
    frameon=True,
    fancybox=True,
    framealpha=0.9,
    bbox_to_anchor=(0.5, 0.01),
)

plt.tight_layout(rect=[0, 0.06, 1, 0.95])
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
