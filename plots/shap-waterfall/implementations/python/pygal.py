""" anyplot.ai
shap-waterfall: SHAP Waterfall Plot for Feature Attribution
Library: pygal 3.1.0 | Python 3.13.13
Quality: 76/100 | Created: 2026-05-07
"""

import os
import sys


# Prevent this file (pygal.py) from shadowing the installed pygal package
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or os.getcwd()) != _here]

import numpy as np
import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data – customer churn prediction SHAP explanation
np.random.seed(42)

feature_names = [
    "Monthly Charges",
    "Contract Type",
    "Tenure",
    "Online Security",
    "Internet Service",
    "Tech Support",
    "Num. of Services",
    "Payment Method",
    "Device Protection",
    "Streaming TV",
]
shap_raw = [0.20, 0.15, -0.12, -0.10, 0.08, -0.06, 0.05, 0.04, -0.03, 0.02]
base_value = 0.25
final_value = round(base_value + sum(shap_raw), 4)

# Sort ascending: pygal draws first x_label at bottom, so ascending order puts
# the largest-magnitude feature at top (last in list = top of chart)
idx = sorted(range(len(shap_raw)), key=lambda i: abs(shap_raw[i]), reverse=False)
features = [feature_names[i] for i in idx]
shap_vals = [shap_raw[i] for i in idx]

# Per-bar color: Okabe-Ito vermillion for positive, blue for negative
# (SHAP domain convention overrides the default first-series green)
bar_data = [{"value": v, "color": "#D55E00" if v > 0 else "#0072B2"} for v in shap_vals]

# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=("#D55E00",),
    title_font_size=28,
    label_font_size=18,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=16,
    stroke_width=0,
)

# Plot
chart = pygal.HorizontalBar(
    width=4800,
    height=2700,
    style=custom_style,
    title=(
        "Customer Churn Prediction  ·  shap-waterfall  ·  pygal  ·  anyplot.ai\n"
        f"Base value: {base_value:.2f}  →  Predicted probability: {final_value:.2f}"
    ),
    x_title="SHAP Value (impact on predicted churn probability)",
    show_legend=False,
    show_y_guides=False,
    show_x_guides=True,
)

chart.x_labels = features
chart.add("SHAP Contribution", bar_data)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
