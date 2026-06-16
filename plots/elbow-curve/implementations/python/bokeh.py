""" anyplot.ai
elbow-curve: Elbow Curve for K-Means Clustering
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-10
"""

import os
import sys
import time
from pathlib import Path


# Remove local bokeh.py from sys.modules cache if it got loaded
if "bokeh" in sys.modules:
    del sys.modules["bokeh"]

# Rebuild sys.path to avoid shadowing
sys.path = [p for p in sys.path if not p.endswith("/python") and p != "" and p != "."]
# Re-add site-packages at the front to ensure bokeh package is found first
import site  # noqa: E402


for sp in site.getsitepackages():
    if sp not in sys.path:
        sys.path.insert(0, sp)

import numpy as np  # noqa: E402
from bokeh.io import output_file, save  # noqa: E402
from bokeh.models import ColumnDataSource  # noqa: E402
from bokeh.plotting import figure  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
BRAND = "#009E73"
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Data - Generate realistic K-means inertia values
np.random.seed(42)

k_values = np.arange(1, 11)
base_inertia = 5000

# Create realistic decreasing inertia with elbow around k=4
inertia = []
for k in k_values:
    if k == 1:
        val = base_inertia
    elif k <= 4:
        # Sharp decrease before elbow
        val = base_inertia * (0.35 ** (k - 1)) + np.random.uniform(50, 100)
    else:
        # Gradual decrease after elbow (diminishing returns)
        val = inertia[-1] * 0.85 + np.random.uniform(20, 50)
    inertia.append(val)

inertia = np.array(inertia)

# Optimal k (elbow point)
optimal_k = 4
optimal_inertia = inertia[optimal_k - 1]

# Create ColumnDataSource
source = ColumnDataSource(data={"k": k_values, "inertia": inertia})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="elbow-curve · bokeh · anyplot.ai",
    x_axis_label="Number of Clusters (k)",
    y_axis_label="Inertia (Within-Cluster Sum of Squares)",
    tools="",
    toolbar_location=None,
)

# Plot line and markers
p.line(x="k", y="inertia", source=source, line_width=4, line_color=BRAND, line_alpha=0.8)
p.scatter(
    x="k",
    y="inertia",
    source=source,
    size=18,
    fill_color=BRAND,
    line_color=BRAND,
    line_width=2,
    fill_alpha=0.8,
    legend_label="Inertia",
)

# Highlight the optimal k with a secondary color
p.scatter(
    x=[optimal_k],
    y=[optimal_inertia],
    size=28,
    fill_color=IMPRINT[1],  # Vermillion
    line_color=IMPRINT[1],
    line_width=3,
    fill_alpha=0.8,
    legend_label=f"Elbow Point (k={optimal_k})",
)

# Style title and axes
p.title.text_font_size = "28pt"
p.title.text_color = INK
p.title.align = "center"

p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK

p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Grid styling
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Set x-axis to show integer values only
p.xaxis.ticker = list(k_values)

# Legend styling
p.legend.location = "top_right"
p.legend.label_text_font_size = "18pt"
p.legend.label_text_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.padding = 15
p.legend.margin = 10

# Background styling
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Save HTML and screenshot with Selenium
html_file = Path(f"plot-{THEME}.html").resolve()
output_file(str(html_file))
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
driver.get(f"file://{html_file}")
time.sleep(3)

png_file = Path(f"plot-{THEME}.png").resolve()
driver.save_screenshot(str(png_file))
driver.quit()
