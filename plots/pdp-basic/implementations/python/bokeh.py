""" anyplot.ai
pdp-basic: Partial Dependence Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-15
"""

import importlib
import sys
from pathlib import Path


# Remove current directory from sys.path to avoid shadowing bokeh package
sys.path = [p for p in sys.path if Path(p).resolve() != Path(__file__).resolve().parent]

# Import bokeh module and its submodules
bokeh_io = importlib.import_module("bokeh.io")  # noqa: E402
bokeh_models = importlib.import_module("bokeh.models")  # noqa: E402
bokeh_plotting = importlib.import_module("bokeh.plotting")  # noqa: E402

import os  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402
from sklearn.datasets import make_friedman1  # noqa: E402
from sklearn.ensemble import GradientBoostingRegressor  # noqa: E402
from sklearn.inspection import partial_dependence  # noqa: E402


# Use imported modules
output_file = bokeh_io.output_file
save = bokeh_io.save
Band = bokeh_models.Band
ColumnDataSource = bokeh_models.ColumnDataSource
Span = bokeh_models.Span
figure = bokeh_plotting.figure

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # Okabe-Ito position 1
ACCENT = "#C475FD"  # Okabe-Ito position 2

# Data - Train a model and compute partial dependence
np.random.seed(42)

# Use Friedman #1 dataset which has known non-linear relationships
X, y = make_friedman1(n_samples=500, n_features=5, noise=0.5, random_state=42)

# Train a gradient boosting model
model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
model.fit(X, y)

# Compute partial dependence for feature 0 (has sin relationship)
feature_idx = 0
grid_resolution = 100

# Compute partial dependence using sklearn
pdp_results = partial_dependence(model, X, features=[feature_idx], kind="both", grid_resolution=grid_resolution)

# Extract values
avg_predictions = pdp_results["average"][0]
individual_predictions = pdp_results["individual"][0]  # ICE lines
grid_values = pdp_results["grid_values"][0]

# Calculate confidence interval (percentiles of ICE lines)
lower_bound = np.percentile(individual_predictions, 10, axis=0)
upper_bound = np.percentile(individual_predictions, 90, axis=0)

# Center partial dependence at zero for easier interpretation
center_val = avg_predictions.mean()
avg_centered = avg_predictions - center_val
lower_centered = lower_bound - center_val
upper_centered = upper_bound - center_val

# Get training data distribution for rug plot
rug_x = X[:, feature_idx]

# Create data source for main line and band
source = ColumnDataSource(data={"x": grid_values, "y": avg_centered, "lower": lower_centered, "upper": upper_centered})

# Create data source for rug plot - position at bottom of plot area
y_min = lower_centered.min() - 1.5
rug_source = ColumnDataSource(data={"x": rug_x, "y": np.full_like(rug_x, y_min + 0.3)})

# Plot
p = figure(
    width=4800,
    height=2700,
    title="pdp-basic · bokeh · anyplot.ai",
    x_axis_label="Feature X₀ Value",
    y_axis_label="Partial Dependence (centered)",
)

# Add confidence band
band = Band(
    base="x",
    lower="lower",
    upper="upper",
    source=source,
    fill_color=BRAND,
    fill_alpha=0.25,
    line_color=BRAND,
    line_alpha=0.4,
)
p.add_layout(band)

# Add horizontal line at y=0 for reference
zero_line = Span(location=0, dimension="width", line_color=INK_SOFT, line_width=3, line_dash="dashed", line_alpha=0.6)
p.add_layout(zero_line)

# Add invisible patch for confidence band legend entry
p.patch([], [], fill_color=BRAND, fill_alpha=0.25, line_color=BRAND, line_alpha=0.4, legend_label="80% CI")

# Add main PDP line
p.line("x", "y", source=source, line_width=5, line_color=BRAND, legend_label="Average PD")

# Add rug plot for data distribution
p.scatter(
    "x",
    "y",
    source=rug_source,
    size=25,
    color=ACCENT,
    alpha=0.6,
    line_width=3,
    angle=1.5708,
    marker="dash",
    legend_label="Data Distribution",
)

# Style - Text sizing
p.title.text_font_size = "28pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

# Axis styling
p.xaxis.axis_line_width = 3
p.yaxis.axis_line_width = 3
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_width = 3
p.yaxis.major_tick_line_width = 3
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_width = 2
p.yaxis.minor_tick_line_width = 2
p.xaxis.minor_tick_line_color = INK_SOFT
p.yaxis.minor_tick_line_color = INK_SOFT

# Grid styling
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Legend styling
p.legend.location = "bottom_right"
p.legend.label_text_font_size = "18pt"
p.legend.label_text_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.9
p.legend.border_line_color = INK_SOFT
p.legend.border_line_alpha = 0.5
p.legend.border_line_width = 2
p.legend.glyph_height = 50
p.legend.glyph_width = 50
p.legend.spacing = 20
p.legend.padding = 25
p.legend.margin = 40

# Background and border
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
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
time.sleep(3)  # let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
