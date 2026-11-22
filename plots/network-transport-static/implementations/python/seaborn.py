"""anyplot.ai
network-transport-static: Static Transport Network Diagram
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-18
"""

import os

import matplotlib.patches as mpatches
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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

sns.set_theme(
    style="white",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK_SOFT,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants
ROUTE_TYPE_NAMES = {"regional": "Regional Express (RE)", "local": "Local Service (S)", "express": "Express (EX)"}

# Columns: set these to your table's column names
SOURCE = "source_id"  # role: routes
TARGET = "target_id"  # role: extra
ROUTE_ID = "route_id"  # role: extra
DEPARTURE = "departure_time"  # role: extra
ARRIVAL = "arrival_time"  # role: extra
ROUTE_TYPE = "route_type"  # role: extra
SOURCE_LABEL = "source_label"  # role: stations
SOURCE_X = "source_x"  # role: extra
SOURCE_Y = "source_y"  # role: extra
TARGET_LABEL = "target_label"  # role: extra
TARGET_X = "target_x"  # role: extra
TARGET_Y = "target_y"  # role: extra
STATION_ID = "id"  # role: extra
STATION_LABEL = "label"  # role: extra
STATION_X = "x"  # role: extra
STATION_Y = "y"  # role: extra

# Data: replace this block with your own table, one row per route with its stations' label and x/y
# coordinates, for example df = pd.read_csv("routes.csv")
nodes = pd.DataFrame(
    {
        STATION_ID: list("ABCDEFGHIJ"),
        STATION_LABEL: [
            "Central Station",
            "North Terminal",
            "East Hub",
            "West Junction",
            "Park Station",
            "Market Square",
            "Airport",
            "Industrial Zone",
            "University",
            "Harbor",
        ],
        STATION_X: [0.5, 0.2, 0.8, 0.1, 0.4, 0.6, 0.9, 0.15, 0.5, 0.85],
        STATION_Y: [0.9, 0.7, 0.7, 0.45, 0.55, 0.55, 0.45, 0.2, 0.25, 0.15],
    }
).set_index(STATION_ID)
routes = pd.DataFrame(
    {
        SOURCE: list("AABCDGBEFDEFAHI"),
        TARGET: list("BCDGHJEFCEIIGIJ"),
        ROUTE_ID: ["RE 01", "RE 02", "RE 01", "RE 02", "RE 01", "RE 02"]
        + ["S 10", "S 10", "S 10", "S 20", "S 20", "S 10", "EX 99", "S 30", "S 30"],
        DEPARTURE: ["06:00", "06:15", "06:22", "06:40", "06:50", "07:10"]
        + ["07:00", "07:15", "07:28", "07:30", "07:52", "08:00", "08:00", "08:15", "08:45"],
        ARRIVAL: ["06:18", "06:35", "06:45", "07:05", "07:15", "07:40"]
        + ["07:12", "07:25", "07:42", "07:48", "08:10", "08:18", "08:35", "08:40", "09:15"],
        ROUTE_TYPE: ["regional"] * 6 + ["local"] * 5 + ["local", "express", "local", "local"],
    }
)
df = routes.join(nodes.add_prefix("source_"), on=SOURCE).join(nodes.add_prefix("target_"), on=TARGET)

# Plot: reads only df and the constants above
# One row per station, derived from the route table
station_cols = [STATION_ID, STATION_LABEL, STATION_X, STATION_Y]
ends = [
    df[[SOURCE, SOURCE_LABEL, SOURCE_X, SOURCE_Y]].set_axis(station_cols, axis=1),
    df[[TARGET, TARGET_LABEL, TARGET_X, TARGET_Y]].set_axis(station_cols, axis=1),
]
stations = pd.concat(ends).drop_duplicates(STATION_ID).reset_index(drop=True)
station_pos = stations.set_index(STATION_ID)[[STATION_X, STATION_Y]]
route_types = list(dict.fromkeys(df[ROUTE_TYPE]))
type_colors = {kind: IMPRINT_PALETTE[i] for i, kind in enumerate(route_types)}
x_span = station_pos[STATION_X].max() - station_pos[STATION_X].min()
y_span = station_pos[STATION_Y].max() - station_pos[STATION_Y].min()

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Routes first so nodes sit on top; parallel routes between one pair are offset sideways
pair_count = {}
label_gap = 0.075 * y_span

# Approximate label boxes in data units (cx, cy, half width, half height): station names, nodes, placed route labels
obstacles = []
for s in stations.itertuples(index=False):
    sx, sy = s[stations.columns.get_loc(STATION_X)], s[stations.columns.get_loc(STATION_Y)]
    name_half_w = (0.0065 * len(s[stations.columns.get_loc(STATION_LABEL)]) + 0.012) * x_span
    obstacles.append((sx, sy + label_gap + 0.04 * y_span, name_half_w, 0.06 * y_span))
    obstacles.append((sx, sy, 0.04 * x_span, 0.05 * y_span))


def overlap(a, b):
    ox = min(a[0] + a[2], b[0] + b[2]) - max(a[0] - a[2], b[0] - b[2])
    oy = min(a[1] + a[3], b[1] + b[3]) - max(a[1] - a[3], b[1] - b[3])
    return max(ox, 0) * max(oy, 0)


for route in df.itertuples(index=False):
    src, tgt = route[df.columns.get_loc(SOURCE)], route[df.columns.get_loc(TARGET)]
    x1, y1 = station_pos.loc[src]
    x2, y2 = station_pos.loc[tgt]

    pair = frozenset((src, tgt))
    pair_count[pair] = pair_count.get(pair, 0) + 1
    offset = (pair_count[pair] - 1) * 0.025 * max(x_span, y_span)

    dx, dy = x2 - x1, y2 - y1
    length = np.hypot(dx, dy)
    perp_x, perp_y = (-dy / length * offset, dx / length * offset) if length > 0 else (0.0, 0.0)
    x1o, y1o, x2o, y2o = x1 + perp_x, y1 + perp_y, x2 + perp_x, y2 + perp_y

    color = type_colors[route[df.columns.get_loc(ROUTE_TYPE)]]
    ax.annotate(
        "",
        xy=(x2o, y2o),
        xytext=(x1o, y1o),
        arrowprops={"arrowstyle": "-|>", "color": color, "lw": 1.4, "shrinkA": 13, "shrinkB": 13, "mutation_scale": 11},
    )

    label_text = (
        f"{route[df.columns.get_loc(ROUTE_ID)]}\n"
        f"{route[df.columns.get_loc(DEPARTURE)]}→{route[df.columns.get_loc(ARRIVAL)]}"
    )
    # Slide the label along its own edge to the spot that collides least with what is already placed
    candidates = []
    for t in np.linspace(0.3, 0.7, 17):
        box = (x1o + t * (x2o - x1o), y1o + t * (y2o - y1o), 0.07 * x_span, 0.06 * y_span)
        candidates.append((sum(overlap(box, other) for other in obstacles), abs(t - 0.5), box))
    box = min(candidates, key=lambda c: c[:2])[2]
    obstacles.append(box)
    ax.text(
        box[0],
        box[1],
        label_text,
        fontsize=6.5,
        ha="center",
        va="center",
        color=INK,
        zorder=5,
        bbox={
            "boxstyle": "round,pad=0.25",
            "facecolor": ELEVATED_BG,
            "edgecolor": color,
            "alpha": 0.92,
            "linewidth": 0.9,
        },
    )

# Station nodes
sns.scatterplot(
    data=stations,
    x=STATION_X,
    y=STATION_Y,
    s=420,
    color=IMPRINT_PALETTE[0],
    edgecolor=INK_SOFT,
    linewidth=1.3,
    ax=ax,
    zorder=10,
    legend=False,
)

for station in stations.itertuples(index=False):
    sx, sy = station[stations.columns.get_loc(STATION_X)], station[stations.columns.get_loc(STATION_Y)]
    ax.text(
        sx,
        sy + label_gap,
        station[stations.columns.get_loc(STATION_LABEL)],
        fontsize=7.5,
        fontweight="bold",
        ha="center",
        va="bottom",
        color=INK,
        bbox={
            "boxstyle": "round,pad=0.3",
            "facecolor": ELEVATED_BG,
            "edgecolor": INK_SOFT,
            "alpha": 0.94,
            "linewidth": 0.6,
        },
        zorder=11,
    )
    ax.text(
        sx,
        sy,
        station[stations.columns.get_loc(STATION_ID)],
        fontsize=9,
        fontweight="bold",
        color=PAGE_BG,
        ha="center",
        va="center",
        zorder=11,
    )

legend_handles = [
    mpatches.Patch(color=type_colors[kind], label=ROUTE_TYPE_NAMES.get(kind, kind)) for kind in route_types
]
ax.legend(handles=legend_handles, loc="upper left", fontsize=8, framealpha=0.92, edgecolor=INK_SOFT)

# Style
ax.set_xlim(station_pos[STATION_X].min() - 0.08 * x_span, station_pos[STATION_X].max() + 0.08 * x_span)
ax.set_ylim(station_pos[STATION_Y].min() - 0.1 * y_span, station_pos[STATION_Y].max() + 0.2 * y_span)
ax.axis("off")
ax.set_title("network-transport-static · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
