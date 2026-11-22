"""anyplot.ai
violin-grouped-swarm: Grouped Violin Plot with Swarm Overlay
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-18
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Legend, LegendItem
from bokeh.plotting import figure
from scipy import stats
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TASK = "Task type"  # role: category
EXPERTISE = "Expertise"  # role: group
RESPONSE = "Response time (ms)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
np.random.seed(42)
tasks = ["Simple", "Moderate", "Complex"]
levels = ["Novice", "Expert"]
rows = []
for t_idx, task in enumerate(tasks):
    for level in levels:
        # Experts are faster, complex tasks take longer
        mean = 200 + t_idx * 150 - (80 if level == "Expert" else 0)
        sd = 30 + t_idx * 15
        for value in np.clip(np.random.normal(mean, sd, 40), 50, 900):
            rows.append({TASK: task, EXPERTISE: level, RESPONSE: value})
df = pd.DataFrame(rows)

# Plot: reads only df and the constants above
categories = list(df[TASK].unique())
groups = list(df[EXPERTISE].unique())
colors = {group: IMPRINT_PALETTE[i] for i, group in enumerate(groups)}
slot = 0.8 / len(groups)  # width of one group's slot inside a category
offsets = {group: (i - (len(groups) - 1) / 2) * slot for i, group in enumerate(groups)}
max_half_width = slot * 0.42
top = df[RESPONSE].max()

p = figure(
    width=3200,
    height=1800,
    title="violin-grouped-swarm · python · bokeh · anyplot.ai",
    x_axis_label=TASK,
    y_axis_label=RESPONSE,
    x_range=(-0.5, len(categories) - 0.5),
    y_range=(0, top * 1.1),
    tools="",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

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

p.xaxis.ticker = list(range(len(categories)))
p.xaxis.major_label_overrides = {i: str(c) for i, c in enumerate(categories)}

legend_items = []
swarm_renderers = []
for group in groups:
    first_violin = None
    for c_idx, category in enumerate(categories):
        values = df.loc[(df[TASK] == category) & (df[EXPERTISE] == group), RESPONSE].dropna().to_numpy(dtype=float)
        center = c_idx + offsets[group]

        # Mirrored violin from a kernel density estimate
        grid = np.linspace(values.min() - 15, values.max() + 15, 100)
        half_width = stats.gaussian_kde(values)(grid)
        half_width = half_width / half_width.max() * max_half_width
        violin = p.patch(
            np.concatenate([center - half_width, (center + half_width)[::-1]]),
            np.concatenate([grid, grid[::-1]]),
            fill_color=colors[group],
            fill_alpha=0.45,
            line_color=colors[group],
            line_width=2.5,
        )
        if first_violin is None:
            first_violin = violin

        # Swarm: points stay at their value; only the x position is spread within the violin
        step = max_half_width / 5
        seen = {}
        swarm_x = []
        for value in values:
            key = int(value // 20)
            n = seen.get(key, 0)
            seen[key] = n + 1
            side = 1 if n % 2 == 0 else -1
            offset = 0.0 if n == 0 else (n // 2 + 1) * step * side
            local = np.interp(value, grid, half_width) * 0.8
            swarm_x.append(center + np.clip(offset, -local, local))

        source = ColumnDataSource(
            {"x": swarm_x, "y": values, "cat": [category] * len(values), "grp": [group] * len(values)}
        )
        swarm_renderers.append(
            p.scatter(
                "x",
                "y",
                source=source,
                size=11,
                fill_color=colors[group],
                fill_alpha=0.8,
                line_color=PAGE_BG,
                line_width=1.5,
            )
        )
    legend_items.append(LegendItem(label=str(group), renderers=[first_violin]))

p.add_tools(HoverTool(renderers=swarm_renderers, tooltips=[(TASK, "@cat"), (EXPERTISE, "@grp"), (RESPONSE, "@y{0.0}")]))

legend = Legend(
    items=legend_items,
    location="top_left",
    title=EXPERTISE,
    title_text_font_size="30pt",
    title_text_color=INK,
    label_text_font_size="30pt",
    label_text_color=INK_SOFT,
    glyph_width=40,
    glyph_height=40,
    spacing=12,
    padding=20,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.95,
    border_line_color=INK_SOFT,
    border_line_width=2,
)
p.add_layout(legend, "center")

# Save HTML and screenshot it with headless Chrome
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
