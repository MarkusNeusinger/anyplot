"""anyplot.ai
flowmap-origin-destination: Origin-Destination Flow Map
Library: seaborn | Python 3.13
Quality: pending | Updated: 2026-05-20
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

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

flow_min, flow_max = df_flows["flow"].min(), df_flows["flow"].max()
# Linewidth proportional to flow magnitude: 1.0 (min) to 5.0 (max)
df_flows["lw"] = 1.0 + 4.0 * (df_flows["flow"] - flow_min) / (flow_max - flow_min)

# Arc colors from seaborn's YlOrRd palette mapped to flow magnitude
n_colors = 256
arc_palette = sns.color_palette("YlOrRd", n_colors=n_colors)
df_flows["color_idx"] = ((df_flows["flow"] - flow_min) / (flow_max - flow_min) * (n_colors - 1)).astype(int)

df_cities = pd.DataFrame([{"city": name, "lat": coords[0], "lon": coords[1]} for name, coords in cities.items()])

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.set_xlim(-180, 180)
ax.set_ylim(-60, 80)

# Draw curved arcs: quadratic Bezier with linewidth proportional to flow
n_points = 50
for _, row in df_flows.iterrows():
    t = np.linspace(0, 1, n_points)
    x0, y0 = row["origin_lon"], row["origin_lat"]
    x2, y2 = row["dest_lon"], row["dest_lat"]
    mid_x = (x0 + x2) / 2
    mid_y = (y0 + y2) / 2
    dx, dy = x2 - x0, y2 - y0
    length = np.sqrt(dx**2 + dy**2)
    offset = length * 0.15
    ctrl_x = mid_x - dy / length * offset
    ctrl_y = mid_y + dx / length * offset
    x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * ctrl_x + t**2 * x2
    y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * ctrl_y + t**2 * y2
    color = arc_palette[int(row["color_idx"])]
    ax.plot(x, y, color=color, linewidth=row["lw"], alpha=0.65, solid_capstyle="round", zorder=1)

# City nodes using seaborn scatterplot — Okabe-Ito position 1 as first (only) series
sns.scatterplot(
    data=df_cities, x="lon", y="lat", s=200, color="#009E73", edgecolor=PAGE_BG, linewidth=1.5, ax=ax, zorder=3
)

# City labels with custom offsets to prevent overlap
for _, row in df_cities.iterrows():
    offset = label_offsets.get(row["city"], (5, 5))
    ax.annotate(
        row["city"],
        (row["lon"], row["lat"]),
        xytext=offset,
        textcoords="offset points",
        fontsize=6,
        fontweight="bold",
        color=INK,
        zorder=4,
    )

# Geographic reference lines
ax.axhline(y=0, color=INK_SOFT, linestyle="--", linewidth=0.5, alpha=0.4, zorder=0)
ax.axvline(x=0, color=INK_SOFT, linestyle="--", linewidth=0.5, alpha=0.4, zorder=0)

# Style
ax.set_xlabel("Longitude", fontsize=10, color=INK)
ax.set_ylabel("Latitude", fontsize=10, color=INK)
ax.set_title("flowmap-origin-destination · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
sns.despine(ax=ax, left=False, bottom=False)

# Colorbar for flow magnitude
norm = plt.Normalize(vmin=flow_min, vmax=flow_max)
sm = plt.cm.ScalarMappable(cmap="YlOrRd", norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, shrink=0.6, aspect=20, pad=0.02)
cbar.set_label("Flow Volume", fontsize=8, color=INK)
cbar.ax.tick_params(labelsize=7, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, bbox_inches="tight", facecolor=PAGE_BG)
