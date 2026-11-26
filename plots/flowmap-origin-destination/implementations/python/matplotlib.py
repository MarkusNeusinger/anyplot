"""anyplot.ai
flowmap-origin-destination: Origin-Destination Flow Map
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-20
"""

import os

import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
LAND_COLOR = "#E6E3D6" if THEME == "light" else "#2C2E27"
OCEAN_COLOR = "#D5E2EA" if THEME == "light" else "#1D2830"
BORDER_COLOR = "#A9A79B" if THEME == "light" else "#555650"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential ramp for marks (colored lines on the page), per theme
SEQ_MARKS = (
    [(0.0, "#009E73"), (0.338, "#4467A3"), (1.0, "#002850")]
    if THEME == "light"
    else [(0.0, "#007755"), (0.32, "#009E73"), (1.0, "#CDD9FF")]
)
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", SEQ_MARKS)

# Constants
LON_RANGE = (-180, 180)  # world basemap extent
LAT_RANGE = (-60, 80)
# Simplified continent outlines as (lon, lat) polygons
CONTINENTS = [
    [(-170, 60), (-170, 25), (-130, 25), (-100, 20), (-80, 25), (-60, 45), (-55, 50), (-70, 70), (-170, 70)],
    [(-80, 10), (-60, 5), (-35, -5), (-35, -25), (-55, -55), (-75, -55), (-80, -20)],
    [(-10, 35), (0, 35), (30, 35), (40, 45), (30, 60), (30, 70), (10, 70), (-10, 60)],
    [(-20, 35), (35, 35), (50, 15), (50, -5), (35, -35), (20, -35), (10, -5), (-20, 5)],
    [
        (30, 35),
        (60, 25),
        (70, 25),
        (100, 20),
        (120, 25),
        (145, 45),
        (145, 55),
        (180, 65),
        (180, 75),
        (60, 75),
        (30, 50),
    ],
    [(110, -10), (155, -10), (155, -40), (130, -40), (110, -25)],
]
ARC_BULGE = 0.28  # control-point height of each Bezier arc, as a share of the arc length
WIDTH_RANGE = (1.5, 8.0)  # arc line width in points, from the smallest to the largest flow
ALPHA_RANGE = (0.45, 0.8)  # arcs of larger flows are more opaque

# Columns: set these to your table's column names
ORIGIN_LAT = "origin_lat"  # role: origin_lat
ORIGIN_LON = "origin_lon"  # role: origin_lon
DEST_LAT = "dest_lat"  # role: dest_lat
DEST_LON = "dest_lon"  # role: dest_lon
FLOW = "Container volume (million TEUs)"  # role: flow
ORIGIN_NAME = "origin_name"  # role: origin_name
DEST_NAME = "dest_name"  # role: dest_name

# Data: replace this block with your own table, for example df = pd.read_csv("flows.csv")
port_xy = {
    "Shanghai": (121.47, 31.23),
    "Singapore": (103.82, 1.35),
    "Rotterdam": (4.48, 51.92),
    "Los Angeles": (-118.25, 33.75),
    "Dubai": (55.27, 25.20),
    "Hong Kong": (114.17, 22.32),
    "Busan": (129.03, 35.10),
    "Hamburg": (9.99, 53.55),
    "New York": (-74.00, 40.71),
    "Santos": (-46.33, -23.95),
}
trade = [
    ("Shanghai", "Los Angeles", 8.5),
    ("Shanghai", "Rotterdam", 6.2),
    ("Shanghai", "Singapore", 5.8),
    ("Singapore", "Rotterdam", 4.5),
    ("Hong Kong", "Los Angeles", 3.9),
    ("Busan", "Los Angeles", 3.2),
    ("Dubai", "Rotterdam", 2.8),
    ("Hamburg", "New York", 2.5),
    ("Rotterdam", "New York", 2.3),
    ("Santos", "Rotterdam", 1.9),
    ("Shanghai", "Dubai", 3.5),
    ("Singapore", "Dubai", 2.7),
    ("Hong Kong", "Singapore", 2.4),
    ("Shanghai", "Hamburg", 4.1),
    ("Busan", "Shanghai", 1.8),
]
df = pd.DataFrame(
    {
        ORIGIN_NAME: [o for o, _, _ in trade],
        DEST_NAME: [d for _, d, _ in trade],
        ORIGIN_LON: [port_xy[o][0] for o, _, _ in trade],
        ORIGIN_LAT: [port_xy[o][1] for o, _, _ in trade],
        DEST_LON: [port_xy[d][0] for _, d, _ in trade],
        DEST_LAT: [port_xy[d][1] for _, d, _ in trade],
        FLOW: [f for _, _, f in trade],
    }
)

# Plot: reads only df and the constants above
flow_min, flow_max = df[FLOW].min(), df[FLOW].max()
span = flow_max - flow_min if flow_max > flow_min else 1.0
share = (df[FLOW] - flow_min) / span  # 0 for the smallest flow, 1 for the largest


def width_of(s):
    return WIDTH_RANGE[0] + s * (WIDTH_RANGE[1] - WIDTH_RANGE[0])


def color_of(s):
    # the dark ramp starts near the page tone, so its low end is lifted to stay visible
    return imprint_seq(s if THEME == "light" else 0.3 + 0.7 * s)


def alpha_of(s):
    return ALPHA_RANGE[0] + s * (ALPHA_RANGE[1] - ALPHA_RANGE[0])


fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(OCEAN_COLOR)
ax.set_xlim(*LON_RANGE)
ax.set_ylim(*LAT_RANGE)

for polygon in CONTINENTS:
    xs, ys = zip(*polygon, strict=True)
    ax.fill(xs, ys, color=LAND_COLOR, edgecolor=BORDER_COLOR, linewidth=0.5, zorder=1)

# Quadratic Bezier arcs, thin ones drawn after thick ones so they stay visible on top
t = np.linspace(0, 1, 80)
for i in np.argsort(-df[FLOW].to_numpy()):
    row = df.iloc[i]
    ox, oy, dx, dy = row[ORIGIN_LON], row[ORIGIN_LAT], row[DEST_LON], row[DEST_LAT]
    length = np.hypot(dx - ox, dy - oy)
    # control point: midpoint pushed perpendicular to the chord
    cx = (ox + dx) / 2 - (dy - oy) * ARC_BULGE
    cy = (oy + dy) / 2 + (dx - ox) * ARC_BULGE
    x = (1 - t) ** 2 * ox + 2 * (1 - t) * t * cx + t**2 * dx
    y = (1 - t) ** 2 * oy + 2 * (1 - t) * t * cy + t**2 * dy
    ax.plot(
        x,
        y,
        color=color_of(share.iloc[i]),
        linewidth=width_of(share.iloc[i]),
        alpha=alpha_of(share.iloc[i]),
        zorder=3,
        solid_capstyle="round",
    )

# Ports: every distinct origin or destination
ports = pd.concat(
    [
        df[[ORIGIN_NAME, ORIGIN_LON, ORIGIN_LAT]].set_axis(["name", "lon", "lat"], axis=1),
        df[[DEST_NAME, DEST_LON, DEST_LAT]].set_axis(["name", "lon", "lat"], axis=1),
    ]
).drop_duplicates("name", ignore_index=True)
ax.scatter(ports["lon"], ports["lat"], s=60, c=IMPRINT_PALETTE[0], edgecolors=PAGE_BG, linewidths=1.2, zorder=4)

# Legend: line samples that carry the width and color encoding at three flow levels
legend_handles = []
for level in (flow_min, df[FLOW].median(), flow_max):
    s = (level - flow_min) / span
    legend_handles.append(
        mlines.Line2D(
            [],
            [],
            color=color_of(s),
            linewidth=width_of(s),
            alpha=alpha_of(s),
            label=f"{level:.1f} M TEUs",
            solid_capstyle="round",
        )
    )
leg = ax.legend(
    handles=legend_handles,
    loc="lower left",
    fontsize=8,
    title=FLOW,
    title_fontsize=9,
    framealpha=0.95,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    labelspacing=0.8,
)
plt.setp(leg.get_title(), color=INK)
plt.setp(leg.get_texts(), color=INK_SOFT)

# Style
title = "Global Port Trade Routes · flowmap-origin-destination · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)
ax.set_xlabel("Longitude (°)", fontsize=10, color=INK)
ax.set_ylabel("Latitude (°)", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(True, alpha=0.10, linewidth=0.5, color=INK, zorder=0)

fig.tight_layout()

# Port labels: greedy placement, each label takes the first direction that clears
# the labels already placed and every port marker
renderer = fig.canvas.get_renderer()
marker_boxes = [(px - 7, py - 7, px + 7, py + 7) for px, py in ax.transData.transform(ports[["lon", "lat"]].to_numpy())]
directions = [(1, 1), (1, -1), (-1, 1), (-1, -1), (0, 1), (0, -1), (1, 0), (-1, 0)]
gap = 8  # distance from the marker, in display pixels at 400 dpi
placed = []
for _, port in ports.iterrows():
    best = None
    for sx, sy in directions:
        label = ax.annotate(
            port["name"],
            (port["lon"], port["lat"]),
            xytext=(sx * 4, sy * 4),
            textcoords="offset points",
            ha="left" if sx > 0 else "right" if sx < 0 else "center",
            va="bottom" if sy > 0 else "top" if sy < 0 else "center",
            fontsize=8,
            fontweight="bold",
            color=INK,
            zorder=5,
        )
        bb = label.get_window_extent(renderer)
        box = (bb.x0, bb.y0, bb.x1, bb.y1)
        others = placed + marker_boxes

        def clash(a, b):
            return a[0] < b[2] + gap and b[0] < a[2] + gap and a[1] < b[3] + gap and b[1] < a[3] + gap

        hits = sum(clash(box, o) for o in others) + (box[0] < ax.bbox.x0 or box[2] > ax.bbox.x1)
        if best is None or hits < best[0]:
            if best is not None:
                best[2].remove()
            best = (hits, box, label)
        else:
            label.remove()
        if hits == 0:
            break
    placed.append(best[1])

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
