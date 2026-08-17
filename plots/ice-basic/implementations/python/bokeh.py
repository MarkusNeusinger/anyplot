"""anyplot.ai
ice-basic: Individual Conditional Expectation (ICE) Plot
Library: bokeh 3.9.2 | Python 3.13.15
Quality: 89/100 | Created: 2026-08-17
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sklearn.ensemble import GradientBoostingRegressor


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (see prompts/default-style-guide.md "Categorical Palette")
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]  # ALWAYS first series

# Data — gradient boosting house-price model with a square-footage x age interaction,
# so predicted price grows faster with square footage for newer houses than older ones.
np.random.seed(42)
n_obs = 80
grid_size = 60

square_footage = np.random.uniform(600, 4000, n_obs)
bedrooms = np.random.randint(1, 6, n_obs).astype(float)
house_age = np.random.uniform(0, 60, n_obs)
lot_size = np.random.uniform(2000, 20000, n_obs)
noise = np.random.normal(0, 15000, n_obs)

price = (
    80 * square_footage
    + 9000 * bedrooms
    - 900 * house_age
    + 1.2 * lot_size
    + 0.04 * square_footage * np.clip(60 - house_age, 0, None)
    + noise
)

features = np.column_stack([square_footage, bedrooms, house_age, lot_size])
model = GradientBoostingRegressor(n_estimators=300, max_depth=3, learning_rate=0.05, random_state=42)
model.fit(features, price)

feature_grid = np.linspace(600, 4000, grid_size)
ice_predictions = np.zeros((n_obs, grid_size))
for i in range(n_obs):
    grid_features = np.tile(features[i], (grid_size, 1))
    grid_features[:, 0] = feature_grid
    ice_predictions[i] = model.predict(grid_features)

ice_price_k = ice_predictions / 1000
pdp_price_k = ice_price_k.mean(axis=0)

y_min, y_max = float(ice_price_k.min()), float(ice_price_k.max())
y_span = y_max - y_min
rug_y0 = y_min - 0.09 * y_span
rug_y1 = y_min - 0.03 * y_span

source = ColumnDataSource(
    data={
        "xs": [feature_grid.tolist()] * n_obs,
        "ys": [row.tolist() for row in ice_price_k],
        "obs_id": list(range(n_obs)),
    }
)

# Plot
title = "ice-basic · python · bokeh · anyplot.ai"
p = figure(
    width=3200,
    height=1800,
    title=title,
    x_axis_label="Square Footage",
    y_axis_label="Predicted Price ($k)",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)
p.y_range = Range1d(rug_y0 - 0.02 * y_span, y_max + 0.08 * y_span)

ice_renderer = p.multi_line(
    xs="xs",
    ys="ys",
    source=source,
    line_color=BRAND,
    line_alpha=0.25,
    line_width=1.5,
    legend_label="Individual houses (ICE)",
)
p.line(feature_grid, pdp_price_k, line_color=INK, line_width=6, legend_label="Average effect (PDP)")
p.segment(
    x0=square_footage, y0=rug_y0, x1=square_footage, y1=rug_y1, line_color=INK_SOFT, line_alpha=0.4, line_width=1.5
)

# HoverTool showcases bokeh's distinctive HTML interactivity (toolbar_location=None
# only hides the button row — hover still fires on mouse move over a line).
p.add_tools(
    HoverTool(
        renderers=[ice_renderer],
        tooltips=[("Observation", "@obs_id"), ("Sq Ft", "$x{0,0}"), ("Price", "$y{0.0}k")],
        mode="mouse",
    )
)

# Style
p.title.text_font_size = "50pt"
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_color = INK
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.15

p.legend.location = "top_left"
p.legend.label_text_font_size = "34pt"
p.legend.glyph_width = 60
p.legend.glyph_height = 40
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT

# Save — write HTML, then screenshot it with headless Chrome (export_png is unreliable in CI)
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
