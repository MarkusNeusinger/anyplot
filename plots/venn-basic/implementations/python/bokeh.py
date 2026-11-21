"""anyplot.ai
venn-basic: Venn Diagram
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
"""

import os
import time
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Label
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per set in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SETS = "Sets"  # role: set_labels
SIZE = "Size"  # role: set_sizes
OVERLAP = "Sets in overlap"  # role: intersections

# Data: replace this block with your own table, for example df = pd.read_csv("sets.csv")
# One row per set or intersection, in the order A, B, C, A+B, A+C, B+C, A+B+C. Sizes are inclusive
# (the A+B row counts the A+B+C elements too); the label of an intersection row is free text.
df = pd.DataFrame(
    {
        SETS: [
            "Product A",
            "Product B",
            "Product C",
            "Product A + Product B",
            "Product A + Product C",
            "Product B + Product C",
            "Product A + Product B + Product C",
        ],
        SIZE: [100, 80, 60, 30, 20, 25, 10],
        OVERLAP: [1, 1, 1, 2, 2, 2, 3],
    }
)

# Plot: reads only df and the constants above
# Rows are ordered singles, then pairs, then the triple, each group in combination order
table = df.sort_values(OVERLAP, kind="stable")
k = min(3, int(np.log2(len(table) + 1)))  # a table of 2**k - 1 rows describes k sets
names = [str(s) for s in table[SETS].iloc[:k]]
regions = [frozenset(c) for r in range(1, k + 1) for c in combinations(range(k), r)]
inclusive = dict(zip(regions, np.nan_to_num(table[SIZE].to_numpy(dtype=float)[: len(regions)]), strict=False))

# Exclusive size of every region: inclusion-exclusion over the supersets of its member sets
exclusive = {s: sum((-1) ** (len(t) - len(s)) * inclusive.get(t, 0) for t in regions if s <= t) for s in regions}

# Circle areas follow the set sizes; the distance of each pair follows its overlap area
radii = [np.sqrt(inclusive[frozenset([i])] / np.pi) for i in range(k)]


def lens_area(r1, r2, d):
    if d >= r1 + r2:
        return 0.0
    if d <= abs(r1 - r2):
        return np.pi * min(r1, r2) ** 2
    a1 = r1**2 * np.arccos((d**2 + r1**2 - r2**2) / (2 * d * r1))
    a2 = r2**2 * np.arccos((d**2 + r2**2 - r1**2) / (2 * d * r2))
    return a1 + a2 - 0.5 * np.sqrt((-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2))


def pair_distance(i, j):
    target = inclusive.get(frozenset([i, j]), 0)
    lo, hi = abs(radii[i] - radii[j]), radii[i] + radii[j]
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if lens_area(radii[i], radii[j], mid) > target else (lo, mid)
    return (lo + hi) / 2


centers = [np.array([0.0, 0.0])]
if k > 1:
    centers.append(np.array([pair_distance(0, 1), 0.0]))
if k > 2:
    d01, d02, d12 = pair_distance(0, 1), pair_distance(0, 2), pair_distance(1, 2)
    cx = (d02**2 - d12**2 + d01**2) / (2 * d01)
    cy = np.sqrt(max(d02**2 - cx**2, 0.0))
    centers.append(np.array([cx, cy]))
centers = np.array(centers)
centers -= centers.mean(axis=0)
radii = np.array(radii)

# Region label anchors: the point of each region farthest from any circle outline
pad = 0.3 * radii.max()
x_lo, x_hi = (centers[:, 0] - radii).min() - pad, (centers[:, 0] + radii).max() + pad
y_lo, y_hi = (centers[:, 1] - radii).min() - pad, (centers[:, 1] + radii).max() + 1.6 * pad
gx, gy = np.meshgrid(np.linspace(x_lo, x_hi, 900), np.linspace(y_lo, y_hi, 900))
dist = np.stack([np.hypot(gx - c[0], gy - c[1]) for c in centers])
inside = dist < radii[:, None, None]
edge_gap = np.abs(dist - radii[:, None, None]).min(axis=0)
anchors = {}
for s in regions:
    member = np.array([i in s for i in range(k)])
    mask = (inside == member[:, None, None]).all(axis=0)
    if mask.any():
        idx = np.argmax(np.where(mask, edge_gap, -1.0))
        anchors[s] = (gx.flat[idx], gy.flat[idx])

# Equal data scale on both axes: widen the shorter span to the aspect of the inner plot area
INNER_W, INNER_H = 3200 - 120, 1800 - 170
x_mid, y_mid = (x_lo + x_hi) / 2, (y_lo + y_hi) / 2
scale = max((x_hi - x_lo) / INNER_W, (y_hi - y_lo) / INNER_H)
x_lo, x_hi = x_mid - scale * INNER_W / 2, x_mid + scale * INNER_W / 2
y_lo, y_hi = y_mid - scale * INNER_H / 2, y_mid + scale * INNER_H / 2

# Figure
circles = ColumnDataSource(
    {"x": centers[:, 0], "y": centers[:, 1], "r": radii, "color": [IMPRINT_PALETTE[i] for i in range(k)]}
)
p = figure(
    width=3200,
    height=1800,
    title="venn-basic · python · bokeh · anyplot.ai",
    x_range=(x_lo, x_hi),
    y_range=(y_lo, y_hi),
    toolbar_location=None,
    min_border_top=110,
    min_border_bottom=60,
    min_border_left=60,
    min_border_right=60,
)
p.circle(
    x="x",
    y="y",
    radius="r",
    source=circles,
    fill_color="color",
    fill_alpha=0.35,
    line_color="color",
    line_alpha=1.0,
    line_width=5,
)

# Set labels sit outside their circle, pushed away from the middle of the diagram
for i, name in enumerate(names):
    away = centers[i] - centers.mean(axis=0)
    away = away / np.linalg.norm(away) if np.linalg.norm(away) > 1e-9 else np.array([0.0, 1.0])
    gap = 0.07 * radii.max()
    ax, ay = centers[i] + away * (radii[i] + gap)
    align = "right" if away[0] < -0.35 else "left" if away[0] > 0.35 else "center"
    p.add_layout(
        Label(
            x=ax,
            y=ay + (0.28 if away[1] > 0 else 0.1) * radii.max(),
            text=name,
            text_font_size="36pt",
            text_font_style="bold",
            text_align=align,
            text_baseline="middle",
            text_color=INK,
        )
    )
    p.add_layout(
        Label(
            x=ax,
            y=ay + (0.1 if away[1] > 0 else -0.1) * radii.max(),
            text=f"n = {inclusive[frozenset([i])]:g}",
            text_font_size="28pt",
            text_align=align,
            text_baseline="middle",
            text_color=INK_SOFT,
        )
    )

# Exclusive counts inside their regions
for s, (rx, ry) in anchors.items():
    p.add_layout(
        Label(
            x=rx,
            y=ry,
            text=f"{exclusive[s]:g}",
            text_font_size="40pt",
            text_font_style="bold",
            text_align="center",
            text_baseline="middle",
            text_color=INK,
        )
    )

# Style
p.title.text_font_size = "50pt"
p.title.align = "center"
p.title.text_color = INK
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
W, H = 3200, 1800
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)

driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
