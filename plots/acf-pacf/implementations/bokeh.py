""" pyplots.ai
acf-pacf: Autocorrelation and Partial Autocorrelation (ACF/PACF) Plot
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-14
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.layouts import column
from bokeh.models import BoxAnnotation, ColumnDataSource, HoverTool, Label, Span
from bokeh.plotting import figure
from statsmodels.tsa.stattools import acf, pacf


# Data - Simulated monthly retail sales with AR(2) structure
# Models inventory cycles: positive lag-1 (momentum) + negative lag-2 (correction)
np.random.seed(42)
n_obs = 200
series = np.zeros(n_obs)
for i in range(2, n_obs):
    series[i] = 0.6 * series[i - 1] - 0.3 * series[i - 2] + np.random.randn()

# Compute ACF and PACF
n_lags = 35
acf_values = acf(series, nlags=n_lags, fft=True)
pacf_values = pacf(series, nlags=n_lags, method="ywm")
conf_bound = 1.96 / np.sqrt(n_obs)

# Identify significant lags (outside confidence bounds)
acf_significant = np.abs(acf_values) > conf_bound
pacf_significant = np.abs(pacf_values[1:]) > conf_bound

# Colors
BLUE = "#306998"
BLUE_MUTED = "#8FAEC4"
RED = "#C44E52"
GOLD = "#E8A838"
BG_COLOR = "#FAFAFA"

# --- ACF plot (top) ---
acf_lags = np.arange(len(acf_values))
acf_colors = [BLUE if sig else BLUE_MUTED for sig in acf_significant]

acf_stem_source = ColumnDataSource(
    data={"x0": acf_lags, "y0": np.zeros(len(acf_lags)), "x1": acf_lags, "y1": acf_values, "color": acf_colors}
)
acf_source = ColumnDataSource(
    data={
        "x": acf_lags,
        "y": acf_values,
        "color": acf_colors,
        "sig": ["Significant" if s else "Not significant" for s in acf_significant],
        "val": [f"{v:.3f}" for v in acf_values],
    }
)

p_acf = figure(
    width=4800,
    height=1350,
    title="acf-pacf · bokeh · pyplots.ai",
    x_axis_label="Lag",
    y_axis_label="ACF",
    background_fill_color=BG_COLOR,
    border_fill_color="white",
)

p_acf.segment(x0="x0", y0="y0", x1="x1", y1="y1", source=acf_stem_source, line_width=5, color="color", alpha=0.85)
p_acf.scatter(x="x", y="y", source=acf_source, size=18, color="color", alpha=0.9)

# Confidence band (shaded region) and bounds
p_acf.add_layout(BoxAnnotation(bottom=-conf_bound, top=conf_bound, fill_alpha=0.08, fill_color=RED, line_alpha=0))
p_acf.add_layout(
    Span(location=conf_bound, dimension="width", line_dash="dashed", line_width=3, line_color=RED, line_alpha=0.5)
)
p_acf.add_layout(
    Span(location=-conf_bound, dimension="width", line_dash="dashed", line_width=3, line_color=RED, line_alpha=0.5)
)
p_acf.add_layout(Span(location=0, dimension="width", line_width=2, line_color="#999999", line_alpha=0.4))

# Confidence band label
p_acf.add_layout(
    Label(
        x=n_lags // 2,
        y=conf_bound,
        text="95% Confidence Interval",
        text_font_size="22pt",
        text_color=RED,
        text_alpha=0.8,
        x_offset=0,
        y_offset=8,
    )
)

# HoverTool for ACF
acf_hover = HoverTool(tooltips=[("Lag", "@x"), ("ACF", "@val"), ("Status", "@sig")], mode="vline")
p_acf.add_tools(acf_hover)

# --- PACF plot (bottom) ---
pacf_lags = np.arange(1, len(pacf_values))
pacf_vals = pacf_values[1:]
pacf_colors = [BLUE if sig else BLUE_MUTED for sig in pacf_significant]

pacf_stem_source = ColumnDataSource(
    data={"x0": pacf_lags, "y0": np.zeros(len(pacf_lags)), "x1": pacf_lags, "y1": pacf_vals, "color": pacf_colors}
)
pacf_source = ColumnDataSource(
    data={
        "x": pacf_lags,
        "y": pacf_vals,
        "color": pacf_colors,
        "sig": ["Significant" if s else "Not significant" for s in pacf_significant],
        "val": [f"{v:.3f}" for v in pacf_vals],
    }
)

p_pacf = figure(
    width=4800,
    height=1350,
    x_axis_label="Lag",
    y_axis_label="PACF",
    x_range=p_acf.x_range,
    background_fill_color=BG_COLOR,
    border_fill_color="white",
)

p_pacf.segment(x0="x0", y0="y0", x1="x1", y1="y1", source=pacf_stem_source, line_width=5, color="color", alpha=0.85)
p_pacf.scatter(x="x", y="y", source=pacf_source, size=18, color="color", alpha=0.9)

# Confidence band (shaded region) and bounds
p_pacf.add_layout(BoxAnnotation(bottom=-conf_bound, top=conf_bound, fill_alpha=0.08, fill_color=RED, line_alpha=0))
p_pacf.add_layout(
    Span(location=conf_bound, dimension="width", line_dash="dashed", line_width=3, line_color=RED, line_alpha=0.5)
)
p_pacf.add_layout(
    Span(location=-conf_bound, dimension="width", line_dash="dashed", line_width=3, line_color=RED, line_alpha=0.5)
)
p_pacf.add_layout(Span(location=0, dimension="width", line_width=2, line_color="#999999", line_alpha=0.4))

# Confidence band label on PACF
p_pacf.add_layout(
    Label(
        x=n_lags // 2,
        y=conf_bound,
        text="95% Confidence Interval",
        text_font_size="22pt",
        text_color=RED,
        text_alpha=0.8,
        x_offset=0,
        y_offset=8,
    )
)

# Highlight AR(2) significant lags in PACF with gold accent markers
ar_lags = [1, 2]
ar_vals = [pacf_values[lag] for lag in ar_lags]
ar_source = ColumnDataSource(data={"x": ar_lags, "y": ar_vals})
p_pacf.scatter(x="x", y="y", source=ar_source, size=26, color=GOLD, alpha=0.9, line_color=BLUE, line_width=3)

# AR(2) annotation
p_pacf.add_layout(
    Label(
        x=3,
        y=pacf_values[1],
        text="AR(2) identified",
        text_font_size="20pt",
        text_color=GOLD,
        text_font_style="bold",
        text_alpha=0.9,
        x_offset=5,
        y_offset=-5,
    )
)

# HoverTool for PACF
pacf_hover = HoverTool(tooltips=[("Lag", "@x"), ("PACF", "@val"), ("Status", "@sig")], mode="vline")
p_pacf.add_tools(pacf_hover)

# Style both plots
for p in [p_acf, p_pacf]:
    p.title.text_font_size = "36pt"
    p.title.text_color = "#333333"
    p.xaxis.axis_label_text_font_size = "28pt"
    p.yaxis.axis_label_text_font_size = "28pt"
    p.xaxis.major_label_text_font_size = "22pt"
    p.yaxis.major_label_text_font_size = "22pt"
    p.xaxis.axis_label_text_color = "#555555"
    p.yaxis.axis_label_text_color = "#555555"
    p.xgrid.grid_line_alpha = 0
    p.ygrid.grid_line_alpha = 0.15
    p.ygrid.grid_line_dash = "dashed"
    p.ygrid.grid_line_color = "#AAAAAA"
    p.outline_line_color = None
    p.toolbar_location = None
    p.xaxis.axis_line_color = "#CCCCCC"
    p.yaxis.axis_line_color = "#CCCCCC"
    p.xaxis.major_tick_line_color = "#CCCCCC"
    p.yaxis.major_tick_line_color = "#CCCCCC"
    p.xaxis.minor_tick_line_color = None
    p.yaxis.minor_tick_line_color = None

# Layout
layout = column(p_acf, p_pacf)

# Save
export_png(layout, filename="plot.png")
output_file("plot.html")
save(layout)
