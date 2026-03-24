""" pyplots.ai
line-stress-strain: Engineering Stress-Strain Curve
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-20
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, HoverTool, Label, Legend, LegendItem, Span
from bokeh.plotting import figure, save


# Data — Mild steel tensile test simulation
np.random.seed(42)

youngs_modulus = 210000  # MPa
yield_strength = 250  # MPa
uts = 400  # MPa
fracture_strain = 0.35
uts_strain = 0.22
yield_strain = yield_strength / youngs_modulus  # ~0.00119

# Elastic region
strain_elastic = np.linspace(0, yield_strain, 60)
stress_elastic = youngs_modulus * strain_elastic

# Yield plateau and strain hardening (Ludwik-type power law)
strain_plastic = np.linspace(yield_strain, uts_strain, 200)
plastic_strain = strain_plastic - yield_strain
stress_plastic = yield_strength + (uts - yield_strength) * (plastic_strain / (uts_strain - yield_strain)) ** 0.45

# Necking region (stress decreases after UTS)
strain_necking = np.linspace(uts_strain, fracture_strain, 80)
necking_progress = (strain_necking - uts_strain) / (fracture_strain - uts_strain)
stress_necking = uts - (uts - 320) * necking_progress**0.8

# Combine all regions
strain = np.concatenate([strain_elastic, strain_plastic, strain_necking])
stress = np.concatenate([stress_elastic, stress_plastic, stress_necking])

# Region labels for hover tooltip
region_labels = np.concatenate(
    [
        np.full(len(strain_elastic), "Elastic"),
        np.full(len(strain_plastic), "Strain Hardening"),
        np.full(len(strain_necking), "Necking"),
    ]
)

# 0.2% offset line — extended to be clearly visible
offset_strain_start = 0.002
offset_strain_end = 0.004 + yield_strength / youngs_modulus
offset_strain_line = np.linspace(offset_strain_start, offset_strain_end, 80)
offset_stress_line = youngs_modulus * (offset_strain_line - 0.002)
mask = offset_stress_line <= yield_strength + 30
offset_strain_line = offset_strain_line[mask]
offset_stress_line = offset_stress_line[mask]

# Key points
yield_point_strain = yield_strain + 0.002
yield_point_stress = yield_strength
uts_point_strain = uts_strain
uts_point_stress = uts
fracture_point_strain = fracture_strain
fracture_point_stress = stress_necking[-1]

# Colorblind-safe palette
color_main = "#306998"  # Python blue
color_yield = "#D4A84B"  # Gold
color_uts = "#8B5CF6"  # Purple (replaces red)
color_fracture = "#0EA5E9"  # Sky blue (replaces green)
color_region = "#6B7280"  # Neutral gray

# Plot
p = figure(
    width=4800,
    height=2700,
    title="line-stress-strain · bokeh · pyplots.ai",
    x_axis_label="Engineering Strain (mm/mm)",
    y_axis_label="Engineering Stress (MPa)",
)

# Subtle horizontal reference lines at yield and UTS
p.add_layout(
    Span(
        location=yield_strength,
        dimension="width",
        line_color=color_yield,
        line_alpha=0.2,
        line_dash="dotted",
        line_width=2,
    )
)
p.add_layout(
    Span(location=uts, dimension="width", line_color=color_uts, line_alpha=0.2, line_dash="dotted", line_width=2)
)

# Main curve with region data for HoverTool
source = ColumnDataSource(data={"strain": strain, "stress": stress, "region": region_labels})
main_line = p.line(x="strain", y="stress", source=source, line_width=5, color=color_main)

# HoverTool — Bokeh-distinctive interactive feature
hover = HoverTool(
    renderers=[main_line],
    tooltips=[("Strain", "@strain{0.0000}"), ("Stress", "@stress{0.1} MPa"), ("Region", "@region")],
    mode="vline",
    line_policy="nearest",
)
p.add_tools(hover)

# 0.2% offset line — thicker and more visible
offset_source = ColumnDataSource(data={"strain": offset_strain_line, "stress": offset_stress_line})
offset_line = p.line(x="strain", y="stress", source=offset_source, line_width=4, line_dash="dashed", color=color_yield)

# Key points — larger markers for clarity
yield_glyph = p.scatter(
    x=[yield_point_strain],
    y=[yield_point_stress],
    size=32,
    color=color_yield,
    marker="circle",
    line_color="white",
    line_width=3,
)

uts_glyph = p.scatter(
    x=[uts_point_strain],
    y=[uts_point_stress],
    size=32,
    color=color_uts,
    marker="triangle",
    line_color="white",
    line_width=3,
)

fracture_glyph = p.scatter(
    x=[fracture_point_strain],
    y=[fracture_point_stress],
    size=32,
    color=color_fracture,
    marker="square",
    line_color="white",
    line_width=3,
)

# Region labels — repositioned to reduce left-side congestion
p.add_layout(
    Label(x=0.008, y=130, text="Elastic", text_font_size="22pt", text_color=color_region, text_font_style="italic")
)

p.add_layout(
    Label(
        x=0.08, y=280, text="Strain Hardening", text_font_size="22pt", text_color=color_region, text_font_style="italic"
    )
)

p.add_layout(
    Label(x=0.27, y=380, text="Necking", text_font_size="22pt", text_color=color_region, text_font_style="italic")
)

# Key point annotations — repositioned to spread out and avoid left-side crowding
p.add_layout(
    Label(
        x=yield_point_strain + 0.018,
        y=yield_point_stress - 25,
        text=f"Yield Point ({yield_point_stress} MPa)",
        text_font_size="18pt",
        text_color=color_yield,
        text_font_style="bold",
    )
)

p.add_layout(
    Label(
        x=uts_point_strain - 0.075,
        y=uts_point_stress + 18,
        text=f"UTS ({uts_point_stress} MPa)",
        text_font_size="18pt",
        text_color=color_uts,
        text_font_style="bold",
    )
)

p.add_layout(
    Label(
        x=fracture_point_strain - 0.04,
        y=fracture_point_stress - 40,
        text="Fracture",
        text_font_size="18pt",
        text_color=color_fracture,
        text_font_style="bold",
    )
)

# Young's modulus annotation — moved right to reduce elastic region crowding
p.add_layout(
    Label(
        x=0.025,
        y=50,
        text=f"E = {youngs_modulus // 1000} GPa",
        text_font_size="18pt",
        text_color=color_main,
        text_font_style="bold",
    )
)

# Legend — positioned inside the plot near the data
legend = Legend(
    items=[
        LegendItem(label="Stress-Strain Curve", renderers=[main_line]),
        LegendItem(label="0.2% Offset Line", renderers=[offset_line]),
        LegendItem(label="Yield Point", renderers=[yield_glyph]),
        LegendItem(label="Ultimate Tensile Strength", renderers=[uts_glyph]),
        LegendItem(label="Fracture Point", renderers=[fracture_glyph]),
    ],
    location=(2800, 200),
)
legend.label_text_font_size = "18pt"
legend.glyph_height = 30
legend.glyph_width = 30
legend.spacing = 10
legend.padding = 20
legend.margin = 20
legend.background_fill_color = "#FAFAFA"
legend.background_fill_alpha = 0.9
legend.border_line_color = "#E5E7EB"
legend.border_line_alpha = 0.6
legend.border_line_width = 2
p.add_layout(legend, "center")

# Style
p.title.text_font_size = "28pt"
p.title.text_font_style = "normal"
p.title.text_color = "#374151"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.axis_label_text_color = "#4B5563"
p.yaxis.axis_label_text_color = "#4B5563"
p.xaxis.major_label_text_color = "#6B7280"
p.yaxis.major_label_text_color = "#6B7280"
p.xaxis.axis_line_color = "#D1D5DB"
p.yaxis.axis_line_color = "#D1D5DB"
p.xaxis.major_tick_line_color = "#D1D5DB"
p.yaxis.major_tick_line_color = "#D1D5DB"
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.xgrid.grid_line_alpha = 0.15
p.ygrid.grid_line_alpha = 0.15
p.xgrid.grid_line_color = "#9CA3AF"
p.ygrid.grid_line_color = "#9CA3AF"

p.outline_line_color = None
p.toolbar_location = None
p.background_fill_color = "#FAFAFA"
p.border_fill_color = "white"

p.y_range.start = -10
p.y_range.end = 450
p.x_range.start = -0.005
p.x_range.end = 0.38

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", title="line-stress-strain · bokeh · pyplots.ai")
