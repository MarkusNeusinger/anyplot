""" anyplot.ai
lift-curve: Model Lift Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-10
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Span
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # Okabe-Ito position 1
SECONDARY = "#C475FD"  # Okabe-Ito position 2 (for baseline)

# Data - Simulated customer response data for marketing campaign
np.random.seed(42)
n_samples = 1000

# Create realistic model predictions with reasonable discrimination
y_true = np.random.binomial(1, 0.15, n_samples)  # 15% baseline response rate

# Generate scores that correlate with true outcomes but imperfectly
noise = np.random.normal(0, 0.3, n_samples)
y_score = 0.3 + 0.5 * y_true + noise
y_score = np.clip(y_score, 0, 1)  # Keep scores in valid range

# Calculate lift curve data
sorted_indices = np.argsort(y_score)[::-1]
y_true_sorted = y_true[sorted_indices]

n_positives = y_true.sum()
baseline_rate = n_positives / n_samples

percentiles = np.arange(1, 101)
cumulative_lift = []
n_selected_list = []

for pct in percentiles:
    n_selected = int(n_samples * pct / 100)
    n_positives_selected = y_true_sorted[:n_selected].sum()
    response_rate = n_positives_selected / n_selected if n_selected > 0 else 0
    lift = response_rate / baseline_rate if baseline_rate > 0 else 0
    cumulative_lift.append(lift)
    n_selected_list.append(n_selected)

# Create data source with hover tooltips
source = ColumnDataSource(data={"percentile": percentiles, "lift": cumulative_lift, "n_selected": n_selected_list})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="lift-curve · bokeh · anyplot.ai",
    x_axis_label="Population Targeted (%)",
    y_axis_label="Cumulative Lift Ratio (Model / Random)",
    x_range=(0, 105),
    y_range=(0, max(cumulative_lift) * 1.15),
)

# Add hover tool for interactivity
hover = HoverTool(
    tooltips=[("Population %", "@percentile%"), ("Lift Ratio", "@lift{0.00}"), ("Customers", "@n_selected{,}")]
)
p.add_tools(hover)

# Add horizontal reference line at y=1 (random selection baseline)
baseline = Span(location=1, dimension="width", line_color=INK_SOFT, line_width=3, line_dash="dashed")
p.add_layout(baseline)

# Plot the lift curve
p.line(x="percentile", y="lift", source=source, line_width=5, line_color=BRAND, legend_label="Model Lift")

# Add scatter points at deciles for emphasis
decile_indices = [9, 19, 29, 39, 49, 59, 69, 79, 89, 99]  # 10%, 20%, ... 100%
decile_source = ColumnDataSource(
    data={"percentile": [percentiles[i] for i in decile_indices], "lift": [cumulative_lift[i] for i in decile_indices]}
)

p.scatter(
    x="percentile",
    y="lift",
    source=decile_source,
    size=20,
    fill_color=SECONDARY,
    line_color=BRAND,
    line_width=3,
    legend_label="Decile Markers",
)

# Styling for large canvas
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

# Spine and axis colors
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Grid styling
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Legend styling
p.legend.location = "top_right"
p.legend.label_text_font_size = "18pt"
p.legend.label_text_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT

# Background
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with Selenium for PNG
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
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
