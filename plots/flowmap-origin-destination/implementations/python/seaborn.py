""" anyplot.ai
flowmap-origin-destination: Origin-Destination Flow Map
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-20
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
LAND_COLOR = "#C8C2B8" if THEME == "light" else "#3A3A35"  # higher contrast than prior values

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

# Simplified world coastline polygons for geographic context
WORLD_COASTLINES = [
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
    # Asia (connected to Europe/Africa via Middle East)
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

# Label offsets — LA moved right + below to clear y-axis tick '40' at lat=40
label_offsets = {
    "New York": (5, 8),
    "London": (-60, 10),
    "Tokyo": (-42, 8),
    "Sydney": (8, 5),
    "Dubai": (8, 5),
    "Singapore": (8, -15),
    "Paris": (-45, -18),
    "Los Angeles": (12, -10),
    "Hong Kong": (8, -15),
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

# Arc colors from cividis: CVD-safe, dark navy at low end avoids viridis yellow-on-light issue
n_colors = 256
arc_palette = sns.color_palette("cividis", n_colors=n_colors)
df_flows["color_idx"] = ((df_flows["flow"] - flow_min) / (flow_max - flow_min) * (n_colors - 1)).astype(int)

# Per-city total incoming flow for seaborn size= aesthetic
city_incoming = df_flows.groupby("destination")["flow"].sum().reset_index()
city_incoming.columns = ["city", "incoming_flow"]
df_cities = pd.DataFrame([{"city": name, "lat": coords[0], "lon": coords[1]} for name, coords in cities.items()])
df_cities = df_cities.merge(city_incoming, on="city", how="left").fillna(0)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.set_xlim(-180, 180)
ax.set_ylim(-60, 80)

# Draw simplified world coastlines — linewidth=0.8 for visible land/sea boundary
for coastline in WORLD_COASTLINES:
    lons = [p[0] for p in coastline]
    lats = [p[1] for p in coastline]
    ax.fill(lons, lats, color=LAND_COLOR, edgecolor=INK_SOFT, linewidth=0.8, alpha=0.9, zorder=0)

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

# City nodes: seaborn scatterplot with size= encoding per-city total incoming flow
sns.scatterplot(
    data=df_cities,
    x="lon",
    y="lat",
    size="incoming_flow",
    sizes=(60, 350),
    color="#009E73",
    edgecolor=PAGE_BG,
    linewidth=1.5,
    ax=ax,
    zorder=3,
    legend="brief",
)

# Style the size legend
leg = ax.get_legend()
if leg is not None:
    leg.set_title("Incoming\nFlow", prop={"size": 6})
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_title(), color=INK)
    for text in leg.get_texts():
        text.set_color(INK)
        text.set_fontsize(5)
    for handle in leg.legend_handles:
        try:
            handle.set_facecolor("#009E73")
            handle.set_edgecolor(PAGE_BG)
        except AttributeError:
            pass
    leg.set_loc("lower left")

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

# Colorbar for flow magnitude using cividis to match arc colors
norm = plt.Normalize(vmin=flow_min, vmax=flow_max)
sm = plt.cm.ScalarMappable(cmap="cividis", norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, shrink=0.6, aspect=20, pad=0.02)
cbar.set_label("Flow Volume", fontsize=8, color=INK)
cbar.ax.tick_params(labelsize=7, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, bbox_inches="tight", facecolor=PAGE_BG)
