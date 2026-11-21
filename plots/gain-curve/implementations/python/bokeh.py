"""anyplot.ai
gain-curve: Cumulative Gains Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
RESPONDED = "Responded (1 = yes)"  # role: y_true
SCORE = "Model score (probability)"  # role: y_score

# Data: replace this block with your own table, for example df = pd.read_csv("responses.csv")
# Simulated customer response model: 15% responders, scores from a classifier
rng = np.random.default_rng(42)
n_samples = 1000
n_positive = int(n_samples * 0.15)
n_negative = n_samples - n_positive
df = pd.DataFrame(
    {
        RESPONDED: np.concatenate([np.ones(n_positive), np.zeros(n_negative)]),
        SCORE: np.concatenate([rng.beta(5, 2, n_positive), rng.beta(2, 5, n_negative)]),
    }
)

# Plot: reads only df and the constants above
X_LABEL = "Percentage of Population Targeted (%)"
Y_LABEL = "Percentage of Positive Cases Captured (%)"

# Rank the population by score (descending) and accumulate the positives captured
ranked = df.sort_values(SCORE, ascending=False)[RESPONDED].to_numpy()
n_total = len(ranked)
positive_rate = ranked.mean()
model = pd.DataFrame(
    {
        X_LABEL: np.arange(0, n_total + 1) / n_total * 100,
        Y_LABEL: np.concatenate([[0.0], np.cumsum(ranked) / ranked.sum() * 100]),
    }
)
# Random selection: the diagonal; perfect model: full capture at the positive rate, flat after
baseline = pd.DataFrame({X_LABEL: [0, 100], Y_LABEL: [0, 100]})
perfect = pd.DataFrame({X_LABEL: [0, positive_rate * 100, 100], Y_LABEL: [0, 100, 100]})

p = figure(
    width=3200,
    height=1800,
    title="gain-curve · python · bokeh · anyplot.ai",
    x_axis_label=X_LABEL,
    y_axis_label=Y_LABEL,
    x_range=(0, 100),
    y_range=(0, 105),
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=60,
)

curves = [
    ("Model Gain Curve", model, IMPRINT_PALETTE[0], 8, "solid", 1.0),
    ("Random Baseline", baseline, INK_SOFT, 6, "dashed", 0.8),
    ("Perfect Model", perfect, IMPRINT_PALETTE[2], 6, "dotted", 1.0),
]
renderers = []
for label, curve, color, width, dash, alpha in curves:
    line = p.line(
        x=X_LABEL,
        y=Y_LABEL,
        source=ColumnDataSource(curve),
        line_color=color,
        line_width=width,
        line_dash=dash,
        line_alpha=alpha,
        legend_label=label,
    )
    renderers.append(line)
    p.add_tools(
        HoverTool(
            renderers=[line],
            tooltips=[
                (label, ""),
                ("Population %", f"@{{{X_LABEL}}}{{0.0}}"),
                ("Captured %", f"@{{{Y_LABEL}}}{{0.0}}"),
            ],
        )
    )

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
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.legend.location = "bottom_right"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.border_line_width = 2
p.legend.label_text_color = INK_SOFT
p.legend.label_text_font_size = "34pt"
p.legend.glyph_height = 50
p.legend.glyph_width = 90
p.legend.spacing = 14
p.legend.padding = 24
p.legend.margin = 40

# Save HTML and screenshot with headless Chrome
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
