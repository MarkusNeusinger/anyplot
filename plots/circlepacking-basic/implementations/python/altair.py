"""anyplot.ai
circlepacking-basic: Circle Packing Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image
from scipy.optimize import minimize


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per department in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
ID = "id"  # role: id
PARENT = "parent"  # role: parent
VALUE = "Budget (thousand USD)"  # role: value
LABEL = "label"  # role: label

# Data: replace this block with your own table, for example df = pd.read_csv("budget.csv")
# One row per node; the root has no parent, only leaf rows carry a value.
df = pd.DataFrame(
    [
        ("company", None, np.nan, "Company"),
        ("eng", "company", np.nan, "Engineering"),
        ("mkt", "company", np.nan, "Marketing"),
        ("ops", "company", np.nan, "Operations"),
        ("sales", "company", np.nan, "Sales"),
        ("eng-backend", "eng", 180, "Backend"),
        ("eng-frontend", "eng", 150, "Frontend"),
        ("eng-mobile", "eng", 120, "Mobile"),
        ("eng-devops", "eng", 90, "DevOps"),
        ("mkt-digital", "mkt", 100, "Digital"),
        ("mkt-content", "mkt", 80, "Content"),
        ("mkt-brand", "mkt", 60, "Brand"),
        ("ops-support", "ops", 70, "Support"),
        ("ops-hr", "ops", 50, "HR"),
        ("ops-admin", "ops", 40, "Admin"),
        ("sales-enterprise", "sales", 130, "Enterprise"),
        ("sales-smb", "sales", 85, "SMB"),
        ("sales-partners", "sales", 55, "Partners"),
    ],
    columns=[ID, PARENT, VALUE, LABEL],
)

# Plot: reads only df and the constants above
GAP = 0.04  # space between sibling circles, as a share of the largest sibling radius
PAD = 0.06  # space between a parent's edge and its children, same unit
VIEW = 500  # side of the square view in pixels
MIN_LABEL_PX = 22  # leaves smaller than this radius stay unlabeled


def pack(radii):
    """Pack circles of the given radii; returns centers and the enclosing radius around (0, 0)."""
    gap = GAP * max(radii)
    centers = [(0.0, 0.0)]
    if len(radii) > 1:
        centers.append((radii[0] + radii[1] + gap, 0.0))
    for k in range(2, len(radii)):
        r = radii[k]
        weights = np.array(radii[:k]) ** 2
        mean = np.average(np.array(centers), axis=0, weights=weights)
        best, best_cost = None, np.inf
        for a in range(k):
            for b in range(a + 1, k):
                (ax, ay), (bx, by) = centers[a], centers[b]
                ra, rb = radii[a] + r + gap, radii[b] + r + gap
                d = np.hypot(bx - ax, by - ay)
                if d > ra + rb or d < abs(ra - rb) or d == 0:
                    continue
                along = (ra**2 - rb**2 + d**2) / (2 * d)
                h = np.sqrt(max(ra**2 - along**2, 0.0))
                mx, my = ax + along * (bx - ax) / d, ay + along * (by - ay) / d
                for sign in (1, -1):
                    cand = (mx - sign * h * (by - ay) / d, my + sign * h * (bx - ax) / d)
                    clear = all(
                        np.hypot(cand[0] - cx, cand[1] - cy) >= r + radii[i] + gap - 1e-9
                        for i, (cx, cy) in enumerate(centers)
                    )
                    cost = np.hypot(cand[0] - mean[0], cand[1] - mean[1])
                    if clear and cost < best_cost:
                        best, best_cost = cand, cost
        centers.append(best)
    centers = np.array(centers)
    radii_arr = np.array(radii)

    def reach_of(point):
        return (np.hypot(*(centers - point).T) + radii_arr).max()

    start = np.average(centers, axis=0, weights=radii_arr**2)
    middle = minimize(reach_of, start, method="Nelder-Mead", options={"xatol": 1e-9, "fatol": 1e-9}).x
    return centers - middle, float(reach_of(middle) + PAD * max(radii))


# Groups are the parents of the valued rows; labels come from their own rows when present
valued = df[df[VALUE].notna()]
names = dict(zip(df[ID], df[LABEL], strict=True))
root_rows_df = df[df[PARENT].isna()]
root_label = root_rows_df[LABEL].iloc[0] if len(root_rows_df) else ""

# Leaves: radius from the square root of the value, so area encodes value
packed = []
for top_id in valued[PARENT].drop_duplicates():
    leaves = valued[valued[PARENT] == top_id]
    offsets, enclosing = pack(np.sqrt(leaves[VALUE].to_numpy(dtype=float)).tolist())
    packed.append((names.get(top_id, top_id), leaves, offsets, enclosing))

top_offsets, root_radius = pack([enclosing for *_, enclosing in packed])
group_names = [name for name, *_ in packed]

ppu = (VIEW / 2) / (root_radius * 1.03)  # pixels per layout unit
cols = ["x", "y", "r", "name", "group", "value"]
root_rows = [(0.0, 0.0, root_radius, root_label, "", np.nan)]
group_rows, leaf_rows = [], []
for (name, leaves, offsets, enclosing), (gx, gy) in zip(packed, top_offsets, strict=True):
    group_rows.append((gx, gy, enclosing, name, name, leaves[VALUE].sum()))
    for (dx, dy), (_, leaf) in zip(offsets, leaves.iterrows(), strict=True):
        leaf_rows.append((gx + dx, gy + dy, np.sqrt(leaf[VALUE]), leaf[LABEL], name, leaf[VALUE]))


def to_frame(rows):
    frame = pd.DataFrame(rows, columns=cols)
    frame["size"] = 4 * (frame["r"] * ppu) ** 2  # Vega circles take the area of their bounding square in px^2
    frame["text"] = [f"{n}\n{v:g}" for n, v in zip(frame["name"], frame["value"], strict=True)]
    return frame


root_nodes, group_nodes, leaf_nodes = to_frame(root_rows), to_frame(group_rows), to_frame(leaf_rows)

x_enc = alt.X("x:Q", axis=None, scale=alt.Scale(domain=[-VIEW / 2 / ppu, VIEW / 2 / ppu], nice=False))
y_enc = alt.Y("y:Q", axis=None, scale=alt.Scale(domain=[-VIEW / 2 / ppu, VIEW / 2 / ppu], nice=False))
size_enc = alt.Size("size:Q", scale=None, legend=None)
group_legend = alt.Legend(title=None, orient="bottom", direction="horizontal", symbolOpacity=0.6)
group_scale = alt.Scale(domain=group_names, range=IMPRINT_PALETTE)
tooltip = [alt.Tooltip("name:N", title="Node"), alt.Tooltip("value:Q", title=VALUE)]

root_layer = (
    alt.Chart(root_nodes)
    .mark_circle(color=ELEVATED_BG, stroke=INK_SOFT, strokeWidth=2.5)
    .encode(x=x_enc, y=y_enc, size=size_enc)
)
group_layer = (
    alt.Chart(group_nodes)
    .mark_circle(fillOpacity=0.22, stroke=INK_SOFT, strokeWidth=1.5)
    .encode(
        x=x_enc,
        y=y_enc,
        size=size_enc,
        color=alt.Color("group:N", scale=group_scale, legend=group_legend),
        tooltip=tooltip,
    )
)
leaf_layer = (
    alt.Chart(leaf_nodes)
    .mark_circle(fillOpacity=0.6, stroke=INK_SOFT, strokeWidth=1.2)
    .encode(
        x=x_enc,
        y=y_enc,
        size=size_enc,
        color=alt.Color("group:N", scale=group_scale, sort=None, legend=group_legend),
        tooltip=tooltip,
    )
)
label_layer = (
    alt.Chart(leaf_nodes[leaf_nodes["r"] * ppu >= MIN_LABEL_PX])
    .mark_text(color=INK, fontWeight="bold", fontSize=9, lineBreak="\n")
    .encode(x=x_enc, y=y_enc, text="text:N")
)

# Style
title = "circlepacking-basic · python · altair · anyplot.ai"
chart = (
    alt.layer(root_layer, group_layer, leaf_layer, label_layer)
    .properties(
        width=VIEW,
        height=VIEW,
        background=PAGE_BG,
        padding={"left": 8, "right": 8, "top": 8, "bottom": 8},
        title=alt.Title(
            title,
            subtitle=f"Circle area proportional to {VALUE}",
            fontSize=18,
            subtitleFontSize=12,
            anchor="middle",
            color=INK,
            subtitleColor=INK_SOFT,
        ),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_legend(labelColor=INK_SOFT, labelFontSize=12, symbolSize=180)
)

# Save: pad up to the 2400 x 2400 square canvas, never crop
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
TARGET = 2400
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET or img.height > TARGET:
    raise SystemExit(f"altair produced {img.width}x{img.height}, exceeds {TARGET}x{TARGET}; shrink VIEW")
canvas = Image.new("RGB", (TARGET, TARGET), PAGE_BG)
canvas.paste(img, ((TARGET - img.width) // 2, (TARGET - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
