"""anyplot.ai
network-transport-static: Static Transport Network Diagram
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-18
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Column constants
FROM_STATION = "From station"  # role: stations
FROM_X = "From x"  # role: extra
FROM_Y = "From y"  # role: extra
TO_STATION = "To station"  # role: extra
TO_X = "To x"  # role: extra
TO_Y = "To y"  # role: extra
ROUTE = "Route"  # role: routes
DEPARTURE = "Departure"  # role: extra
ARRIVAL = "Arrival"  # role: extra
ROUTE_TYPE = "Route type"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("routes.csv")
# Regional rail network: stations with schematic x/y positions, one row per directed route
stations = {
    "Central": (0.5, 0.5),
    "North": (0.5, 0.92),
    "East": (0.92, 0.5),
    "South": (0.5, 0.08),
    "West": (0.08, 0.5),
    "Airport": (0.88, 0.88),
    "University": (0.12, 0.88),
    "Harbor": (0.88, 0.12),
    "Old Town": (0.12, 0.12),
}
express = "Regional Express (RE)"
airport = "Airport Service (AIR)"
suburban = "S-Bahn (S)"
routes = [
    ("Central", "North", "RE1", "06:00", "06:18", express),
    ("Central", "East", "RE2", "06:10", "06:28", express),
    ("Central", "South", "RE3", "06:20", "06:38", express),
    ("Central", "West", "RE4", "06:15", "06:33", express),
    ("North", "Central", "RE1", "06:30", "06:48", express),
    ("East", "Central", "RE2", "06:40", "06:58", express),
    ("South", "Central", "RE3", "06:50", "07:08", express),
    ("West", "Central", "RE4", "06:45", "07:03", express),
    ("Central", "Airport", "AIR", "05:30", "06:00", airport),
    ("Airport", "Central", "AIR", "22:00", "22:30", airport),
    ("North", "University", "S1", "07:00", "07:15", suburban),
    ("North", "Airport", "S2", "07:05", "07:22", suburban),
    ("East", "Harbor", "S3", "07:10", "07:25", suburban),
    ("South", "Harbor", "S4", "07:20", "07:38", suburban),
    ("South", "Old Town", "S5", "07:25", "07:43", suburban),
    ("West", "Old Town", "S6", "07:15", "07:32", suburban),
    ("West", "University", "S7", "07:30", "07:48", suburban),
]
df = pd.DataFrame(routes, columns=[FROM_STATION, TO_STATION, ROUTE, DEPARTURE, ARRIVAL, ROUTE_TYPE])
df[[FROM_X, FROM_Y]] = [stations[s] for s in df[FROM_STATION]]
df[[TO_X, TO_Y]] = [stations[s] for s in df[TO_STATION]]

# Plot
NODE_RADIUS = 0.035
CURVE = 0.28  # arc3 curvature for station pairs served in both directions

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Station nodes, taken from the unique stations in df at their given coordinates
nodes = pd.concat(
    [
        df[[FROM_STATION, FROM_X, FROM_Y]].set_axis(["name", "x", "y"], axis=1),
        df[[TO_STATION, TO_X, TO_Y]].set_axis(["name", "x", "y"], axis=1),
    ]
).drop_duplicates("name")
node_patches = {}
for name, x, y in nodes.itertuples(index=False):
    circle = mpatches.Circle((x, y), NODE_RADIUS, facecolor=PAGE_BG, edgecolor=INK_SOFT, linewidth=1.6, zorder=4)
    ax.add_patch(circle)
    node_patches[name] = circle
    ax.annotate(
        name,
        (x, y - NODE_RADIUS - 0.012),
        fontsize=8,
        ha="center",
        va="top",
        fontweight="bold",
        color=INK,
        bbox={"boxstyle": "round,pad=0.12", "facecolor": PAGE_BG, "edgecolor": "none", "alpha": 0.85},
        zorder=6,
    )

# Routes: one arrow per row, colored by route type; station pairs served both ways curve apart
route_types = list(dict.fromkeys(df[ROUTE_TYPE]))
type_color = {t: IMPRINT_PALETTE[i] for i, t in enumerate(route_types)}
pair_count = df.apply(lambda r: frozenset((r[FROM_STATION], r[TO_STATION])), axis=1).value_counts()

for row in df.to_dict("records"):
    src, dst = row[FROM_STATION], row[TO_STATION]
    x1, y1, x2, y2 = row[FROM_X], row[FROM_Y], row[TO_X], row[TO_Y]
    color = type_color[row[ROUTE_TYPE]]
    two_way = pair_count[frozenset((src, dst))] > 1
    rad = CURVE if two_way else 0.0  # reversed direction flips the arc3 side, so the pair separates

    arrow = mpatches.FancyArrowPatch(
        (x1, y1),
        (x2, y2),
        connectionstyle=f"arc3,rad={rad}",
        arrowstyle="-|>,head_length=0.9,head_width=0.45",
        patchA=node_patches[src],
        patchB=node_patches[dst],
        shrinkA=0,
        shrinkB=0,
        color=color,
        linewidth=1.6,
        alpha=0.9,
        zorder=1,
    )
    ax.add_patch(arrow)

    # Label on its own curve (quadratic Bezier of the arc3 path); two-way pairs sit at 38 % from
    # their own source so the two labels of a pair stagger along the line instead of colliding
    t = 0.38 if two_way else 0.5
    dx, dy = x2 - x1, y2 - y1
    cx, cy = (x1 + x2) / 2 + rad * dy, (y1 + y2) / 2 - rad * dx
    lx = (1 - t) ** 2 * x1 + 2 * t * (1 - t) * cx + t**2 * x2
    ly = (1 - t) ** 2 * y1 + 2 * t * (1 - t) * cy + t**2 * y2
    ax.annotate(
        f"{row[ROUTE]} {row[DEPARTURE]}→{row[ARRIVAL]}",
        (lx, ly),
        fontsize=6,
        ha="center",
        va="center",
        color=INK,
        fontweight="bold",
        bbox={"boxstyle": "round,pad=0.2", "facecolor": ELEVATED_BG, "edgecolor": color, "linewidth": 1.0},
        zorder=5,
    )

# Legend below the plot
legend_elements = [mpatches.Patch(facecolor=type_color[t], edgecolor=type_color[t], label=t) for t in route_types]
leg = ax.legend(
    handles=legend_elements, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=len(route_types), fontsize=7
)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

# Styling
pad = NODE_RADIUS + 0.06
ax.set_xlim(df[[FROM_X, TO_X]].min().min() - pad, df[[FROM_X, TO_X]].max().max() + pad)
ax.set_ylim(df[[FROM_Y, TO_Y]].min().min() - pad - 0.03, df[[FROM_Y, TO_Y]].max().max() + pad)
ax.set_aspect("equal")
ax.set_title("network-transport-static · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel("Relative position (west → east)", fontsize=9, color=INK)
ax.set_ylabel("Relative position (south → north)", fontsize=9, color=INK)
ax.tick_params(axis="both", labelsize=7, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.grid(True, alpha=0.12, linewidth=0.6, color=INK)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

fig.subplots_adjust(left=0.1, right=0.97, top=0.93, bottom=0.2)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
