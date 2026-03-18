""" pyplots.ai
lightcurve-transit: Astronomical Light Curve
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-18
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import (
    Band,
    BoxAnnotation,
    ColumnDataSource,
    CustomJSTickFormatter,
    HoverTool,
    Label,
    Range1d,
    Span,
    Whisker,
)
from bokeh.plotting import figure


# Data - simulated exoplanet transit (phase-folded, hot Jupiter style)
np.random.seed(42)

n_points = 600
phase = np.sort(np.random.uniform(0.0, 1.0, n_points))

# Transit parameters (wide transit for visual clarity)
transit_center = 0.5
transit_depth = 0.012  # ~1.2% dip
half_duration = 0.06  # half of total transit duration in phase

# Simple smooth transit model using a cosine-bell shape
dist = np.abs(phase - transit_center)
in_transit = dist < half_duration
model_flux = np.ones(n_points)
model_flux[in_transit] = 1.0 - transit_depth * (0.5 + 0.5 * np.cos(np.pi * dist[in_transit] / half_duration))

# Photometric noise
flux_err = np.random.uniform(0.001, 0.002, n_points)
flux = model_flux + np.random.normal(0, 1, n_points) * flux_err

# Smooth model for overlay line
phase_model = np.linspace(0.0, 1.0, 3000)
dist_m = np.abs(phase_model - transit_center)
in_transit_m = dist_m < half_duration
model_smooth = np.ones(3000)
model_smooth[in_transit_m] = 1.0 - transit_depth * (0.5 + 0.5 * np.cos(np.pi * dist_m[in_transit_m] / half_duration))

# 1-sigma band around model
model_band_upper = model_smooth + 0.0008
model_band_lower = model_smooth - 0.0008
source_band = ColumnDataSource(data={"phase": phase_model, "upper": model_band_upper, "lower": model_band_lower})

# Data sources
source_data = ColumnDataSource(
    data={
        "phase": phase,
        "flux": flux,
        "flux_err": flux_err,
        "model_flux": model_flux,
        "residual": (flux - model_flux) * 1000,
        "upper": flux + flux_err,
        "lower": flux - flux_err,
    }
)

source_model = ColumnDataSource(data={"phase": phase_model, "model": model_smooth})

# Compute tight y-range from data
y_min = min(flux.min(), model_smooth.min()) - 0.002
y_max = max(flux.max(), model_smooth.max()) + 0.002

# Plot
p = figure(
    width=4800,
    height=2700,
    title="lightcurve-transit · bokeh · pyplots.ai",
    x_axis_label="Orbital Phase",
    y_axis_label="Relative Flux",
    x_range=Range1d(-0.02, 1.02),
    y_range=Range1d(y_min, y_max),
    background_fill_color="#F5F6F8",
)

# Subtle shaded region highlighting the transit window
transit_box = BoxAnnotation(
    left=transit_center - half_duration, right=transit_center + half_duration, fill_color="#306998", fill_alpha=0.04
)
p.add_layout(transit_box)

# Baseline reference line at flux = 1.0
baseline = Span(location=1.0, dimension="width", line_color="#95A5A6", line_width=2, line_dash=[8, 6], line_alpha=0.5)
p.add_layout(baseline)

# Confidence band around transit model
band = Band(
    base="phase",
    upper="upper",
    lower="lower",
    source=source_band,
    fill_color="#306998",
    fill_alpha=0.12,
    line_color=None,
)
p.add_layout(band)

# Error bars (reduced alpha to avoid visual noise)
whisker = Whisker(
    base="phase", upper="upper", lower="lower", source=source_data, line_color="#306998", line_alpha=0.1, line_width=1
)
whisker.upper_head.size = 0
whisker.lower_head.size = 0
p.add_layout(whisker)

# Data points
scatter_renderer = p.scatter(
    x="phase",
    y="flux",
    source=source_data,
    size=16,
    color="#306998",
    alpha=0.5,
    line_color="#1A3A5C",
    line_width=1,
    legend_label="Photometric Data",
)

# Transit model curve (colorblind-friendly amber/gold)
p.line(
    x="phase",
    y="model",
    source=source_model,
    line_color="#D4A017",
    line_width=5,
    line_alpha=0.95,
    legend_label="Transit Model",
)

# Transit depth annotation — arrow-like label showing the dip magnitude
depth_label = Label(
    x=transit_center + half_duration + 0.025,
    y=1.0 - transit_depth / 2,
    text=f"Transit depth\n{transit_depth * 100:.1f}%",
    text_font_size="22pt",
    text_color="#2C3E50",
    text_font_style="italic",
    text_align="left",
)
p.add_layout(depth_label)

# Vertical span lines marking transit depth
p.line(
    x=[transit_center + half_duration + 0.018] * 2,
    y=[1.0, 1.0 - transit_depth],
    line_color="#D4A017",
    line_width=3,
    line_alpha=0.7,
)
p.scatter(
    x=[transit_center + half_duration + 0.018] * 2,
    y=[1.0, 1.0 - transit_depth],
    size=10,
    color="#D4A017",
    marker="diamond",
    alpha=0.8,
)

# HoverTool for interactive exploration (Bokeh distinctive feature)
hover = HoverTool(
    renderers=[scatter_renderer],
    tooltips="""
    <div style="font-size:16px; padding:8px; background:#FFFFFF; border:1px solid #BDC3C7; border-radius:4px;">
        <b>Phase:</b> @phase{0.0000}<br>
        <b>Flux:</b> @flux{0.00000}<br>
        <b>Error:</b> ±@flux_err{0.00000}<br>
        <b>Residual:</b> @residual{+0.000} ppt
    </div>
    """,
    mode="mouse",
)
p.add_tools(hover)

# Custom tick formatter for y-axis showing 4 decimal places (scientific precision)
p.yaxis.formatter = CustomJSTickFormatter(code="return tick.toFixed(4);")

# Typography — larger sizes for 4800×2700 canvas
p.title.text_font_size = "38pt"
p.title.text_color = "#2C3E50"
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_font_size = "20pt"
p.xaxis.axis_label_text_color = "#34495E"
p.yaxis.axis_label_text_color = "#34495E"
p.xaxis.axis_label_standoff = 20
p.yaxis.axis_label_standoff = 20

# Remove spines (outline) for cleaner look
p.outline_line_color = None

# Axis styling
p.xaxis.axis_line_color = "#95A5A6"
p.yaxis.axis_line_color = "#95A5A6"
p.xaxis.major_tick_line_color = "#95A5A6"
p.yaxis.major_tick_line_color = "#95A5A6"
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Grid — subtle y-grid only
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = "#D5D8DC"
p.ygrid.grid_line_alpha = 0.35
p.ygrid.grid_line_dash = [4, 4]

# Legend
p.legend.location = "top_left"
p.legend.label_text_font_size = "24pt"
p.legend.background_fill_alpha = 0.9
p.legend.background_fill_color = "#FFFFFF"
p.legend.border_line_color = "#BDC3C7"
p.legend.border_line_alpha = 0.4
p.legend.padding = 20
p.legend.spacing = 10
p.legend.glyph_height = 30
p.legend.glyph_width = 30

# Save
export_png(p, filename="plot.png")
output_file("plot.html", title="lightcurve-transit · bokeh · pyplots.ai")
save(p)
