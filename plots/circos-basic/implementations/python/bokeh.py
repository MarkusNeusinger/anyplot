"""anyplot.ai
circos-basic: Circos Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-15
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per region in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
FLOW_THRESHOLD = 15  # region pairs with a combined flow below this get no ribbon
SEGMENT_GAP = 0.03  # gap between outer segments, in radians

# Columns: set these to your table's column names
SOURCE = "Origin region"  # role: source
TARGET = "Destination region"  # role: target
VALUE = "Trade flow (USD bn)"  # role: value
TRACK = "GDP growth (%)"  # role: track_data

# Data: replace this block with your own edge list, for example df = pd.read_csv("flows.csv")
# One row per directed flow; the track value of the origin region repeats on its rows.
regions = ["Asia", "Europe", "N. America", "S. America", "Africa", "Oceania"]
flow_matrix = np.array(
    [
        [0, 45, 52, 18, 15, 22],
        [38, 0, 35, 12, 20, 8],
        [48, 42, 0, 28, 10, 15],
        [15, 18, 25, 0, 8, 5],
        [12, 25, 8, 10, 0, 3],
        [20, 10, 18, 6, 4, 0],
    ]
)
gdp_growth = [4.2, 1.8, 2.5, 1.5, 3.8, 2.2]
df = pd.DataFrame(
    [
        {SOURCE: regions[i], TARGET: regions[j], VALUE: flow_matrix[i, j], TRACK: gdp_growth[i]}
        for i in range(len(regions))
        for j in range(len(regions))
        if i != j
    ]
)

# Plot: reads only df and the constants above
regions = list(df[SOURCE].unique())
n_regions = len(regions)
flows = df.pivot_table(index=SOURCE, columns=TARGET, values=VALUE, aggfunc="sum", sort=False)
flows = flows.reindex(index=regions, columns=regions).to_numpy(dtype=float)
flows = np.nan_to_num(flows, nan=0.0)  # a pair with no row is a pair with no flow
track_values = df.groupby(SOURCE, sort=False)[TRACK].first().reindex(regions).to_numpy(dtype=float)

segment_sizes = flows.sum(axis=0) + flows.sum(axis=1)
total_size = segment_sizes.sum()
available_angle = 2 * np.pi - SEGMENT_GAP * n_regions

segment_angles = []
current_angle = 0.0
for size in segment_sizes:
    end = current_angle + (size / total_size) * available_angle
    segment_angles.append((current_angle, end))
    current_angle = end + SEGMENT_GAP

SIZE = 2400
LIMIT = 1.65
p = figure(
    width=SIZE,
    height=SIZE,
    title="circos-basic · python · bokeh · anyplot.ai",
    x_range=(-LIMIT, LIMIT),
    y_range=(-LIMIT, LIMIT),
    tools="",
    toolbar_location=None,
)

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

outer_radius = 1.0
inner_radius = 0.85
track_outer = 0.82
track_inner = 0.70
ribbon_radius = 0.65

for i, (start, end) in enumerate(segment_angles):
    theta = np.linspace(start, end, 50)
    xs = np.concatenate([outer_radius * np.cos(theta), inner_radius * np.cos(theta[::-1])])
    ys = np.concatenate([outer_radius * np.sin(theta), inner_radius * np.sin(theta[::-1])])
    p.patches(xs=[xs], ys=[ys], fill_color=IMPRINT_PALETTE[i], line_color=INK_SOFT, line_width=2, alpha=0.85)

    mid_angle = (start + end) / 2
    label_radius = outer_radius + 0.12
    angle = np.degrees(mid_angle)
    if 90 < angle < 270:
        angle += 180
    p.text(
        x=[label_radius * np.cos(mid_angle)],
        y=[label_radius * np.sin(mid_angle)],
        text=[regions[i]],
        text_font_size="30pt",
        text_align="center",
        text_baseline="middle",
        text_color=INK,
        angle=[np.radians(angle - 90)],
    )

# Inner track: bar height follows the region's track value
min_track = track_values.min()
track_range = track_values.max() - min_track
for i, (start, end) in enumerate(segment_angles):
    norm_val = (track_values[i] - min_track) / track_range if track_range > 0 else 0.5
    bar_radius = track_inner + norm_val * (track_outer - track_inner)
    theta = np.linspace(start, end, 30)
    xs = np.concatenate([bar_radius * np.cos(theta), track_inner * np.cos(theta[::-1])])
    ys = np.concatenate([bar_radius * np.sin(theta), track_inner * np.sin(theta[::-1])])
    p.patches(xs=[xs], ys=[ys], fill_color=IMPRINT_PALETTE[i], line_color=None, alpha=0.4)

ring = np.linspace(0, 2 * np.pi, 100)
p.line(track_inner * np.cos(ring), track_inner * np.sin(ring), line_color=INK_SOFT, line_width=2, line_alpha=0.2)

# Ribbons: width on each segment is proportional to the pair's combined flow
n_curve = 30
t = np.linspace(0, 1, n_curve)
for i in range(n_regions):
    for j in range(i + 1, n_regions):
        total_flow = flows[i, j] + flows[j, i]
        if total_flow < FLOW_THRESHOLD:
            continue

        start_i, end_i = segment_angles[i]
        start_j, end_j = segment_angles[j]
        width_i = (total_flow / segment_sizes[i]) * (end_i - start_i) * 0.8
        width_j = (total_flow / segment_sizes[j]) * (end_j - start_j) * 0.8
        mid_i = (start_i + end_i) / 2
        mid_j = (start_j + end_j) / 2
        i_lo, i_hi = mid_i - width_i / 2, mid_i + width_i / 2
        j_lo, j_hi = mid_j - width_j / 2, mid_j + width_j / 2

        def bezier(a0, a1):
            """Quadratic curve between two ribbon-radius points, pulled to the centre."""
            x0, y0 = ribbon_radius * np.cos(a0), ribbon_radius * np.sin(a0)
            x1, y1 = ribbon_radius * np.cos(a1), ribbon_radius * np.sin(a1)
            return (1 - t) ** 2 * x0 + t**2 * x1, (1 - t) ** 2 * y0 + t**2 * y1

        curve1_x, curve1_y = bezier(i_lo, j_lo)
        curve2_x, curve2_y = bezier(j_hi, i_hi)
        arc_j = np.linspace(j_lo, j_hi, 10)
        arc_i = np.linspace(i_hi, i_lo, 10)

        ribbon_x = np.concatenate([curve1_x, ribbon_radius * np.cos(arc_j), curve2_x, ribbon_radius * np.cos(arc_i)])
        ribbon_y = np.concatenate([curve1_y, ribbon_radius * np.sin(arc_j), curve2_y, ribbon_radius * np.sin(arc_i)])
        p.patches(
            xs=[ribbon_x],
            ys=[ribbon_y],
            fill_color=IMPRINT_PALETTE[i],
            line_color=IMPRINT_PALETTE[i],
            line_width=1,
            alpha=0.45,
        )

# Legend and track caption below the circle, two rows of three
for i, region in enumerate(regions):
    x_pos = -1.15 + (i % 3) * 0.85
    y_pos = -1.40 - (i // 3) * 0.13
    p.rect(x=[x_pos], y=[y_pos], width=0.08, height=0.08, fill_color=IMPRINT_PALETTE[i], line_color=None)
    p.text(
        x=[x_pos + 0.09],
        y=[y_pos],
        text=[region],
        text_font_size="26pt",
        text_align="left",
        text_baseline="middle",
        text_color=INK_SOFT,
    )

p.text(
    x=[0],
    y=[-1.27],
    text=[f"Inner track: {TRACK}"],
    text_font_size="26pt",
    text_color=INK_SOFT,
    text_align="center",
    text_baseline="middle",
)

# Output
output_file(f"plot-{THEME}.html")
save(p)

opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={SIZE},{SIZE}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.set_window_size(SIZE, SIZE)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": SIZE, "height": SIZE, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
