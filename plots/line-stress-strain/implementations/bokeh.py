"""pyplots.ai
line-stress-strain: Engineering Stress-Strain Curve
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-03-20
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, Label, Legend, LegendItem
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

# 0.2% offset line for yield point determination
offset_strain_line = np.linspace(0.002, 0.007, 50)
offset_stress_line = youngs_modulus * (offset_strain_line - 0.002)
mask = offset_stress_line <= yield_strength + 15
offset_strain_line = offset_strain_line[mask]
offset_stress_line = offset_stress_line[mask]

# Key points
yield_point_strain = yield_strain + 0.002
yield_point_stress = yield_strength
uts_point_strain = uts_strain
uts_point_stress = uts
fracture_point_strain = fracture_strain
fracture_point_stress = stress_necking[-1]

# Plot
p = figure(
    width=4800,
    height=2700,
    title="Mild Steel Tensile Test · line-stress-strain · bokeh · pyplots.ai",
    x_axis_label="Engineering Strain (mm/mm)",
    y_axis_label="Engineering Stress (MPa)",
)

# Main curve
source = ColumnDataSource(data={"strain": strain, "stress": stress})
main_line = p.line(x="strain", y="stress", source=source, line_width=4, color="#306998")

# 0.2% offset line
offset_source = ColumnDataSource(data={"strain": offset_strain_line, "stress": offset_stress_line})
offset_line = p.line(x="strain", y="stress", source=offset_source, line_width=3, line_dash="dashed", color="#D4A84B")

# Key points
yield_glyph = p.scatter(
    x=[yield_point_strain],
    y=[yield_point_stress],
    size=28,
    color="#D4A84B",
    marker="circle",
    line_color="white",
    line_width=2,
)

uts_glyph = p.scatter(
    x=[uts_point_strain],
    y=[uts_point_stress],
    size=28,
    color="#C44E52",
    marker="triangle",
    line_color="white",
    line_width=2,
)

fracture_glyph = p.scatter(
    x=[fracture_point_strain],
    y=[fracture_point_stress],
    size=28,
    color="#55A868",
    marker="square",
    line_color="white",
    line_width=2,
)

# Region labels
p.add_layout(
    Label(x=0.01, y=130, text="Elastic", text_font_size="20pt", text_color="#888888", text_font_style="italic")
)

p.add_layout(
    Label(x=0.07, y=280, text="Strain Hardening", text_font_size="20pt", text_color="#888888", text_font_style="italic")
)

p.add_layout(
    Label(x=0.275, y=375, text="Necking", text_font_size="20pt", text_color="#888888", text_font_style="italic")
)

# Key point annotations
p.add_layout(
    Label(
        x=yield_point_strain + 0.008,
        y=yield_point_stress - 15,
        text=f"Yield Point ({yield_point_stress} MPa)",
        text_font_size="18pt",
        text_color="#D4A84B",
        text_font_style="bold",
    )
)

p.add_layout(
    Label(
        x=uts_point_strain - 0.06,
        y=uts_point_stress + 15,
        text=f"UTS ({uts_point_stress} MPa)",
        text_font_size="18pt",
        text_color="#C44E52",
        text_font_style="bold",
    )
)

p.add_layout(
    Label(
        x=fracture_point_strain - 0.055,
        y=fracture_point_stress - 30,
        text="Fracture",
        text_font_size="18pt",
        text_color="#55A868",
        text_font_style="bold",
    )
)

p.add_layout(
    Label(
        x=0.012,
        y=60,
        text=f"E = {youngs_modulus // 1000} GPa",
        text_font_size="18pt",
        text_color="#306998",
        text_font_style="bold",
    )
)

# Legend
legend = Legend(
    items=[
        LegendItem(label="Stress-Strain Curve", renderers=[main_line]),
        LegendItem(label="0.2% Offset Line", renderers=[offset_line]),
        LegendItem(label="Yield Point", renderers=[yield_glyph]),
        LegendItem(label="Ultimate Tensile Strength", renderers=[uts_glyph]),
        LegendItem(label="Fracture Point", renderers=[fracture_glyph]),
    ],
    location="center_right",
)
legend.label_text_font_size = "18pt"
legend.glyph_height = 30
legend.glyph_width = 30
legend.spacing = 10
legend.padding = 15
legend.background_fill_alpha = 0.8
legend.border_line_alpha = 0.3
p.add_layout(legend)

# Style
p.title.text_font_size = "28pt"
p.title.text_font_style = "normal"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

p.xgrid.grid_line_alpha = 0.2
p.ygrid.grid_line_alpha = 0.2
p.xgrid.grid_line_width = 1
p.ygrid.grid_line_width = 1

p.outline_line_color = None
p.toolbar_location = None

p.y_range.start = -15
p.y_range.end = 450
p.x_range.start = -0.008
p.x_range.end = 0.38

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", title="Engineering Stress-Strain Curve")
