"""anyplot.ai
alluvial-basic: Basic Alluvial Diagram
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 96/100 | Updated: 2026-05-09
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import Label
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
FROM_POINT = "From"  # role: time_point
TO_POINT = "To"  # role: extra
SOURCE = "Party at start"  # role: category
TARGET = "Party at end"  # role: extra
FLOW = "Voters (millions)"  # role: flow

# Data: replace this block with your own table, for example df = pd.read_csv("flows.csv")
transitions = {
    ("2012", "2016"): [
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
    ("2016", "2020"): [
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
    ("2020", "2024"): [
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
}
df = pd.DataFrame(
    [
        {FROM_POINT: a, TO_POINT: b, SOURCE: src, TARGET: dst, FLOW: value}
        for (a, b), rows in transitions.items()
        for src, dst, value in rows
    ]
)

# Plot: reads only df and the constants above
time_points = list(dict.fromkeys(df[FROM_POINT])) + [df[TO_POINT].iloc[-1]]
categories = list(dict.fromkeys(pd.concat([df[SOURCE], df[TARGET]])))
colors = {cat: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, cat in enumerate(categories)}

# Block heights: outflow at the first time point, inflow everywhere else
node_heights = []
for t_idx, point in enumerate(time_points):
    if t_idx == 0:
        sizes = df[df[FROM_POINT] == point].groupby(SOURCE)[FLOW].sum()
    else:
        sizes = df[df[TO_POINT] == point].groupby(TARGET)[FLOW].sum()
    node_heights.append({cat: float(sizes.get(cat, 0)) for cat in categories})

node_width = 0.12
gap = 0.05 * max(sum(h.values()) for h in node_heights)

node_positions = []
for heights in node_heights:
    positions = {}
    y_cursor = 0.0
    for cat in categories:
        positions[cat] = (y_cursor, y_cursor + heights[cat])
        y_cursor += heights[cat] + gap
    node_positions.append(positions)

y_top = max(pos[cat][1] for pos in node_positions for cat in categories)
header_y = -0.03 * y_top
subtitle_y = y_top + 0.12 * y_top

W, H = 3200, 1800
p = figure(
    width=W,
    height=H,
    title="alluvial-basic · python · bokeh · anyplot.ai",
    x_range=(-1.25, len(time_points) - 1 + 1.25),
    y_range=(-0.14 * y_top, subtitle_y + 0.02 * y_top),
    tools="",
    toolbar_location=None,
    min_border_left=40,
    min_border_right=40,
    min_border_top=110,
    min_border_bottom=40,
)

p.title.text_font_size = "50pt"
p.title.text_color = INK
p.title.align = "center"
p.xgrid.visible = False
p.ygrid.visible = False
p.xaxis.visible = False
p.yaxis.visible = False
p.outline_line_color = None
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG

p.add_layout(
    Label(
        x=(len(time_points) - 1) / 2,
        y=subtitle_y,
        text="Voter Migration Between Parties (values in millions)",
        text_font_size="34pt",
        text_align="center",
        text_baseline="top",
        text_color=INK_SOFT,
    )
)

# Ribbons: cubic Bezier with horizontal tangents, so y follows a smoothstep in x
s = np.linspace(0, 1, 50)
ease = 3 * s**2 - 2 * s**3
for t_idx, point in enumerate(time_points[:-1]):
    x_start = t_idx + node_width / 2
    x_end = t_idx + 1 - node_width / 2
    xs_curve = x_start + (x_end - x_start) * s

    source_cursors = {cat: node_positions[t_idx][cat][0] for cat in categories}
    target_cursors = {cat: node_positions[t_idx + 1][cat][0] for cat in categories}

    for _, row in df[df[FROM_POINT] == point].iterrows():
        src, dst, value = row[SOURCE], row[TARGET], row[FLOW]
        src_bottom = source_cursors[src]
        source_cursors[src] += value
        dst_bottom = target_cursors[dst]
        target_cursors[dst] += value

        y_lo = src_bottom + (dst_bottom - src_bottom) * ease
        y_hi = y_lo + value
        xs = np.concatenate([xs_curve, xs_curve[::-1]])
        ys = np.concatenate([y_hi, y_lo[::-1]])
        p.patch(xs, ys, fill_color=colors[src], fill_alpha=0.5, line_color=colors[src], line_alpha=0.7, line_width=1)

# Blocks, with a category label at every column
last = len(time_points) - 1
for t_idx in range(len(time_points)):
    for cat in categories:
        y_start, y_end = node_positions[t_idx][cat]
        if y_end <= y_start:
            continue
        p.quad(
            left=t_idx - node_width / 2,
            right=t_idx + node_width / 2,
            top=y_end,
            bottom=y_start,
            fill_color=colors[cat],
            line_color=PAGE_BG,
            line_width=2,
        )
        text = f"{cat} ({y_end - y_start:g}M)"
        if t_idx == 0:
            label = Label(
                x=t_idx - node_width / 2 - 0.03,
                y=(y_start + y_end) / 2,
                text=text,
                text_align="right",
                text_color=INK_SOFT,
            )
        else:
            label = Label(
                x=t_idx + node_width / 2 + 0.03,
                y=(y_start + y_end) / 2,
                text=text if t_idx == last else cat,
                text_color=INK_SOFT if t_idx == last else INK,
                background_fill_color=None if t_idx == last else PAGE_BG,
                background_fill_alpha=0.0 if t_idx == last else 0.7,
            )
        label.update(text_font_size="26pt", text_baseline="middle")
        p.add_layout(label)

# Column headers
for t_idx, point in enumerate(time_points):
    p.add_layout(
        Label(
            x=t_idx,
            y=header_y,
            text=point,
            text_font_size="34pt",
            text_font_style="bold",
            text_align="center",
            text_baseline="top",
            text_color=INK,
        )
    )

output_file(f"plot-{THEME}.html")
save(p)

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
