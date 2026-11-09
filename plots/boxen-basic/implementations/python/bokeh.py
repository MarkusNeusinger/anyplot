"""anyplot.ai
boxen-basic: Basic Boxen Plot (Letter-Value Plot)
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 96/100 | Updated: 2026-05-17
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Legend, LegendItem
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Constants: letter-value levels, from the quartiles out into the tails
LEVEL_NAMES = ["Fourths", "Eighths", "Sixteenths", "32nds", "64ths", "128ths"]
LEVEL_TAILS = 0.5 ** (np.arange(len(LEVEL_NAMES)) + 2)  # level i spans the (tail, 1 - tail) quantiles

# Imprint sequential ramp (imprint_seq, brand green → blue): one step per ordered quantile level
SEQ_START, SEQ_END = np.array([0x00, 0x9E, 0x73]), np.array([0x44, 0x67, 0xA3])
LEVEL_COLORS = [
    "#{:02X}{:02X}{:02X}".format(*np.round(SEQ_START + (SEQ_END - SEQ_START) * t).astype(int))
    for t in np.linspace(0, 1, len(LEVEL_NAMES))
]

# Columns: set these to your table's column names
ENDPOINT = "API Endpoint"  # role: category
RESPONSE_TIME = "Response Time (ms)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
np.random.seed(42)
samples = {
    "API Auth": np.concatenate(
        [np.random.exponential(50, 4000) + 20, np.random.normal(200, 30, 800), np.random.uniform(400, 600, 200)]
    ),
    "API Users": np.concatenate([np.random.normal(80, 25, 4500), np.random.uniform(180, 300, 500)]),
    "API Orders": np.concatenate([np.random.lognormal(4, 0.5, 4800), np.random.uniform(300, 500, 200)]),
    "API Search": np.concatenate([np.random.gamma(3, 30, 4600), np.random.uniform(350, 550, 400)]),
}
df = pd.DataFrame(
    [(endpoint, value) for endpoint, values in samples.items() for value in values], columns=[ENDPOINT, RESPONSE_TIME]
)

# Plot: reads only df and the constants above
categories = [str(c) for c in df[ENDPOINT].dropna().unique()]
width_factors = np.linspace(0.75, 0.25, len(LEVEL_NAMES))  # deeper levels get narrower boxes

p = figure(
    width=3200,
    height=1800,
    title="boxen-basic · python · bokeh · anyplot.ai",
    x_axis_label=ENDPOINT,
    y_axis_label=RESPONSE_TIME,
    x_range=categories,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

level_renderers = [[] for _ in LEVEL_NAMES]
median_renderers = []
outlier_renderers = []

for cat_idx, category in enumerate(categories):
    values = df.loc[df[ENDPOINT].astype(str) == category, RESPONSE_TIME].dropna().to_numpy()
    if len(values) == 0:
        continue

    lowers = np.quantile(values, LEVEL_TAILS)
    uppers = np.quantile(values, 1 - LEVEL_TAILS)

    # Draw from the deepest level inward, so the quartile box sits on top
    for level_idx in reversed(range(len(LEVEL_NAMES))):
        half = width_factors[level_idx] / 2
        box = ColumnDataSource(
            data={
                "left": [cat_idx + 0.5 - half],
                "right": [cat_idx + 0.5 + half],
                "bottom": [lowers[level_idx]],
                "top": [uppers[level_idx]],
            }
        )
        level_renderers[level_idx].append(
            p.quad(
                left="left",
                right="right",
                bottom="bottom",
                top="top",
                source=box,
                fill_color=LEVEL_COLORS[level_idx],
                fill_alpha=1.0,
                line_color=PAGE_BG,
                line_width=3,
            )
        )

    median = np.median(values)
    half = width_factors[0] / 2
    median_renderers.append(
        p.line(x=[cat_idx + 0.5 - half, cat_idx + 0.5 + half], y=[median, median], line_color=INK, line_width=6)
    )

    # Observations beyond the deepest letter value, spread across the box width for legibility
    outliers = values[(values < lowers[-1]) | (values > uppers[-1])]
    jitter = np.random.uniform(-0.1, 0.1, len(outliers))
    outlier_renderers.append(
        p.scatter(
            x=cat_idx + 0.5 + jitter,
            y=outliers,
            size=14,
            fill_color=LEVEL_COLORS[-1],
            fill_alpha=0.6,
            line_color=PAGE_BG,
            line_width=1,
        )
    )

# Legend: median, then the quantile levels from the quartiles outward, then outliers
quantile_labels = [
    f"{name} ({100 * t:.3g}–{100 * (1 - t):.3g}%)" for name, t in zip(LEVEL_NAMES, LEVEL_TAILS, strict=True)
]
legend_items = [LegendItem(label="Median", renderers=median_renderers)]
legend_items += [
    LegendItem(label=label, renderers=renderers)
    for label, renderers in zip(quantile_labels, level_renderers, strict=True)
]
legend_items.append(LegendItem(label="Outliers", renderers=outlier_renderers))

legend = Legend(items=legend_items, location="top_left")
legend.title = "Quantile level"
legend.title_text_font_size = "34pt"
legend.title_text_color = INK
legend.label_text_font_size = "30pt"
legend.label_text_color = INK_SOFT
legend.glyph_height = 44
legend.glyph_width = 44
legend.spacing = 14
legend.padding = 28
legend.margin = 30
legend.background_fill_color = ELEVATED_BG
legend.border_line_color = INK_SOFT
p.add_layout(legend, "right")

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.12

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

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
