"""anyplot.ai
circlepacking-basic: Circle Packing Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_polygon,
    geom_text,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_fill_manual,
    scale_size_identity,
    theme,
    theme_void,
)
from scipy.optimize import minimize


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
GAP = 0.06  # padding between sibling circles, as a share of the smaller radius
LABEL_BAND = 0.34  # extra room above a parent's children for its label, as a share of their enclosure
LABEL_MIN_SHARE = 0.03  # leaves whose area is below this share of the total stay unlabeled

# Columns
ID = "id"  # role: id
PARENT = "parent"  # role: parent
VALUE = "value"  # role: value
LABEL = "label"  # role: label

# Data: investment portfolio, asset classes and their holdings
df = pd.DataFrame(
    {
        ID: [
            "root",
            "stocks",
            "bonds",
            "realestate",
            "tech",
            "healthcare",
            "finance",
            "corp",
            "govt",
            "commercial",
            "residential",
        ],
        PARENT: [
            None,
            "root",
            "root",
            "root",
            "stocks",
            "stocks",
            "stocks",
            "bonds",
            "bonds",
            "realestate",
            "realestate",
        ],
        VALUE: [None, None, None, None, 180000, 150000, 120000, 150000, 100000, 120000, 60000],
        LABEL: [
            "Portfolio",
            "Stocks",
            "Bonds",
            "Real Estate",
            "Tech",
            "Healthcare",
            "Finance",
            "Corporate",
            "Government",
            "Commercial",
            "Residential",
        ],
    }
)

# Plot: packing is computed from df, drawing reads only the derived tables
# Leaves without a value cannot be drawn: drop them until every leaf has one
tree = df.copy()
while True:
    is_parent = tree[ID].isin(tree[PARENT])
    undrawable = ~is_parent & tree[VALUE].isna() & tree[PARENT].notna()
    if not undrawable.any():
        break
    tree = tree[~undrawable]

children = {}
for node_id, parent_id in zip(tree[ID], tree[PARENT], strict=True):
    if pd.notna(parent_id):
        children.setdefault(parent_id, []).append(node_id)
root_id = tree.loc[tree[PARENT].isna(), ID].iloc[0]
leaf_value = dict(zip(tree[ID], tree[VALUE], strict=True))


def enclose(centers, radii):
    """Smallest circle around the given circles, found by minimising the farthest reach."""
    start = np.average(centers, axis=0, weights=radii**2)

    def farthest(point):
        return (np.linalg.norm(centers - point, axis=1) + radii).max()

    best = minimize(farthest, start, method="Nelder-Mead", options={"xatol": 1e-9, "fatol": 1e-9})
    return best.x, best.fun


def pack(radii):
    """Place circles tangent to each other, each new one at the free spot nearest the group's centre."""
    order = np.argsort(-radii)
    placed = []
    for idx in order:
        r = radii[idx]
        if not placed:
            placed.append((idx, 0.0, 0.0))
            continue
        pts = np.array([[x, y] for _, x, y in placed])
        rs = np.array([radii[i] for i, _, _ in placed])
        best, best_cost = None, np.inf
        if len(placed) == 1:
            candidates = [(rs[0] + r + GAP * min(rs[0], r), 0.0)]
        else:
            candidates = []
            for a in range(len(placed)):
                for b in range(a + 1, len(placed)):
                    ra, rb = rs[a] + r + GAP * min(rs[a], r), rs[b] + r + GAP * min(rs[b], r)
                    delta = pts[b] - pts[a]
                    dist = np.linalg.norm(delta)
                    if dist > ra + rb or dist < abs(ra - rb) or dist == 0:
                        continue
                    along = (ra**2 - rb**2 + dist**2) / (2 * dist)
                    h = np.sqrt(max(ra**2 - along**2, 0))
                    base = pts[a] + along * delta / dist
                    normal = np.array([-delta[1], delta[0]]) / dist
                    candidates += [tuple(base + h * normal), tuple(base - h * normal)]
        if not candidates:
            candidates = [(pts[:, 0].max() + rs.max() + r, 0.0)]
        centroid = np.average(pts, axis=0, weights=rs**2)
        for cx, cy in candidates:
            gap_ok = np.all(np.linalg.norm(pts - [cx, cy], axis=1) >= rs + r + GAP * np.minimum(rs, r) - 1e-9)
            if not gap_ok:
                continue
            cost = np.hypot(cx - centroid[0], cy - centroid[1])
            if cost < best_cost:
                best, best_cost = (cx, cy), cost
        placed.append((idx, best[0], best[1]))
    out = np.zeros((len(radii), 2))
    for idx, x, y in placed:
        out[idx] = (x, y)
    return out


# Layout in packing units: a leaf's radius is sqrt(value), so areas stay proportional across the whole chart
offset = {}  # id -> centre relative to its parent's centre
radius_of = {}  # id -> radius
label_dy = {}  # parent id -> label height above its centre


def build(node_id):
    """Return the radius of a node and record where its children sit relative to it."""
    kids = children.get(node_id)
    if not kids:
        radius_of[node_id] = float(np.sqrt(leaf_value[node_id]))
        return radius_of[node_id]
    radii = np.array([build(k) for k in kids])
    centers = pack(radii)
    centre, reach = enclose(centers, radii)
    is_root = node_id == root_id
    # A non-root parent keeps a band above its children for its own label
    shift = 0.0 if is_root else LABEL_BAND * reach
    pad = reach * (0.08 if is_root else 0.04)
    for k, c in zip(kids, centers - centre, strict=True):
        offset[k] = (c[0], c[1] - shift)
    radius_of[node_id] = reach + pad + shift
    label_dy[node_id] = reach + pad / 2
    return radius_of[node_id]


root_radius = build(root_id)

# Absolute positions: walk down from the root
absolute = {root_id: (0.0, 0.0, 0)}
stack = [root_id]
while stack:
    parent_node = stack.pop()
    px, py, depth = absolute[parent_node]
    for kid in children.get(parent_node, []):
        absolute[kid] = (px + offset[kid][0], py + offset[kid][1], depth + 1)
        stack.append(kid)

# Root radius becomes 1
labels = dict(zip(tree[ID], tree[LABEL], strict=True))
total_value = tree[VALUE].sum()
n_points = 96
angles = np.linspace(0, 2 * np.pi, n_points)
polygon_rows = []
label_rows = []
for node_id, (cx, cy, depth) in sorted(absolute.items(), key=lambda item: item[1][2]):
    r = radius_of[node_id] / root_radius
    cx, cy = cx / root_radius, cy / root_radius
    polygon_rows.append(
        pd.DataFrame({"node": node_id, "x": cx + r * np.cos(angles), "y": cy + r * np.sin(angles), "depth": depth})
    )
    if node_id in children and depth > 0:
        label_rows.append({"x": cx, "y": cy + label_dy[node_id] / root_radius, "text": labels[node_id], "size": 4.6})
    elif node_id not in children and leaf_value[node_id] / total_value >= LABEL_MIN_SHARE:
        label_rows.append({"x": cx, "y": cy, "text": labels[node_id], "size": 3.6})

df_circles = pd.concat(polygon_rows, ignore_index=True)
df_circles["order"] = np.tile(np.arange(n_points), len(polygon_rows))
df_labels = pd.DataFrame(label_rows, columns=["x", "y", "text", "size"])

depth_levels = sorted(df_circles["depth"].unique())
level_names = {0: "Root", 1: "Asset class", 2: "Holding"}
legend_labels = [level_names.get(d, f"Level {d}") for d in depth_levels]

plot = (
    ggplot()
    + geom_polygon(
        df_circles, aes(x="x", y="y", group="node", fill="factor(depth)"), color=INK_SOFT, size=0.3, alpha=0.88
    )
    + geom_text(
        df_labels, aes(x="x", y="y", label="text", size="size"), color=INK, fontweight="bold", show_legend=False
    )
    + scale_fill_manual(values=IMPRINT_PALETTE, labels=legend_labels, name="Hierarchy level")
    + scale_size_identity()
    + coord_fixed(ratio=1)
    + labs(title="circlepacking-basic · python · plotnine · anyplot.ai")
    + theme_void()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        figure_size=(6, 6),
        plot_title=element_text(size=12, ha="center", weight="bold", color=INK, margin={"t": 14, "b": 8}),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=9, color=INK_SOFT),
        legend_title=element_text(size=10, weight="bold", color=INK),
        legend_position="bottom",
        legend_direction="horizontal",
    )
    + guides(fill=guide_legend(override_aes={"size": 0.5}))
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in", verbose=False)
