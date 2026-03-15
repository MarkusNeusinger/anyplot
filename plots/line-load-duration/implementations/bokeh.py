"""pyplots.ai
line-load-duration: Load Duration Curve for Energy Systems
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-03-15
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, Label, Legend, Span
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Synthetic annual hourly load profile for a mid-sized utility
np.random.seed(42)
hours_in_year = 8760

# Generate realistic hourly load data
base_load = 400
peak_load = 1200
time = np.arange(hours_in_year)

# Seasonal pattern (summer/winter peaks)
seasonal = 150 * np.sin(2 * np.pi * time / hours_in_year - np.pi / 3)

# Daily pattern (daytime peaks)
daily = 100 * np.sin(2 * np.pi * time / 24 - np.pi / 2)

# Random variation
noise = np.random.normal(0, 40, hours_in_year)

# Combine components
load_raw = base_load + 300 + seasonal + daily + noise
load_raw = np.clip(load_raw, base_load, peak_load)

# Sort descending for load duration curve
load_mw = np.sort(load_raw)[::-1]
hour = np.arange(hours_in_year)

# Define load regions
base_capacity = 500
intermediate_capacity = 900

# Find transition hours
peak_end = np.searchsorted(-load_mw, -intermediate_capacity)
intermediate_end = np.searchsorted(-load_mw, -base_capacity)

# Total energy consumption (area under curve)
total_energy_gwh = np.trapezoid(load_mw) / 1000

# Plot
p = figure(
    width=4800,
    height=2700,
    title="line-load-duration · bokeh · pyplots.ai",
    x_axis_label="Hours of the Year",
    y_axis_label="Power Demand (MW)",
    x_range=(-100, hours_in_year + 100),
    y_range=(0, peak_load * 1.12),
)

# Shaded regions under the curve
# Peak region (0 to peak_end)
peak_source = ColumnDataSource(
    data={"x": hour[: peak_end + 1], "y": load_mw[: peak_end + 1], "zero": np.full(peak_end + 1, 0)}
)
r_peak = p.varea(x="x", y1="zero", y2="y", source=peak_source, fill_color="#E74C3C", fill_alpha=0.3)

# Intermediate region (peak_end to intermediate_end)
inter_source = ColumnDataSource(
    data={
        "x": hour[peak_end : intermediate_end + 1],
        "y": load_mw[peak_end : intermediate_end + 1],
        "zero": np.full(intermediate_end - peak_end + 1, 0),
    }
)
r_inter = p.varea(x="x", y1="zero", y2="y", source=inter_source, fill_color="#F39C12", fill_alpha=0.3)

# Base region (intermediate_end to end)
base_source = ColumnDataSource(
    data={
        "x": hour[intermediate_end:],
        "y": load_mw[intermediate_end:],
        "zero": np.full(hours_in_year - intermediate_end, 0),
    }
)
r_base = p.varea(x="x", y1="zero", y2="y", source=base_source, fill_color="#306998", fill_alpha=0.3)

# Main load duration curve
curve_source = ColumnDataSource(data={"x": hour, "y": load_mw})
p.line(x="x", y="y", source=curve_source, line_width=3.5, color="#306998")

# Horizontal dashed lines for capacity tiers
peak_span = Span(location=peak_load, dimension="width", line_color="#E74C3C", line_dash="dashed", line_width=2.5)
inter_span = Span(
    location=intermediate_capacity, dimension="width", line_color="#F39C12", line_dash="dashed", line_width=2.5
)
base_span = Span(location=base_capacity, dimension="width", line_color="#306998", line_dash="dashed", line_width=2.5)
p.add_layout(peak_span)
p.add_layout(inter_span)
p.add_layout(base_span)

# Capacity tier labels
peak_label = Label(
    x=hours_in_year - 400,
    y=peak_load + 15,
    text=f"Peak Capacity: {peak_load} MW",
    text_font_size="20pt",
    text_color="#E74C3C",
    text_align="right",
)
inter_label = Label(
    x=hours_in_year - 400,
    y=intermediate_capacity + 15,
    text=f"Intermediate Capacity: {intermediate_capacity} MW",
    text_font_size="20pt",
    text_color="#F39C12",
    text_align="right",
)
base_label = Label(
    x=hours_in_year - 400,
    y=base_capacity + 15,
    text=f"Base Load Capacity: {base_capacity} MW",
    text_font_size="20pt",
    text_color="#306998",
    text_align="right",
)
p.add_layout(peak_label)
p.add_layout(inter_label)
p.add_layout(base_label)

# Region labels on the plot
peak_region_label = Label(
    x=peak_end // 2,
    y=load_mw[0] * 0.55,
    text="Peak\nLoad",
    text_font_size="22pt",
    text_color="#E74C3C",
    text_font_style="bold",
    text_align="center",
)
inter_region_label = Label(
    x=(peak_end + intermediate_end) // 2,
    y=load_mw[0] * 0.40,
    text="Intermediate\nLoad",
    text_font_size="22pt",
    text_color="#F39C12",
    text_font_style="bold",
    text_align="center",
)
base_region_label = Label(
    x=(intermediate_end + hours_in_year) // 2,
    y=load_mw[0] * 0.25,
    text="Base\nLoad",
    text_font_size="22pt",
    text_color="#306998",
    text_font_style="bold",
    text_align="center",
)
p.add_layout(peak_region_label)
p.add_layout(inter_region_label)
p.add_layout(base_region_label)

# Total energy annotation
energy_label = Label(
    x=hours_in_year // 2,
    y=peak_load * 0.95,
    text=f"Total Energy: {total_energy_gwh:,.0f} GWh/year",
    text_font_size="22pt",
    text_color="#333333",
    text_font_style="bold",
    text_align="center",
)
p.add_layout(energy_label)

# Legend
legend = Legend(
    items=[("Peak Load", [r_peak]), ("Intermediate Load", [r_inter]), ("Base Load", [r_base])], location="top_right"
)
legend.label_text_font_size = "20pt"
legend.glyph_height = 35
legend.glyph_width = 35
legend.spacing = 12
legend.padding = 15
legend.background_fill_alpha = 0.85
legend.border_line_color = "#cccccc"
p.add_layout(legend, "right")

# Style
p.title.text_font_size = "36pt"
p.title.text_font_style = "normal"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Remove top and right spines
p.outline_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Grid
p.xgrid.grid_line_alpha = 0.2
p.ygrid.grid_line_alpha = 0.2

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "white"

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="line-load-duration · bokeh · pyplots.ai")
