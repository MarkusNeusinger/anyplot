"""anyplot.ai
violin-split: Split Violin Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-08
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Legend, LegendItem, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per split group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
CONDITION = "Condition Severity"  # role: category
SCORE = "Recovery Score (0-100)"  # role: value
ARM = "Treatment Arm"  # role: split_group

# Data: replace this block with your own table, for example df = pd.read_csv("trial.csv")
np.random.seed(42)
rows = []
for cond, base, gain, spread in [("Mild", 65, 12, 8), ("Moderate", 45, 25, 12), ("Severe", 30, 35, 15)]:
    placebo = np.clip(np.random.normal(base, spread, 120), 0, 100)
    treatment = np.clip(np.random.normal(base + gain, spread * 0.85, 120), 0, 100)
    rows += [(cond, v, "Placebo") for v in placebo]
    rows += [(cond, v, "Active Treatment") for v in treatment]
df = pd.DataFrame(rows, columns=[CONDITION, SCORE, ARM])

# Plot: reads only df and the constants above
conditions = list(df[CONDITION].unique())
arms = list(df[ARM].unique())
VIOLIN_WIDTH = 0.35  # half-width of a violin in category units


def gaussian_kde(values, lo, hi, n_points=120):
    """Gaussian KDE (Scott-style bandwidth) evaluated on a grid from lo to hi."""
    values = np.asarray(values, dtype=float)
    values = values[~np.isnan(values)]
    bandwidth = 1.06 * np.std(values, ddof=1) * len(values) ** (-1 / 5)
    grid = np.linspace(lo, hi, n_points)
    z = (grid[:, None] - values[None, :]) / bandwidth
    density = np.exp(-0.5 * z**2).sum(axis=1) / (len(values) * bandwidth * np.sqrt(2 * np.pi))
    return grid, density


y_min, y_max = df[SCORE].min(), df[SCORE].max()
pad = (y_max - y_min) * 0.05
y_lo, y_hi = y_min - 2.2 * pad, y_max + 2.2 * pad

title = "Clinical Recovery Scores · violin-split · python · bokeh · anyplot.ai"
title_pt = round(50 * min(1.0, 67 / len(title)))

p = figure(
    width=3200,
    height=1800,
    title=title,
    x_axis_label=CONDITION,
    y_axis_label=SCORE,
    x_range=conditions,
    y_range=Range1d(y_lo, y_hi),
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

legend_renderers = {}
stats = {"x": [], "y": [], "group": [], "median": [], "q1": [], "q3": [], "n": []}

for idx, cond in enumerate(conditions):
    i = idx + 0.5  # center of the categorical slot
    for k, arm in enumerate(arms):
        values = df.loc[(df[CONDITION] == cond) & (df[ARM] == arm), SCORE].to_numpy()
        grid, density = gaussian_kde(values, max(y_lo, values.min() - pad), min(y_hi, values.max() + pad))
        half = density / density.max() * VIOLIN_WIDTH
        sign = -1 if k == 0 else 1  # first arm left, second arm right of the shared center line
        xs = np.concatenate([[i], i + sign * half, [i]])
        ys = np.concatenate([[grid[0]], grid, [grid[-1]]])
        color = IMPRINT_PALETTE[k]
        patch = p.patch(xs, ys, fill_color=color, fill_alpha=0.65, line_color=color, line_width=2)
        legend_renderers.setdefault(arm, patch)

        q1, median, q3 = np.percentile(values, [25, 50, 75])
        x0, x1 = sorted([i, i + sign * VIOLIN_WIDTH * 0.6])
        p.segment(x0=[x0], y0=[median], x1=[x1], y1=[median], line_color=INK, line_width=5)
        for q in (q1, q3):
            p.segment(x0=[x0], y0=[q], x1=[x1], y1=[q], line_color=INK, line_width=3, line_dash="dashed")

        stats["x"].append(i + sign * VIOLIN_WIDTH / 2)
        stats["y"].append(median)
        stats["group"].append(f"{cond} - {arm}")
        stats["median"].append(f"{median:.1f}")
        stats["q1"].append(f"{q1:.1f}")
        stats["q3"].append(f"{q3:.1f}")
        stats["n"].append(str(len(values)))

# Invisible hit targets that carry the per-half statistics for hover tooltips
hover_points = p.scatter(x="x", y="y", size=60, fill_alpha=0, line_alpha=0, source=ColumnDataSource(stats))
p.add_tools(
    HoverTool(
        renderers=[hover_points],
        tooltips=[("Group", "@group"), ("Median", "@median"), ("Q1", "@q1"), ("Q3", "@q3"), ("N", "@n")],
    )
)

legend = Legend(
    items=[LegendItem(label=str(arm), renderers=[legend_renderers[arm]]) for arm in arms],
    location="bottom_left",
    title=ARM,
)
p.add_layout(legend)
legend.label_text_font_size = "34pt"
legend.title_text_font_size = "34pt"
legend.label_text_color = INK_SOFT
legend.title_text_color = INK
legend.glyph_width = 70
legend.glyph_height = 50
legend.spacing = 14
legend.padding = 24
legend.margin = 30
legend.background_fill_color = ELEVATED_BG
legend.background_fill_alpha = 0.9
legend.border_line_color = INK_SOFT

# Style
p.title.text_font_size = f"{title_pt}pt"
p.title.align = "center"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.15
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.outline_line_color = None
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG

# Save HTML, then screenshot it with headless Chrome
output_file(f"plot-{THEME}.html")
save(p)

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
