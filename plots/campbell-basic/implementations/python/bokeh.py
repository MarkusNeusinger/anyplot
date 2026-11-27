"""anyplot.ai
campbell-basic: Campbell Diagram
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-28
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Legend, LegendItem, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
ANYPLOT_AMBER = "#DDCC77"  # warning semantic anchor: critical speeds

# Constants
ENGINE_ORDERS = [1, 2, 3]  # excitation lines: frequency (Hz) = order * speed (RPM) / 60

# Columns: set these to your table's column names
SPEED = "Rotational Speed (RPM)"  # role: speed
MODES = ["1st Bending", "2nd Bending", "1st Torsional", "Axial", "3rd Bending"]  # role: frequency_mode_

# Data: replace this block with your own table, for example df = pd.read_csv("modes.csv")
speeds = np.linspace(0, 6000, 100)
df = pd.DataFrame(
    {
        SPEED: speeds,
        MODES[0]: 25 + 0.008 * speeds + 3.5 * np.sin(speeds / 2800 * np.pi),
        MODES[1]: 62 - 0.006 * speeds + 2.0 * np.sin(speeds / 2200 * np.pi),
        MODES[2]: 85 + 0.005 * speeds,
        MODES[3]: 110 - 0.004 * speeds + 2.5 * np.cos(speeds / 3200 * np.pi),
        MODES[4]: 130 + 0.010 * speeds - 4.0 * np.cos(speeds / 2600 * np.pi),
    }
)

# Plot: reads only df and the constants above
table = df.set_index(SPEED)[MODES]
modes = MODES
speeds = table.index.to_numpy()
speed_min, speed_max = speeds.min(), speeds.max()
y_max = np.nanmax(table.to_numpy()) * 1.08

# Engine order lines, cut where they leave the top of the plot
eo_names = {order: f"{order}x EO" for order in ENGINE_ORDERS}
eo_freq = {order: order * speeds / 60 for order in ENGINE_ORDERS}

# Critical speeds: sign-change interpolation where an engine order line crosses a mode curve
crit_rpm, crit_freq, crit_label = [], [], []
for order in ENGINE_ORDERS:
    for mode in modes:
        diff = eo_freq[order] - table[mode].to_numpy()
        for idx in np.where(np.diff(np.sign(diff)))[0]:
            frac = abs(diff[idx]) / (abs(diff[idx]) + abs(diff[idx + 1]))
            rpm = speeds[idx] + frac * (speeds[idx + 1] - speeds[idx])
            freq = table[mode].to_numpy()[idx] + frac * (table[mode].to_numpy()[idx + 1] - table[mode].to_numpy()[idx])
            if speed_min < rpm < speed_max and freq < y_max:
                crit_rpm.append(rpm)
                crit_freq.append(freq)
                crit_label.append(f"{order}x × {mode}")

# Title with font-size scaling
title = "campbell-basic · python · bokeh · anyplot.ai"
title_fontsize = f"{round(50 * min(67 / len(title), 1.0))}pt"

speed_span = speed_max - speed_min
p = figure(
    width=3200,
    height=1800,
    title=title,
    x_axis_label=SPEED,
    y_axis_label="Frequency (Hz)",
    x_range=Range1d(speed_min - 0.015 * speed_span, speed_max + 0.05 * speed_span),
    y_range=Range1d(0, y_max),
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

source_data = {SPEED: speeds}
source_data.update({mode: table[mode].to_numpy() for mode in modes})
source_data.update({eo_names[o]: np.where(eo_freq[o] <= y_max, eo_freq[o], np.nan) for o in ENGINE_ORDERS})
source = ColumnDataSource(source_data)

legend_items = []
for i, mode in enumerate(modes):
    line = p.line(
        x=SPEED,
        y=mode,
        source=source,
        line_width=4,
        line_color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
        line_alpha=0.9,
    )
    legend_items.append(LegendItem(label=mode, renderers=[line]))

for order in ENGINE_ORDERS:
    line = p.line(
        x=SPEED,
        y=eo_names[order],
        source=source,
        line_width=3,
        line_color=INK_MUTED,
        line_dash=[12, 8],
        line_alpha=0.85,
    )
    legend_items.append(LegendItem(label=eo_names[order], renderers=[line]))

    # Order label at the line's end (right edge, or just below the top of the plot)
    x_end = min(speed_max, 0.95 * y_max * 60 / order)
    p.add_layout(
        Label(
            x=x_end + 0.008 * speed_span,
            y=order * x_end / 60,
            text=f"{order}x",
            text_font_size="24pt",
            text_color=INK_MUTED,
            text_font_style="bold",
            text_baseline="middle",
        )
    )

# Critical speed markers
crit_source = ColumnDataSource(
    {
        "rpm": crit_rpm,
        "freq": crit_freq,
        "label": crit_label,
        "rpm_display": [f"{r:.0f}" for r in crit_rpm],
        "freq_display": [f"{f:.1f}" for f in crit_freq],
    }
)
crit_scatter = p.scatter(
    x="rpm",
    y="freq",
    source=crit_source,
    marker="diamond",
    size=26,
    fill_color=ANYPLOT_AMBER,
    line_color=INK,
    line_width=2,
    fill_alpha=0.95,
)
legend_items.append(LegendItem(label="Critical Speed", renderers=[crit_scatter]))
p.add_tools(
    HoverTool(
        renderers=[crit_scatter],
        tooltips=[("Intersection", "@label"), ("RPM", "@rpm_display"), ("Frequency", "@freq_display Hz")],
    )
)

# Style
legend = Legend(
    items=legend_items,
    location="center",
    label_text_font_size="34pt",
    label_text_color=INK_SOFT,
    glyph_width=60,
    glyph_height=36,
    label_standoff=16,
    spacing=12,
    padding=20,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.92,
    border_line_color=INK_SOFT,
    border_line_alpha=0.5,
)
p.add_layout(legend, "right")

p.title.text_font_size = title_fontsize
p.title.align = "center"
p.title.text_color = INK
p.title.text_font_style = "bold"

for axis in (p.xaxis, p.yaxis):
    axis.axis_label_text_font_size = "42pt"
    axis.major_label_text_font_size = "34pt"
    axis.axis_label_text_color = INK
    axis.major_label_text_color = INK_SOFT
    axis.axis_line_color = INK_SOFT
    axis.major_tick_line_color = INK_SOFT
    axis.minor_tick_line_color = None

for grid in (p.xgrid, p.ygrid):
    grid.grid_line_color = INK
    grid.grid_line_alpha = 0.10

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

# Save HTML + PNG via headless Chrome
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
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
