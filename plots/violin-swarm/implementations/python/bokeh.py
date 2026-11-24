"""anyplot.ai
violin-swarm: Violin Plot with Overlaid Swarm Points
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-18
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, FactorRange, HoverTool
from bokeh.plotting import figure
from scipy import stats
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
CONDITION = "Experimental condition"  # role: category
REACTION = "Reaction time (ms)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("trials.csv")
np.random.seed(42)
n_per_group = 50
conditions = {"Control": (350, 50), "Low Dose": (320, 45), "Medium Dose": (280, 60), "High Dose": (250, 40)}
df = pd.DataFrame(
    {
        CONDITION: np.repeat(list(conditions), n_per_group),
        REACTION: np.concatenate([np.random.normal(mu, sd, n_per_group) for mu, sd in conditions.values()]),
    }
)

# Plot: reads only df and the constants above
categories = list(df[CONDITION].unique())
max_half_width = 0.35  # in category units; a violin never exceeds this on either side
rng = np.random.default_rng(42)

violins = []
swarm_parts = []
for i, cat in enumerate(categories):
    values = df.loc[df[CONDITION] == cat, REACTION].dropna().to_numpy()
    center = i + 0.5  # categorical factors sit at index + 0.5 on the numeric scale

    # Mirrored KDE outline, tails ending a little beyond the data range
    kde = stats.gaussian_kde(values)
    pad = 0.1 * np.ptp(values)
    grid = np.linspace(values.min() - pad, values.max() + pad, 200)
    density = kde(grid)
    half = density / density.max() * max_half_width
    violins.append((np.concatenate([center - half, (center + half)[::-1]]), np.concatenate([grid, grid[::-1]])))

    # Swarm: every point keeps its value; only the sideways offset is random,
    # bounded by the violin outline at that value
    limit = kde(values) / density.max() * max_half_width * 0.85
    swarm_parts.append(pd.DataFrame({"x": center + rng.uniform(-limit, limit), CONDITION: cat, REACTION: values}))
swarm = pd.concat(swarm_parts, ignore_index=True)

p = figure(
    width=3200,
    height=1800,
    title="violin-swarm · python · bokeh · anyplot.ai",
    x_range=FactorRange(*categories, range_padding=0.1),
    x_axis_label=CONDITION,
    y_axis_label=REACTION,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Background and chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Translucent violins, then swarm points on top
for vx, vy in violins:
    p.patch(
        vx.tolist(),
        vy.tolist(),
        fill_color=IMPRINT_PALETTE[0],
        fill_alpha=0.4,
        line_color=IMPRINT_PALETTE[0],
        line_width=4,
    )

p.scatter(
    "x",
    REACTION,
    source=ColumnDataSource(swarm),
    size=16,
    color=IMPRINT_PALETTE[0],
    alpha=0.75,
    line_color=INK_SOFT,
    line_width=1.5,
)
p.add_tools(HoverTool(tooltips=[(CONDITION, f"@{{{CONDITION}}}"), (REACTION, f"@{{{REACTION}}}{{0.0}}")]))

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
time.sleep(3)  # let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
