"""anyplot.ai
bubble-packed: Basic Packed Bubble Chart
Library: bokeh 3.10.2 | Python 3.14.10
Quality: pending | Updated: 2026-11-27
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, LabelSet, Legend, LegendItem
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: tier colors follow the canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
# Label color per palette position, chosen by fill luminance (fills do not change between themes)
LABEL_ON = ["#FFFFFF", "#1A1A17", "#FFFFFF", "#1A1A17", "#FFFFFF", "#1A1A17", "#FFFFFF", "#1A1A17"]

# Constants
SEED = 42
W, H = 2400, 2400  # square canvas, also the packing space
MAX_R = 310  # radius of the largest circle in packing units
PAD = 12  # gap between circles in packing units
MARGIN = 80  # empty border around the cluster in packing units

# Columns: set these to your table's column names
DEPARTMENT = "Department"  # role: label
BUDGET = "Budget (million USD)"  # role: value
TIER = "Spending tier"  # role: group

# Data: replace this block with your own table, for example df = pd.read_csv("budgets.csv")
departments = [
    "Engineering",
    "Marketing",
    "Sales",
    "Operations",
    "HR",
    "Finance",
    "R&D",
    "Legal",
    "IT",
    "Customer Support",
    "Product",
    "Design",
    "QA",
    "Data Science",
    "Security",
]
budgets = [45, 32, 38, 25, 12, 18, 42, 8, 22, 15, 28, 14, 10, 20, 6]
df = pd.DataFrame(
    {
        DEPARTMENT: departments,
        BUDGET: budgets,
        TIER: [">$35M" if b > 35 else "$20–$35M" if b >= 20 else "$10–$19M" if b >= 10 else "<$10M" for b in budgets],
    }
)

# Plot: reads only df and the constants above
n = len(df)
vals = df[BUDGET].to_numpy(dtype=float)
# Area-scaled radii (sqrt) for accurate visual perception
radii = np.sqrt(vals / np.nanmax(vals)) * MAX_R

# Force-directed circle packing in the canvas coordinate space
rng = np.random.RandomState(SEED)
center = np.array([W / 2.0, H / 2.0])
pos = center + (rng.rand(n, 2) - 0.5) * 400

for step in range(600):
    pos += (center - pos) * 0.012
    total_shift = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            d = pos[j] - pos[i]
            dist = np.linalg.norm(d) + 1e-6
            gap = radii[i] + radii[j] + PAD
            if dist < gap:
                s = d / dist * (gap - dist) * 0.5
                pos[i] -= s
                pos[j] += s
                total_shift += gap - dist
    pos[:, 0] = np.clip(pos[:, 0], radii + 50, W - radii - 50)
    pos[:, 1] = np.clip(pos[:, 1], radii + 50, H - radii - 50)
    if step > 200 and total_shift < 1.0:
        break

# Recenter cluster
x_lo = (pos[:, 0] - radii).min()
x_hi = (pos[:, 0] + radii).max()
y_lo = (pos[:, 1] - radii).min()
y_hi = (pos[:, 1] + radii).max()
pos[:, 0] += (W - (x_lo + x_hi)) / 2
pos[:, 1] += (H - (y_lo + y_hi)) / 2

# Equal x/y range so data-unit circles render as true circles on the square canvas
x_lo = (pos[:, 0] - radii).min() - MARGIN
x_hi = (pos[:, 0] + radii).max() + MARGIN
y_lo = (pos[:, 1] - radii).min() - MARGIN
y_hi = (pos[:, 1] + radii).max() + MARGIN
cx = (x_lo + x_hi) / 2
cy = (y_lo + y_hi) / 2
half = max(x_hi - x_lo, y_hi - y_lo) / 2
xr = (cx - half, cx + half)
yr = (cy - half, cy + half)

circles = df.assign(x=pos[:, 0], y=pos[:, 1], radius=radii)
# Tiers in the order of their largest member, so the legend reads from big to small
tiers = list(circles.groupby(TIER, sort=False)[BUDGET].max().sort_values(ascending=False).index)

p = figure(
    width=W,
    height=H,
    title="Department Budgets by Spending Tier · bubble-packed · python · bokeh · anyplot.ai",
    x_range=xr,
    y_range=yr,
    tools="",
    toolbar_location=None,
)

renderers = []
legend_items = []
for t, tier_name in enumerate(tiers):
    src = ColumnDataSource(circles[circles[TIER] == tier_name])
    r = p.circle(
        x="x",
        y="y",
        radius="radius",
        source=src,
        fill_color=IMPRINT_PALETTE[t],
        fill_alpha=0.90,
        line_color=PAGE_BG,
        line_width=4,
    )
    renderers.append(r)
    # Screen-size marker for the legend key; the data-unit circle would draw a speck there
    key = p.scatter(
        x=[xr[0] - 10 * half],
        y=[yr[0] - 10 * half],
        size=44,
        marker="circle",
        fill_color=IMPRINT_PALETTE[t],
        fill_alpha=0.90,
        line_color=PAGE_BG,
    )
    legend_items.append(LegendItem(label=str(tier_name), renderers=[key]))

# Adaptive label sizes by radius bracket, as shares of the largest radius
# y_offset is in screen pixels, separating the name (above) and the value (below)
brackets = [
    (0.726, float("inf"), "34pt", "28pt", 24),
    (0.435, 0.726, "26pt", "22pt", 18),
    (0, 0.435, "20pt", "16pt", 14),
]

for lo, hi, name_fs, val_fs, y_off in brackets:
    for t, tier_name in enumerate(tiers):
        text_color = LABEL_ON[t]
        rel = circles["radius"] / circles["radius"].max()
        rows = circles[(circles[TIER] == tier_name) & (rel >= lo) & (rel < hi)]
        if rows.empty:
            continue
        src = ColumnDataSource(
            {"x": rows["x"], "y": rows["y"], "name": rows[DEPARTMENT], "val": [f"${b:g}M" for b in rows[BUDGET]]}
        )
        p.add_layout(
            LabelSet(
                x="x",
                y="y",
                text="name",
                source=src,
                text_align="center",
                text_baseline="middle",
                text_font_size=name_fs,
                text_color=text_color,
                text_font_style="bold",
                y_offset=y_off,
            )
        )
        p.add_layout(
            LabelSet(
                x="x",
                y="y",
                text="val",
                source=src,
                text_align="center",
                text_baseline="middle",
                text_font_size=val_fs,
                text_color=text_color,
                text_alpha=0.85,
                y_offset=-y_off,
            )
        )

# Theme-adaptive chrome
p.title.text_font_size = "41pt"
p.title.align = "center"
p.title.text_color = INK
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
p.min_border = 50

# Legend — theme-adaptive styling with improved sizing for 2400px canvas
p.add_layout(Legend(items=legend_items, location="top_right"))
p.legend.label_text_font_size = "34pt"
p.legend.label_text_color = INK
p.legend.glyph_height = 48
p.legend.glyph_width = 48
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.92
p.legend.border_line_color = INK_SOFT
p.legend.border_line_width = 2
p.legend.padding = 16
p.legend.spacing = 10
p.legend.label_standoff = 12
p.legend.click_policy = "hide"

# HoverTool — active in the HTML artifact
p.add_tools(
    HoverTool(
        tooltips=[(DEPARTMENT, f"@{{{DEPARTMENT}}}"), (BUDGET, f"@{{{BUDGET}}}"), (TIER, f"@{{{TIER}}}")],
        renderers=renderers,
    )
)

# Save interactive HTML (catalog artifact)
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome via Selenium (export_png uses snap chromedriver which fails)
# CDP setDeviceMetricsOverride forces the exact inner viewport — --window-size alone is
# consumed by browser chrome in headless mode and shrinks the rendered height.
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
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
# Paint the page in the theme color so the anti-aliased canvas edge shows no white line
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
