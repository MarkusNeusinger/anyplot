""" anyplot.ai
flowmap-origin-destination: Origin-Destination Flow Map
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-27
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
LAND_COLOR = "#C8C2B8" if THEME == "light" else "#3A3A35"
BRAND = "#009E73"  # Imprint palette position 1: the city nodes are one series

# Imprint sequential ramp for marks (the arcs sit on the page), low to high flow
SEQ_MARKS = (
    [(0.0, "#009E73"), (0.687, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#6F7E20"), (0.21, "#009E73"), (1.0, "#CDD9FF")]
)
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", SEQ_MARKS)

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

# Constants
ARC_BEND = 0.15  # sideways bow of each Bezier arc, as a share of its length
MIN_LINEWIDTH, MAX_LINEWIDTH = 1.0, 5.0  # arc width range, proportional to flow
ARC_ALPHA = 0.65
LAT_PAD = 26  # degrees of land shown beyond the southernmost and northernmost city
# Simplified world coastlines (lon, lat) for geographic context
WORLD_COASTLINES = [
    # North America
    [(-168, 66), (-141, 70), (-130, 70), (-120, 60), (-125, 50), (-125, 40), (-117, 33), (-105, 25), (-97, 26)]
    + [(-82, 25), (-81, 30), (-75, 35), (-70, 42), (-67, 45), (-60, 47), (-55, 52), (-60, 60), (-65, 68), (-80, 70)]
    + [(-100, 73), (-120, 75), (-145, 72), (-168, 66)],
    # South America
    [(-82, 10), (-77, 0), (-80, -5), (-70, -15), (-60, -5), (-50, 0), (-35, -5), (-40, -23), (-55, -35), (-68, -55)]
    + [(-75, -50), (-75, -40), (-70, -20), (-80, -5), (-82, 10)],
    # Europe
    [(-10, 36), (-10, 45), (-5, 48), (0, 52), (5, 55), (10, 58), (20, 60), (28, 70), (35, 70), (30, 60), (25, 55)]
    + [(20, 50), (15, 45), (20, 40), (25, 35), (35, 35), (28, 42), (20, 38), (10, 38), (-10, 36)],
    # Africa
    [(-17, 15), (-17, 28), (-5, 36), (10, 38), (20, 33), (35, 30), (45, 12), (52, 12), (45, 0), (42, -10), (35, -25)]
    + [(25, -34), (18, -35), (12, -20), (15, -5), (5, 5), (-10, 5), (-17, 15)],
    # Asia
    [(35, 30), (45, 42), (52, 45), (70, 42), (80, 30), (75, 15), (90, 22), (100, 15), (105, 22), (110, 5), (120, 25)]
    + [(130, 35), (140, 45), (145, 55), (135, 70), (100, 78), (70, 75), (50, 70), (30, 70), (35, 50), (45, 45)]
    + [(35, 30)],
    # Australia
    [(113, -22), (120, -18), (135, -12), (145, -15), (152, -25), (150, -38), (140, -38), (130, -33), (115, -35)]
    + [(113, -22)],
]

# Columns: set these to your table's column names
ORIGIN = "Origin"  # role: origin_name
DESTINATION = "Destination"  # role: dest_name
FLOW = "Flow volume (thousand people)"  # role: flow
ORIGIN_LAT = "Origin latitude (°)"  # role: origin_lat
ORIGIN_LON = "Origin longitude (°)"  # role: origin_lon
DEST_LAT = "Destination latitude (°)"  # role: dest_lat
DEST_LON = "Destination longitude (°)"  # role: dest_lon

# Data: replace this block with your own table, for example df = pd.read_csv("flows.csv")
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
df = pd.DataFrame(flows, columns=[ORIGIN, DESTINATION, FLOW])
df[ORIGIN_LAT] = df[ORIGIN].map(lambda c: cities[c][0])
df[ORIGIN_LON] = df[ORIGIN].map(lambda c: cities[c][1])
df[DEST_LAT] = df[DESTINATION].map(lambda c: cities[c][0])
df[DEST_LON] = df[DESTINATION].map(lambda c: cities[c][1])

# Plot: reads only df and the constants above
flow_norm = plt.Normalize(vmin=df[FLOW].min(), vmax=df[FLOW].max())
linewidths = MIN_LINEWIDTH + (MAX_LINEWIDTH - MIN_LINEWIDTH) * flow_norm(df[FLOW])

# One row per city (origins and destinations), sized by the flow arriving there
nodes = (
    pd.concat(
        [
            df[[ORIGIN, ORIGIN_LAT, ORIGIN_LON]].set_axis(["city", "lat", "lon"], axis=1),
            df[[DESTINATION, DEST_LAT, DEST_LON]].set_axis(["city", "lat", "lon"], axis=1),
        ]
    )
    .drop_duplicates("city")
    .reset_index(drop=True)
)
incoming = df.groupby(DESTINATION)[FLOW].sum()
nodes["Incoming flow"] = nodes["city"].map(incoming).fillna(0)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.set_xlim(-180, 180)
ax.set_ylim(
    max(-90, min(df[ORIGIN_LAT].min(), df[DEST_LAT].min()) - LAT_PAD),
    min(90, max(df[ORIGIN_LAT].max(), df[DEST_LAT].max()) + LAT_PAD),
)

for coastline in WORLD_COASTLINES:
    lons, lats = zip(*coastline, strict=True)
    ax.fill(lons, lats, color=LAND_COLOR, edgecolor=INK_SOFT, linewidth=0.8, alpha=0.9, zorder=0)

# Geographic reference lines: equator and prime meridian
ax.axhline(0, color=INK_SOFT, linestyle="--", linewidth=0.5, alpha=0.4, zorder=0)
ax.axvline(0, color=INK_SOFT, linestyle="--", linewidth=0.5, alpha=0.4, zorder=0)

# Quadratic Bezier arcs: ends on the two cities, control point bowed sideways of the midpoint
t = np.linspace(0, 1, 50)
arc_points = []
for (_, row), lw in zip(df.iterrows(), linewidths, strict=True):
    x0, y0, x2, y2 = row[ORIGIN_LON], row[ORIGIN_LAT], row[DEST_LON], row[DEST_LAT]
    dx, dy = x2 - x0, y2 - y0
    length = max(np.hypot(dx, dy), 1e-9)
    ctrl_x = (x0 + x2) / 2 - dy / length * length * ARC_BEND
    ctrl_y = (y0 + y2) / 2 + dx / length * length * ARC_BEND
    x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * ctrl_x + t**2 * x2
    y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * ctrl_y + t**2 * y2
    arc_points.append(np.column_stack([x, y]))
    ax.plot(
        x, y, color=imprint_seq(flow_norm(row[FLOW])), linewidth=lw, alpha=ARC_ALPHA, solid_capstyle="round", zorder=1
    )

# City nodes: seaborn size encoding of the incoming flow
sns.scatterplot(
    data=nodes,
    x="lon",
    y="lat",
    size="Incoming flow",
    sizes=(60, 350),
    color=BRAND,
    edgecolor=PAGE_BG,
    linewidth=1.5,
    legend="brief",
    ax=ax,
    zorder=3,
)
sns.move_legend(
    ax,
    "lower left",
    title="Incoming flow",
    fontsize=8,
    title_fontsize=8,
    frameon=True,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    labelcolor=INK,
    borderpad=0.8,
    labelspacing=1.1,
)
legend = ax.get_legend()
legend.get_title().set_color(INK)
for handle in legend.legend_handles:
    handle.set_markerfacecolor(BRAND)
    handle.set_markeredgecolor(PAGE_BG)

# Style
ax.set_xlabel("Longitude (°)", fontsize=10, color=INK)
ax.set_ylabel("Latitude (°)", fontsize=10, color=INK)
ax.set_title("flowmap-origin-destination · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
sns.despine(ax=ax, left=False, bottom=False)

# Colorbar for flow magnitude, the same ramp as the arcs
sm = plt.cm.ScalarMappable(cmap=imprint_seq, norm=flow_norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, shrink=0.6, aspect=20, pad=0.02)
cbar.set_label(FLOW, fontsize=10, color=INK)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)
plt.tight_layout()

# City labels: score every side of the node and keep the best one: no overlap with the labels already
# placed, no neighbouring node close to the label (so it reads as its own city's), as few arcs as possible
fig.canvas.draw()
renderer = fig.canvas.get_renderer()
node_xy = ax.transData.transform(nodes[["lon", "lat"]].to_numpy())
arc_xy = ax.transData.transform(np.vstack(arc_points))
NODE_CLEARANCE = 60  # pixels of free space between a label and any other city's node
placed = []
candidates = [(7, 5), (7, -14), (-7, 5), (-7, -14), (7, 16), (-7, 16), (7, -26), (-7, -26)]
for i, city in nodes.iterrows():
    options = []
    for dx, dy in candidates:
        label = ax.annotate(
            city["city"],
            (city["lon"], city["lat"]),
            xytext=(dx, dy),
            textcoords="offset points",
            ha="left" if dx > 0 else "right",
            fontsize=8,
            fontweight="bold",
            color=INK,
            arrowprops={"arrowstyle": "-", "color": INK, "linewidth": 0.7, "shrinkA": 1, "shrinkB": 5},
            zorder=4,
        )
        box = label.get_window_extent(renderer).expanded(1.08, 1.2)
        inside = ax.bbox.x0 <= box.x0 and box.x1 <= ax.bbox.x1 and ax.bbox.y0 <= box.y0 and box.y1 <= ax.bbox.y1
        label_hits = sum(box.overlaps(other) for other in placed)
        near_nodes = sum(
            box.x0 - NODE_CLEARANCE <= nx <= box.x1 + NODE_CLEARANCE
            and box.y0 - NODE_CLEARANCE <= ny <= box.y1 + NODE_CLEARANCE
            for j, (nx, ny) in enumerate(node_xy)
            if j != i
        )
        arc_hits = np.sum(
            (arc_xy[:, 0] >= box.x0) & (arc_xy[:, 0] <= box.x1) & (arc_xy[:, 1] >= box.y0) & (arc_xy[:, 1] <= box.y1)
        )
        score = 1e6 * (not inside) + 1e4 * label_hits + 1e3 * near_nodes + arc_hits
        options.append((score, label, box))
    score, best_label, best_box = min(options, key=lambda option: option[0])
    for _, label, _ in options:
        if label is not best_label:
            label.remove()
    placed.append(best_box)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
