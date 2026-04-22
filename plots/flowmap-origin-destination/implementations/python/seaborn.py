""" pyplots.ai
flowmap-origin-destination: Origin-Destination Flow Map
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-16
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data: Migration flows between major world cities
np.random.seed(42)

cities = {
    "New York": (40.71, -74.01),
    "London": (51.51, -0.13),
    "Tokyo": (35.68, 139.69),
    "Sydney": (-33.87, 151.21),
    "Dubai": (25.20, 55.27),
    "Singapore": (1.35, 103.82),
    "Paris": (48.86, 2.35),
    "Los Angeles": (34.05, -118.24),
    "Hong Kong": (22.32, 114.17),
    "Frankfurt": (50.11, 8.68),
    "Mumbai": (19.08, 72.88),
    "Sao Paulo": (-23.55, -46.63),
}

# Label offsets to prevent overlap in European cluster
label_offsets = {
    "New York": (5, 8),
    "London": (-60, 10),
    "Tokyo": (8, -15),
    "Sydney": (8, 5),
    "Dubai": (8, 5),
    "Singapore": (8, -15),
    "Paris": (-45, -18),
    "Los Angeles": (-85, 8),
    "Hong Kong": (8, 8),
    "Frankfurt": (8, 8),
    "Mumbai": (8, -15),
    "Sao Paulo": (8, 5),
}

# Create flow data between cities
flows = [
    ("New York", "London", 850),
    ("New York", "Los Angeles", 720),
    ("London", "Paris", 580),
    ("London", "Dubai", 450),
    ("Tokyo", "Hong Kong", 620),
    ("Tokyo", "Singapore", 480),
    ("Sydney", "Singapore", 390),
    ("Dubai", "Mumbai", 510),
    ("Los Angeles", "Tokyo", 340),
    ("Paris", "Frankfurt", 420),
    ("Hong Kong", "Singapore", 550),
    ("New York", "Sao Paulo", 280),
    ("London", "Frankfurt", 380),
    ("Singapore", "Sydney", 310),
    ("Mumbai", "Dubai", 460),
    ("Frankfurt", "Dubai", 290),
    ("Paris", "New York", 410),
    ("Tokyo", "Los Angeles", 370),
]

df_flows = pd.DataFrame(flows, columns=["origin", "destination", "flow"])
df_flows["origin_lat"] = df_flows["origin"].map(lambda x: cities[x][0])
df_flows["origin_lon"] = df_flows["origin"].map(lambda x: cities[x][1])
df_flows["dest_lat"] = df_flows["destination"].map(lambda x: cities[x][0])
df_flows["dest_lon"] = df_flows["destination"].map(lambda x: cities[x][1])

# Create arc points using quadratic Bezier curves for seaborn lineplot
n_points = 50
arc_data = []

for idx, row in df_flows.iterrows():
    t = np.linspace(0, 1, n_points)
    x0, y0 = row["origin_lon"], row["origin_lat"]
    x2, y2 = row["dest_lon"], row["dest_lat"]
    # Control point offset perpendicular to line for curve
    mid_x = (x0 + x2) / 2
    mid_y = (y0 + y2) / 2
    dx = x2 - x0
    dy = y2 - y0
    length = np.sqrt(dx**2 + dy**2)
    offset = length * 0.15
    ctrl_x = mid_x - dy / length * offset
    ctrl_y = mid_y + dx / length * offset
    # Quadratic Bezier
    x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * ctrl_x + t**2 * x2
    y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * ctrl_y + t**2 * y2
    for i in range(n_points):
        arc_data.append(
            {
                "x": x[i],
                "y": y[i],
                "flow_id": idx,
                "flow": row["flow"],
                "route": f"{row['origin']} → {row['destination']}",
            }
        )

df_arcs = pd.DataFrame(arc_data)

# City dataframe for scatter plot
df_cities = pd.DataFrame([{"city": name, "lat": coords[0], "lon": coords[1]} for name, coords in cities.items()])

# Plot setup with seaborn styling
sns.set_theme(style="whitegrid", context="talk", font_scale=1.2)
fig, ax = plt.subplots(figsize=(16, 9))
ax.set_facecolor("#f0f4f8")

# Set map bounds
ax.set_xlim(-180, 180)
ax.set_ylim(-60, 80)

# Draw curved arcs using seaborn lineplot with hue for flow magnitude
sns.lineplot(
    data=df_arcs,
    x="x",
    y="y",
    hue="flow",
    units="flow_id",
    estimator=None,
    palette="YlOrRd",
    linewidth=2.5,
    alpha=0.6,
    legend=False,
    ax=ax,
    zorder=1,
)

# Plot cities using seaborn scatterplot
sns.scatterplot(
    data=df_cities, x="lon", y="lat", s=350, color="#306998", edgecolor="white", linewidth=2.5, ax=ax, zorder=3
)

# Add city labels with custom offsets to avoid overlap
for _, row in df_cities.iterrows():
    offset = label_offsets.get(row["city"], (5, 5))
    ax.annotate(
        row["city"],
        (row["lon"], row["lat"]),
        xytext=offset,
        textcoords="offset points",
        fontsize=12,
        fontweight="bold",
        color="#333333",
        zorder=4,
    )

# Reference lines for equator and prime meridian
ax.axhline(y=0, color="#888888", linestyle="--", linewidth=0.8, alpha=0.5, zorder=0)
ax.axvline(x=0, color="#888888", linestyle="--", linewidth=0.8, alpha=0.5, zorder=0)

# Styling with seaborn
ax.set_xlabel("Longitude", fontsize=20)
ax.set_ylabel("Latitude", fontsize=20)
ax.set_title("flowmap-origin-destination · seaborn · pyplots.ai", fontsize=24, fontweight="bold")
ax.tick_params(axis="both", labelsize=16)
sns.despine(ax=ax, left=False, bottom=False)

# Add colorbar for flow magnitude
norm = plt.Normalize(vmin=df_flows["flow"].min(), vmax=df_flows["flow"].max())
sm = plt.cm.ScalarMappable(cmap="YlOrRd", norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, shrink=0.6, aspect=20, pad=0.02)
cbar.set_label("Flow Volume", fontsize=16)
cbar.ax.tick_params(labelsize=14)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
