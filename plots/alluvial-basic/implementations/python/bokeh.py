""" anyplot.ai
alluvial-basic: Basic Alluvial Diagram
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 96/100 | Updated: 2026-05-09
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import Label, Legend, LegendItem
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"
OI_2 = "#C475FD"
OI_3 = "#4467A3"
OI_4 = "#BD8233"

np.random.seed(42)

time_points = ["2012", "2016", "2020", "2024"]
categories = ["Democratic", "Republican", "Independent", "Other"]
colors = {"Democratic": BRAND, "Republican": OI_2, "Independent": OI_3, "Other": OI_4}

flows_data = [
    [
        ("Democratic", "Democratic", 35),
        ("Democratic", "Independent", 5),
        ("Democratic", "Republican", 2),
        ("Republican", "Republican", 30),
        ("Republican", "Independent", 4),
        ("Republican", "Democratic", 3),
        ("Independent", "Democratic", 4),
        ("Independent", "Republican", 3),
        ("Independent", "Independent", 8),
        ("Other", "Other", 3),
        ("Other", "Independent", 2),
        ("Other", "Democratic", 1),
    ],
    [
        ("Democratic", "Democratic", 38),
        ("Democratic", "Independent", 3),
        ("Democratic", "Republican", 2),
        ("Republican", "Republican", 32),
        ("Republican", "Independent", 3),
        ("Republican", "Democratic", 2),
        ("Independent", "Democratic", 5),
        ("Independent", "Republican", 4),
        ("Independent", "Independent", 8),
        ("Other", "Other", 2),
        ("Other", "Independent", 2),
        ("Other", "Republican", 1),
    ],
    [
        ("Democratic", "Democratic", 40),
        ("Democratic", "Independent", 4),
        ("Democratic", "Republican", 1),
        ("Republican", "Republican", 34),
        ("Republican", "Independent", 2),
        ("Republican", "Democratic", 3),
        ("Independent", "Democratic", 4),
        ("Independent", "Republican", 5),
        ("Independent", "Independent", 6),
        ("Other", "Other", 2),
        ("Other", "Democratic", 1),
        ("Other", "Independent", 1),
    ],
]

node_heights = []
for t_idx, _t in enumerate(time_points):
    heights = {}
    if t_idx == 0:
        for cat in categories:
            heights[cat] = sum(f[2] for f in flows_data[0] if f[0] == cat)
    elif t_idx == len(time_points) - 1:
        for cat in categories:
            heights[cat] = sum(f[2] for f in flows_data[-1] if f[1] == cat)
    else:
        for cat in categories:
            heights[cat] = sum(f[2] for f in flows_data[t_idx - 1] if f[1] == cat)
    node_heights.append(heights)

x_positions = [0, 1, 2, 3]
node_width = 0.12
gap = 2

node_positions = []
for t_idx in range(len(time_points)):
    positions = {}
    y_cursor = 0
    for cat in categories:
        height = node_heights[t_idx][cat]
        positions[cat] = {"y_start": y_cursor, "y_end": y_cursor + height}
        y_cursor += height + gap
    node_positions.append(positions)

p = figure(
    width=4800,
    height=2700,
    title="alluvial-basic · bokeh · anyplot.ai",
    x_range=(-0.9, 4.3),
    y_range=(-8, max(sum(node_heights[0].values()) + gap * len(categories), 120)),
    tools="",
    toolbar_location=None,
)

p.title.text_font_size = "28pt"
p.title.text_color = INK
p.title.align = "center"
p.xgrid.visible = False
p.ygrid.visible = False
p.xaxis.visible = False
p.yaxis.visible = False
p.outline_line_color = None
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG

subtitle = Label(
    x=1.5,
    y=115,
    text="Voter Migration Between Parties (values in millions)",
    text_font_size="22pt",
    text_align="center",
    text_baseline="top",
    text_color=INK_SOFT,
)
p.add_layout(subtitle)

n_points = 50
t_param = np.linspace(0, 1, n_points)

for t_idx, flows in enumerate(flows_data):
    x_start = x_positions[t_idx] + node_width / 2
    x_end = x_positions[t_idx + 1] - node_width / 2

    source_cursors = {cat: node_positions[t_idx][cat]["y_start"] for cat in categories}
    target_cursors = {cat: node_positions[t_idx + 1][cat]["y_start"] for cat in categories}

    for from_cat, to_cat, value in flows:
        if value == 0:
            continue

        y_src_bottom = source_cursors[from_cat]
        y_src_top = y_src_bottom + value
        source_cursors[from_cat] = y_src_top

        y_tgt_bottom = target_cursors[to_cat]
        y_tgt_top = y_tgt_bottom + value
        target_cursors[to_cat] = y_tgt_top

        cx0 = x_start + (x_end - x_start) / 3
        cx1 = x_start + 2 * (x_end - x_start) / 3

        x_top = (
            (1 - t_param) ** 3 * x_start
            + 3 * (1 - t_param) ** 2 * t_param * cx0
            + 3 * (1 - t_param) * t_param**2 * cx1
            + t_param**3 * x_end
        )
        y_top = (
            (1 - t_param) ** 3 * y_src_top
            + 3 * (1 - t_param) ** 2 * t_param * y_src_top
            + 3 * (1 - t_param) * t_param**2 * y_tgt_top
            + t_param**3 * y_tgt_top
        )

        x_bottom = (
            (1 - t_param) ** 3 * x_start
            + 3 * (1 - t_param) ** 2 * t_param * cx0
            + 3 * (1 - t_param) * t_param**2 * cx1
            + t_param**3 * x_end
        )
        y_bottom = (
            (1 - t_param) ** 3 * y_src_bottom
            + 3 * (1 - t_param) ** 2 * t_param * y_src_bottom
            + 3 * (1 - t_param) * t_param**2 * y_tgt_bottom
            + t_param**3 * y_tgt_bottom
        )

        xs = list(x_top) + list(x_bottom[::-1])
        ys = list(y_top) + list(y_bottom[::-1])

        color = colors[from_cat]
        p.patch(xs, ys, fill_color=color, fill_alpha=0.5, line_color=color, line_alpha=0.7, line_width=1)

legend_renderers = {}
for t_idx, _t in enumerate(time_points):
    x = x_positions[t_idx]
    for cat in categories:
        y_start = node_positions[t_idx][cat]["y_start"]
        y_end = node_positions[t_idx][cat]["y_end"]
        height = y_end - y_start

        if height > 0:
            renderer = p.quad(
                left=x - node_width / 2,
                right=x + node_width / 2,
                top=y_end,
                bottom=y_start,
                fill_color=colors[cat],
                line_color=PAGE_BG,
                line_width=2,
            )

            if cat not in legend_renderers:
                legend_renderers[cat] = renderer

            if t_idx == 0:
                label = Label(
                    x=x - node_width / 2 - 0.03,
                    y=(y_start + y_end) / 2,
                    text=f"{cat} ({int(height)}M)",
                    text_font_size="22pt",
                    text_baseline="middle",
                    text_align="right",
                    text_color=INK_SOFT,
                )
                p.add_layout(label)
            elif t_idx == len(time_points) - 1:
                label = Label(
                    x=x + node_width / 2 + 0.03,
                    y=(y_start + y_end) / 2,
                    text=f"{cat} ({int(height)}M)",
                    text_font_size="22pt",
                    text_baseline="middle",
                    text_color=INK_SOFT,
                )
                p.add_layout(label)

legend_items = [LegendItem(label=cat, renderers=[legend_renderers[cat]]) for cat in categories]
legend = Legend(
    items=legend_items,
    location="top_right",
    label_text_font_size="18pt",
    label_text_color=INK_SOFT,
    glyph_width=30,
    glyph_height=30,
    spacing=10,
    padding=15,
    background_fill_alpha=0.9,
    background_fill_color=ELEVATED_BG,
    border_line_color=INK_SOFT,
)
p.add_layout(legend, "right")

for t_idx, t in enumerate(time_points):
    label = Label(
        x=x_positions[t_idx],
        y=-4,
        text=t,
        text_font_size="24pt",
        text_align="center",
        text_baseline="top",
        text_color=INK,
        text_font_style="bold",
    )
    p.add_layout(label)

output_file(f"plot-{THEME}.html")
save(p)

W, H = 4800, 2700
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
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
