"""anyplot.ai
pdp-basic: Partial Dependence Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-15
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Span
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sklearn.datasets import make_friedman1
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.inspection import partial_dependence


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
CI_LOW, CI_HIGH = 10, 90  # percentiles of the ICE curves that bound the band
GRID_POINTS = 100

# Columns: set these to your table's column names
FEATURE = "Feature X₀ value"  # role: feature_values
PD = "Partial dependence (centered, predicted units)"  # role: partial_dependence
LOWER = "Lower bound (10th percentile)"  # role: confidence_interval
UPPER = "Upper bound (90th percentile)"  # role: extra
FEATURE_1 = "Feature X₁"  # role: extra
FEATURE_2 = "Feature X₂"  # role: extra
FEATURE_3 = "Feature X₃"  # role: extra
FEATURE_4 = "Feature X₄"  # role: extra
TARGET = "Target"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("training_data.csv")
X, y = make_friedman1(n_samples=500, n_features=5, noise=0.5, random_state=42)
df = pd.DataFrame(X, columns=[FEATURE, FEATURE_1, FEATURE_2, FEATURE_3, FEATURE_4])
df[TARGET] = y

# Plot: reads only df and the constants above
features = [c for c in df.columns if c != TARGET]
model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
model.fit(df[features], df[TARGET])

pdp_results = partial_dependence(model, df[features], features=[FEATURE], kind="both", grid_resolution=GRID_POINTS)
ice = pdp_results["individual"][0]
average = pdp_results["average"][0]
center = average.mean()

pdp = pd.DataFrame(
    {
        FEATURE: pdp_results["grid_values"][0],
        PD: average - center,
        LOWER: np.percentile(ice, CI_LOW, axis=0) - center,
        UPPER: np.percentile(ice, CI_HIGH, axis=0) - center,
    }
)
source = ColumnDataSource(pdp)

# Rug: observed feature values as short ticks just below the band
span = pdp[UPPER].max() - pdp[LOWER].min()
rug_y = pdp[LOWER].min() - 0.12 * span
rug_source = ColumnDataSource({FEATURE: df[FEATURE], "rug_y": np.full(len(df), rug_y)})

p = figure(
    width=3200,
    height=1800,
    title="pdp-basic · python · bokeh · anyplot.ai",
    x_axis_label=FEATURE,
    y_axis_label=PD,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Confidence band, behind the line
p.varea(
    x=FEATURE,
    y1=LOWER,
    y2=UPPER,
    source=source,
    fill_color=IMPRINT_PALETTE[0],
    fill_alpha=0.25,
    legend_label="80% band (ICE 10th–90th pct)",
)
p.add_layout(Span(location=0, dimension="width", line_color=INK_SOFT, line_width=3, line_dash="dashed", line_alpha=0.6))
p.line(
    FEATURE, PD, source=source, line_width=8, line_color=IMPRINT_PALETTE[0], legend_label="Average partial dependence"
)
p.scatter(
    FEATURE,
    "rug_y",
    source=rug_source,
    size=40,
    color=IMPRINT_PALETTE[1],
    alpha=0.5,
    line_width=3,
    angle=np.pi / 2,
    marker="dash",
    legend_label="Training data (rug)",
)

# Style
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
for axis in (p.xaxis, p.yaxis):
    axis.axis_line_width = 3
    axis.axis_line_color = INK_SOFT
    axis.major_tick_line_width = 3
    axis.major_tick_line_color = INK_SOFT
    axis.minor_tick_line_color = None
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

p.legend.location = "top_left"
p.legend.label_text_font_size = "30pt"
p.legend.label_text_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.9
p.legend.border_line_color = INK_SOFT
p.legend.border_line_alpha = 0.5
p.legend.border_line_width = 2
p.legend.glyph_height = 40
p.legend.glyph_width = 50
p.legend.spacing = 14
p.legend.padding = 20
p.legend.margin = 30

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

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
