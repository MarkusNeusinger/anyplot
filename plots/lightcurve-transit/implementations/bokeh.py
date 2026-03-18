"""pyplots.ai
lightcurve-transit: Astronomical Light Curve
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-03-18
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Whisker
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

# Data sources
source_data = ColumnDataSource(data={"phase": phase, "flux": flux, "upper": flux + flux_err, "lower": flux - flux_err})

source_model = ColumnDataSource(data={"phase": phase_model, "model": model_smooth})

# Plot
p = figure(
    width=4800,
    height=2700,
    title="Exoplanet Transit · lightcurve-transit · bokeh · pyplots.ai",
    x_axis_label="Orbital Phase",
    y_axis_label="Relative Flux",
)

# Error bars
whisker = Whisker(
    base="phase", upper="upper", lower="lower", source=source_data, line_color="#306998", line_alpha=0.2, line_width=2
)
whisker.upper_head.size = 0
whisker.lower_head.size = 0
p.add_layout(whisker)

# Data points
p.scatter(
    x="phase",
    y="flux",
    source=source_data,
    size=10,
    color="#306998",
    alpha=0.6,
    line_color="white",
    line_width=0.5,
    legend_label="Photometric Data",
)

# Transit model curve
p.line(
    x="phase",
    y="model",
    source=source_model,
    line_color="#E34A33",
    line_width=4,
    line_alpha=0.9,
    legend_label="Transit Model",
)

# Style
p.title.text_font_size = "32pt"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid
p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.2
p.ygrid.grid_line_dash = [6, 4]

# Legend
p.legend.location = "bottom_right"
p.legend.label_text_font_size = "20pt"
p.legend.background_fill_alpha = 0.7
p.legend.border_line_alpha = 0.3

# Save
export_png(p, filename="plot.png")
output_file("plot.html", title="lightcurve-transit · bokeh · pyplots.ai")
save(p)
