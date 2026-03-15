""" pyplots.ai
line-load-duration: Load Duration Curve for Energy Systems
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-15
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Legend, NumeralTickFormatter, Span
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

# Classify each hour into a load region
region_labels = np.array(["Peak"] * hours_in_year, dtype="U16")
region_labels[peak_end:intermediate_end] = "Intermediate"
region_labels[intermediate_end:] = "Base"

# Cumulative energy at each hour (for hover context)
cumulative_energy = np.cumsum(load_mw) / 1000  # GWh

# Total energy consumption (area under curve)
total_energy_gwh = np.trapezoid(load_mw) / 1000

# Percentage of hours at or above each load level
pct_hours = (hour / hours_in_year * 100).astype(int)

# Colorblind-safe palette: Python Blue, Teal, Amber (distinct in luminance and hue)
color_peak = "#D4A017"
color_inter = "#2AA198"
color_base = "#306998"
color_curve = "#1A3A5C"

# Plot - tighter y_range to reduce top whitespace
p = figure(
    width=4800,
    height=2700,
    title="line-load-duration · bokeh · pyplots.ai",
    x_axis_label="Hours of the Year",
    y_axis_label="Power Demand (MW)",
    x_range=(-100, hours_in_year + 100),
    y_range=(0, peak_load * 1.10),
)

# Hide toolbar for clean PNG output
p.toolbar_location = None

# Shaded regions under the curve
# Peak region (0 to peak_end)
peak_source = ColumnDataSource(
    data={"x": hour[: peak_end + 1], "y": load_mw[: peak_end + 1], "zero": np.full(peak_end + 1, 0)}
)
r_peak = p.varea(x="x", y1="zero", y2="y", source=peak_source, fill_color=color_peak, fill_alpha=0.25)

# Intermediate region (peak_end to intermediate_end)
inter_source = ColumnDataSource(
    data={
        "x": hour[peak_end : intermediate_end + 1],
        "y": load_mw[peak_end : intermediate_end + 1],
        "zero": np.full(intermediate_end - peak_end + 1, 0),
    }
)
r_inter = p.varea(x="x", y1="zero", y2="y", source=inter_source, fill_color=color_inter, fill_alpha=0.25)

# Base region (intermediate_end to end)
base_source = ColumnDataSource(
    data={
        "x": hour[intermediate_end:],
        "y": load_mw[intermediate_end:],
        "zero": np.full(hours_in_year - intermediate_end, 0),
    }
)
r_base = p.varea(x="x", y1="zero", y2="y", source=base_source, fill_color=color_base, fill_alpha=0.25)

# Main load duration curve with rich hover data
curve_source = ColumnDataSource(
    data={
        "x": hour,
        "y": load_mw,
        "region": region_labels,
        "cumulative_gwh": np.round(cumulative_energy, 1),
        "pct": pct_hours,
    }
)
curve_line = p.line(x="x", y="y", source=curve_source, line_width=4.5, color=color_curve)

# HoverTool - Bokeh-distinctive interactive feature for HTML export
hover = HoverTool(
    renderers=[curve_line],
    tooltips=[
        ("Hour Rank", "@x{0,0}"),
        ("Load", "@y{0,0} MW"),
        ("Region", "@region"),
        ("Cumulative Energy", "@cumulative_gwh{0,0.0} GWh"),
        ("Duration", "@pct% of year"),
    ],
    mode="vline",
    line_policy="nearest",
)
p.add_tools(hover)

# Horizontal dashed lines for capacity tiers
peak_span = Span(location=peak_load, dimension="width", line_color=color_peak, line_dash="dashed", line_width=2.5)
inter_span = Span(
    location=intermediate_capacity, dimension="width", line_color=color_inter, line_dash="dashed", line_width=2.5
)
base_span = Span(location=base_capacity, dimension="width", line_color=color_base, line_dash="dashed", line_width=2.5)
p.add_layout(peak_span)
p.add_layout(inter_span)
p.add_layout(base_span)

# Capacity tier labels (positioned at left side for better spacing)
peak_label = Label(
    x=200,
    y=peak_load + 15,
    text=f"Peak Capacity: {peak_load:,} MW",
    text_font_size="20pt",
    text_color=color_peak,
    text_font_style="bold",
    text_align="left",
)
inter_label = Label(
    x=200,
    y=intermediate_capacity + 15,
    text=f"Intermediate Capacity: {intermediate_capacity} MW",
    text_font_size="20pt",
    text_color=color_inter,
    text_font_style="bold",
    text_align="left",
)
base_label = Label(
    x=200,
    y=base_capacity + 15,
    text=f"Base Load Capacity: {base_capacity} MW",
    text_font_size="20pt",
    text_color=color_base,
    text_font_style="bold",
    text_align="left",
)
p.add_layout(peak_label)
p.add_layout(inter_label)
p.add_layout(base_label)

# Region labels on the plot - positioned to avoid crowding
peak_region_label = Label(
    x=peak_end // 2,
    y=load_mw[0] * 0.55,
    text="Peak\nLoad",
    text_font_size="26pt",
    text_color="#8B6914",
    text_font_style="bold",
    text_align="center",
)
inter_region_label = Label(
    x=(peak_end + intermediate_end) // 2,
    y=load_mw[0] * 0.40,
    text="Intermediate\nLoad",
    text_font_size="26pt",
    text_color="#1B7A72",
    text_font_style="bold",
    text_align="center",
)
# Base load label - position centered in region with adequate space
base_region_x = (intermediate_end + hours_in_year) // 2
base_region_label = Label(
    x=base_region_x,
    y=load_mw[intermediate_end] * 0.45,
    text="Base Load",
    text_font_size="26pt",
    text_color="#1E4670",
    text_font_style="bold",
    text_align="center",
)
p.add_layout(peak_region_label)
p.add_layout(inter_region_label)
p.add_layout(base_region_label)

# Total energy annotation - positioned below peak capacity to reduce top gap
energy_label = Label(
    x=hours_in_year // 2,
    y=peak_load * 0.94,
    text=f"Total Energy: {total_energy_gwh:,.0f} GWh/year",
    text_font_size="24pt",
    text_color="#333333",
    text_font_style="bold",
    text_align="center",
)
p.add_layout(energy_label)

# Load factor annotation - adds storytelling insight
load_factor = total_energy_gwh * 1000 / (peak_load * hours_in_year) * 100
load_factor_label = Label(
    x=hours_in_year // 2,
    y=peak_load * 0.87,
    text=f"Load Factor: {load_factor:.1f}%",
    text_font_size="20pt",
    text_color="#666666",
    text_font_style="italic",
    text_align="center",
)
p.add_layout(load_factor_label)

# Legend - placed inside plot for tighter layout
legend = Legend(
    items=[("Peak Load", [r_peak]), ("Intermediate Load", [r_inter]), ("Base Load", [r_base])], location="top_right"
)
legend.label_text_font_size = "20pt"
legend.glyph_height = 35
legend.glyph_width = 35
legend.spacing = 12
legend.padding = 15
legend.background_fill_alpha = 0.85
legend.border_line_color = None
p.add_layout(legend, "right")

# Style
p.title.text_font_size = "36pt"
p.title.text_font_style = "normal"
p.title.text_color = "#2C3E50"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.axis_label_text_color = "#444444"
p.yaxis.axis_label_text_color = "#444444"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = "#555555"
p.yaxis.major_label_text_color = "#555555"

# Format tick labels for readability
p.xaxis.formatter = NumeralTickFormatter(format="0,0")
p.yaxis.formatter = NumeralTickFormatter(format="0,0")

# Remove spines and ticks for clean look
p.outline_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.major_tick_line_color = "#CCCCCC"
p.yaxis.major_tick_line_color = "#CCCCCC"
p.xaxis.axis_line_color = "#AAAAAA"
p.yaxis.axis_line_color = "#AAAAAA"

# Grid - y-axis only for line chart, subtle
p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.18
p.ygrid.grid_line_color = "#888888"

# Background
p.background_fill_color = "#FFFFFF"
p.border_fill_color = "white"

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="line-load-duration · bokeh · pyplots.ai")
