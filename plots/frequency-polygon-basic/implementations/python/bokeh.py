""" anyplot.ai
frequency-polygon-basic: Frequency Polygon for Distribution Comparison
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-22
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Range1d
from bokeh.plotting import figure
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

# Constants
N_BINS = 20  # histogram bins shared by every group

# Columns: set these to your table's column names
SCORE = "Test Score (points)"  # role: values
SESSION = "Session"  # role: group

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
rng = np.random.default_rng(42)
df = pd.DataFrame(
    {
        SCORE: np.concatenate(
            [
                rng.normal(loc=65, scale=8, size=300),
                rng.normal(loc=75, scale=12, size=300),
                rng.normal(loc=50, scale=6, size=150),
                rng.normal(loc=60, scale=6, size=150),
            ]
        ),
        SESSION: ["Morning Session"] * 300 + ["Afternoon Session"] * 300 + ["Evening Session"] * 300,
    }
)

# Plot: reads only df and the constants above
sessions = list(df[SESSION].unique())

# Common bin edges for all groups, padded by one bin-width-ish margin
bins = np.linspace(df[SCORE].min() - 5, df[SCORE].max() + 5, N_BINS + 1)
bin_centers = (bins[:-1] + bins[1:]) / 2
bin_width = bins[1] - bins[0]

# Extend to zero one bin beyond each end so every polygon closes on the baseline
x_extended = np.concatenate([[bin_centers[0] - bin_width], bin_centers, [bin_centers[-1] + bin_width]])
counts = {s: np.histogram(df.loc[df[SESSION] == s, SCORE], bins=bins)[0] for s in sessions}
top = max(c.max() for c in counts.values())

p = figure(
    width=3200,
    height=1800,
    title="frequency-polygon-basic · python · bokeh · anyplot.ai",
    x_axis_label=SCORE,
    y_axis_label="Frequency (count)",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
    y_range=Range1d(0, top * 1.1),
)

for i, session in enumerate(sessions):
    y_extended = np.concatenate([[0], counts[session], [0]])
    source = ColumnDataSource(data={"x": x_extended, "y": y_extended})
    color = IMPRINT_PALETTE[i]
    p.patch(x="x", y="y", source=source, fill_alpha=0.25, fill_color=color, line_width=0)
    p.line(x="x", y="y", source=source, line_color=color, line_width=4, legend_label=str(session))
    p.scatter(x=bin_centers, y=counts[session], size=12, color=color, alpha=0.9)

# Theme-adaptive styling
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_color = INK
p.title.text_font_size = "50pt"

p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"

p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"

p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Legend styling
p.legend.location = "top_right"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT
p.legend.label_text_font_size = "34pt"
p.legend.title = SESSION
p.legend.title_text_color = INK
p.legend.title_text_font_size = "34pt"
p.legend.padding = 20
p.legend.spacing = 10
p.legend.glyph_height = 40
p.legend.glyph_width = 50
p.legend.margin = 30

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
