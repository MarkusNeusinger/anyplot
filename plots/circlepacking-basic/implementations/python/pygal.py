"""anyplot.ai
circlepacking-basic: Circle Packing Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
"""

import math
import os

import cairosvg
import pandas as pd
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: one position per sector, in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# pygal's Style carries the theme tokens; the SVG below reads them back from it
style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE),
)

# Constants
PAD = 0.14  # gap between sibling circles and inside a parent, as a share of the mean leaf radius
LABEL_MIN_SIZE = 24  # leaf labels smaller than this many px are left to the tooltip
LEAF_INK = "#1A1A17"  # leaf fills are mid-tone in both themes, so dark text reads on both

# Columns: set these to your table's column names
NODE = "id"  # role: id
PARENT = "parent"  # role: parent
BUDGET = "Budget (million USD)"  # role: value
LABEL = "label"  # role: label

# Data: replace this block with your own table, for example df = pd.read_csv("tree.csv")
df = pd.DataFrame(
    [
        ("city", None, None, "Riverton"),
        ("transport", "city", None, "Transport"),
        ("health", "city", None, "Health"),
        ("education", "city", None, "Education"),
        ("safety", "city", None, "Public safety"),
        ("parks", "city", None, "Parks"),
        ("roads", "transport", 180, "Roads"),
        ("transit", "transport", 150, "Transit"),
        ("cycling", "transport", 30, "Cycling"),
        ("hospitals", "health", 210, "Hospitals"),
        ("clinics", "health", 90, "Clinics"),
        ("publichealth", "health", 45, "Prevention"),
        ("schools", "education", 240, "Schools"),
        ("libraries", "education", 40, "Libraries"),
        ("adult", "education", 25, "Adult ed."),
        ("police", "safety", 130, "Police"),
        ("fire", "safety", 100, "Fire"),
        ("emergency", "safety", 35, "Dispatch"),
        ("maintenance", "parks", 60, "Upkeep"),
        ("recreation", "parks", 35, "Recreation"),
        ("trees", "parks", 18, "Trees"),
    ],
    columns=[NODE, PARENT, BUDGET, LABEL],
)

# Plot: reads only df and the constants above
# Rows are addressed by position, so repeated ids or missing values cannot break the lookups
ids = df[NODE].tolist()
values = pd.to_numeric(df[BUDGET], errors="coerce").tolist()
names = [str(n) if pd.notna(n) else "" for n in df[LABEL].tolist()]


def escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


kids_of = {}
for row, parent_id in enumerate(df[PARENT].tolist()):
    if pd.notna(parent_id):
        kids_of.setdefault(parent_id, []).append(row)
root_row = int(df[PARENT].isna().to_numpy().argmax())
leaf_values = [v for row, v in enumerate(values) if ids[row] not in kids_of and pd.notna(v)]
mean_leaf_r = math.sqrt(sum(leaf_values) / len(leaf_values)) if leaf_values else 1.0


def overlaps(x, y, r, placed):
    return any(math.hypot(x - px, y - py) < r + pr - 1e-6 for px, py, pr in placed)


def tangent_points(a, b, r):
    """Centres of a circle of radius r that touches circles a and b."""
    (ax, ay, ar), (bx, by, br) = a, b
    d = math.hypot(bx - ax, by - ay)
    da, db = ar + r, br + r
    if d == 0 or d > da + db or d < abs(da - db):
        return []
    t = (da**2 - db**2 + d**2) / (2 * d)
    h = math.sqrt(max(da**2 - t**2, 0))
    mx, my = ax + t * (bx - ax) / d, ay + t * (by - ay) / d
    ox, oy = h * (by - ay) / d, h * (bx - ax) / d
    return [(mx + ox, my - oy), (mx - ox, my + oy)]


def enclose(circles):
    """Centre and radius of a circle enclosing all circles (iterative minimax)."""
    cx = sum(x for x, _, _ in circles) / len(circles)
    cy = sum(y for _, y, _ in circles) / len(circles)
    step = max(r for _, _, r in circles)
    for _ in range(3000):
        fx, fy, _ = max(circles, key=lambda c: math.hypot(c[0] - cx, c[1] - cy) + c[2])
        dist = math.hypot(fx - cx, fy - cy)
        if dist > 0:
            cx += (fx - cx) / dist * step
            cy += (fy - cy) / dist * step
        step *= 0.997
    return cx, cy, max(math.hypot(x - cx, y - cy) + r for x, y, r in circles)


def pack(radii):
    """Greedy front packing: each circle goes to the free tangent spot closest to the cluster centre."""
    order = sorted(range(len(radii)), key=lambda i: -radii[i])
    placed = {order[0]: (0.0, 0.0, radii[order[0]])}
    if len(order) > 1:
        placed[order[1]] = (radii[order[0]] + radii[order[1]], 0.0, radii[order[1]])
    for i in order[2:]:
        r = radii[i]
        circles = list(placed.values())
        cx = sum(c[0] for c in circles) / len(circles)
        cy = sum(c[1] for c in circles) / len(circles)
        best = None
        for a in range(len(circles)):
            for b in range(a + 1, len(circles)):
                for x, y in tangent_points(circles[a], circles[b], r):
                    if not overlaps(x, y, r, circles):
                        score = math.hypot(x - cx, y - cy) + r
                        if best is None or score < best[0]:
                            best = (score, x, y)
        placed[i] = (best[1], best[2], r) if best else (cx + 4 * r * len(circles), cy, r)
    return [placed[i] for i in range(len(radii))]


def layout(row):
    """Radius and child offsets of a subtree, centred on its own origin; leaf area is proportional to value."""
    kids = kids_of.get(ids[row], [])
    if not kids:
        return {"row": row, "r": math.sqrt(values[row]) if pd.notna(values[row]) else 0.0, "kids": []}
    subs = [layout(k) for k in kids]
    gap = PAD * mean_leaf_r
    spots = pack([s["r"] + gap / 2 for s in subs])
    cx, cy, radius = enclose(spots)
    for s, (x, y, _) in zip(subs, spots, strict=True):
        s["dx"], s["dy"] = x - cx, y - cy
    return {"row": row, "r": radius + gap, "kids": subs}


tree = layout(root_row)

# Canvas: square, the root circle fills the area below the title
SIZE = 2400
CENTER_X, CENTER_Y = SIZE / 2, SIZE / 2 + 50
scale = (SIZE / 2 - 160) / max(tree["r"], 1e-9)

circles = []  # (depth, x, y, r, row, sector index)


def flatten(sub, x, y, depth, sector):
    circles.append((depth, x, y, sub["r"] * scale, sub["row"], sector))
    for index, k in enumerate(sub["kids"]):
        flatten(k, x + k["dx"] * scale, y + k["dy"] * scale, depth + 1, index if depth == 0 else sector)


flatten(tree, CENTER_X, CENTER_Y, 0, -1)

# SVG, written as text: pygal has no circle-packing chart, so the shapes are plain SVG
title = "Riverton city budget · circlepacking-basic · python · pygal · anyplot.ai"
title_size = round(52 * min(1.0, 67 / len(title)))
parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}" viewBox="0 0 {SIZE} {SIZE}">',
    f'<rect width="{SIZE}" height="{SIZE}" fill="{style.background}"/>',
    f'<text x="{SIZE / 2}" y="110" text-anchor="middle" font-family="sans-serif" font-weight="bold" '
    f'font-size="{title_size}px" fill="{style.foreground_strong}">{escape(title)}</text>',
]
for depth, x, y, r, row, sector in circles:
    if r <= 0:
        continue
    if depth == 0:
        fill, opacity, stroke, stroke_w = INK_MUTED, 0.08, INK_SOFT, 4
    elif depth == 1:
        fill, opacity, stroke, stroke_w = IMPRINT_PALETTE[sector], 0.22, INK_SOFT, 4
    else:
        fill, opacity, stroke, stroke_w = IMPRINT_PALETTE[sector], 0.9, PAGE_BG, 2
    tip = names[row] + (f": {values[row]:.0f}" if pd.notna(values[row]) else "")
    parts.append(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" fill-opacity="{opacity}" '
        f'stroke="{stroke}" stroke-width="{stroke_w}"><title>{escape(tip)}</title></circle>'
    )


def text(x, y, content, size, fill, weight="bold", halo=False):
    """One text element; a halo is a separate stroked copy underneath because cairosvg ignores paint-order."""
    attrs = f'x="{x:.1f}" y="{y:.1f}" text-anchor="middle" font-family="sans-serif" font-size="{size:.0f}px"'
    out = ""
    if halo:
        out += f'<text {attrs} font-weight="{weight}" fill="none" stroke="{PAGE_BG}" stroke-width="12" stroke-linejoin="round">{escape(content)}</text>'
    return out + f'<text {attrs} font-weight="{weight}" fill="{fill}">{escape(content)}</text>'


for depth, x, y, r, row, _sector in circles:
    if r <= 0:
        continue
    if depth == 1:
        # The sector name sits above the circle, or below it for sectors in the lower half
        upper = y < CENTER_Y
        parts.append(text(x, y - r - 18 if upper else y + r + 52, names[row], 46, INK, halo=True))
    elif depth == 2:
        size = min(54, 2 * r * 0.78 / (0.66 * max(len(names[row]), 1)))
        if size >= LABEL_MIN_SIZE:
            parts.append(text(x, y + size * 0.05, names[row], size, LEAF_INK))
            parts.append(text(x, y + size * 1.05, f"{values[row]:.0f}", size * 0.78, LEAF_INK, weight="normal"))

parts.append(text(SIZE / 2, SIZE - 40, f"Circle area = {BUDGET}; color = sector", 34, INK_SOFT, weight="normal"))
parts.append("</svg>")
svg_text = "".join(parts)

with open(f"plot-{THEME}.html", "w") as f:
    f.write(svg_text)
cairosvg.svg2png(bytestring=svg_text.encode("utf-8"), write_to=f"plot-{THEME}.png")
