""" anyplot.ai
shap-waterfall: SHAP Waterfall Plot for Feature Attribution
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 85/100 | Created: 2026-05-07
"""

import os
import sys
import time
from pathlib import Path


# Prevent this file from shadowing the bokeh package
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _this_dir and p != ""]

from bokeh.io import output_file, save
from bokeh.models import Span
from bokeh.plotting import figure
from bokeh.resources import INLINE
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

POS_COLOR = "#AE3030"  # imprint red — positive SHAP (pushes prediction up)
NEG_COLOR = "#4467A3"  # Okabe-Ito blue — negative SHAP (pushes prediction down)
LABEL_INK = "#F0EFE8"  # near-white for text on colored bar segments

# Data — credit default risk model: explaining one loan applicant's prediction
features = [
    "Credit Score (715)",
    "Debt-to-Income Ratio",
    "Monthly Income",
    "Late Payments (2)",
    "Employment Duration",
    "Loan Amount",
    "Savings Balance",
    "Credit History Age",
    "Credit Inquiries (3)",
    "Credit Cards Count",
    "Housing (Renter)",
    "Education Level",
]
shap_values = [-0.18, 0.15, -0.12, 0.11, -0.08, 0.07, -0.05, -0.04, 0.04, 0.03, 0.02, -0.02]
base_value = 0.35

# Cumulative waterfall positions
n = len(features)
cumulative = [base_value]
for sv in shap_values:
    cumulative.append(round(cumulative[-1] + sv, 6))

final_value = cumulative[-1]

bar_lefts = [min(cumulative[i], cumulative[i + 1]) for i in range(n)]
bar_rights = [max(cumulative[i], cumulative[i + 1]) for i in range(n)]
bar_colors = [POS_COLOR if sv > 0 else NEG_COLOR for sv in shap_values]
bar_labels = [f"{sv:+.2f}" for sv in shap_values]

# Y-axis: features[0] (largest |SHAP|) at top — Bokeh places y_range[0] at bottom
y_range = list(reversed(features))

# Plot
p = figure(
    width=4800,
    height=2700,
    y_range=y_range,
    title="Credit Default Risk · shap-waterfall · bokeh · anyplot.ai",
    toolbar_location=None,
    x_axis_label="Cumulative Default Probability",
)

# Waterfall bars
p.hbar(y=features, left=bar_lefts, right=bar_rights, height=0.6, color=bar_colors, alpha=0.88)

# Connector lines: vertical dashed segments at each cumulative transition
p.segment(
    x0=[cumulative[i + 1] for i in range(n - 1)],
    y0=[features[i] for i in range(n - 1)],
    x1=[cumulative[i + 1] for i in range(n - 1)],
    y1=[features[i + 1] for i in range(n - 1)],
    line_color=INK_SOFT,
    line_dash="dashed",
    line_width=2,
    line_alpha=0.6,
)

# SHAP value labels centered inside bars (p.text supports categorical y-axis)
p.text(
    x=[(l + r) / 2 for l, r in zip(bar_lefts, bar_rights)],
    y=features,
    text=bar_labels,
    text_align="center",
    text_baseline="middle",
    text_font_size="18pt",
    text_color=LABEL_INK,
    text_font_style="bold",
)

# Base value annotation above the topmost bar — right-aligned so it stays inside plot
p.text(
    x=[base_value],
    y=[features[0]],
    text=[f"Base value: {base_value:.2f}"],
    x_offset=-8,
    y_offset=28,
    text_align="right",
    text_font_size="18pt",
    text_color=INK_SOFT,
)

# Final prediction annotation below the bottommost bar
p.text(
    x=[final_value],
    y=[features[-1]],
    text=[f"Prediction: {final_value:.2f}"],
    x_offset=6,
    y_offset=-28,
    text_font_size="18pt",
    text_color=INK,
    text_font_style="bold",
)

# Reference lines for base value and final prediction
p.add_layout(
    Span(location=base_value, dimension="height", line_color=INK_SOFT, line_dash="dashed", line_width=3, line_alpha=0.8)
)
p.add_layout(Span(location=final_value, dimension="height", line_color=INK, line_dash="solid", line_width=3))

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_font_size = "28pt"
p.title.text_color = INK
p.title.text_font_style = "bold"

p.xaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT

p.yaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_color = None

# Save HTML and take PNG screenshot with headless Chrome
output_file(f"plot-{THEME}.html")
save(p, resources=INLINE)

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
time.sleep(4)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
