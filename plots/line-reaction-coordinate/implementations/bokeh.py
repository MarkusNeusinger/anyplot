""" pyplots.ai
line-reaction-coordinate: Reaction Coordinate Energy Diagram
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-21
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import Arrow, ColumnDataSource, Label, NormalHead, Span
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data
reactant_energy = 50.0
transition_energy = 120.0
product_energy = 20.0

reaction_coord = np.linspace(0, 1, 400)

# Build smooth energy profile using a combination of Gaussians
peak_center = 0.45
peak_width = 0.12
gaussian_peak = (transition_energy - reactant_energy) * np.exp(
    -((reaction_coord - peak_center) ** 2) / (2 * peak_width**2)
)

# Sigmoid for the overall energy drop from reactants to products
sigmoid = 1 / (1 + np.exp(30 * (reaction_coord - 0.55)))
baseline = reactant_energy * sigmoid + product_energy * (1 - sigmoid)

energy = baseline + gaussian_peak

source = ColumnDataSource(data={"x": reaction_coord, "y": energy})

# Plot
p = figure(
    width=4800,
    height=2700,
    title="line-reaction-coordinate · bokeh · pyplots.ai",
    x_axis_label="Reaction Coordinate",
    y_axis_label="Potential Energy (kJ/mol)",
    x_range=(-0.08, 1.15),
    y_range=(-5, 155),
)

# Area fill under the curve
fill_source = ColumnDataSource(data={"x": reaction_coord, "y": energy})
p.varea(x="x", y1=0, y2="y", source=fill_source, fill_color="#306998", fill_alpha=0.08)

p.line("x", "y", source=source, line_width=5, color="#306998")

# Transition state emphasis — glowing highlight
ts_idx = int(np.argmax(energy))
ts_x_val = float(reaction_coord[ts_idx])
ts_y_val = float(energy[ts_idx])
p.scatter([ts_x_val], [ts_y_val], size=28, color="#306998", alpha=0.18, line_color=None)
p.scatter([ts_x_val], [ts_y_val], size=14, color="#306998", alpha=0.9, line_color="white", line_width=2)

# Horizontal dashed reference lines
reactant_line = Span(
    location=reactant_energy, dimension="width", line_color="#888888", line_width=2, line_dash="dashed"
)
product_line = Span(location=product_energy, dimension="width", line_color="#888888", line_width=2, line_dash="dashed")
p.add_layout(reactant_line)
p.add_layout(product_line)

# Labels for reactants, transition state, products
label_style = {"text_font_size": "20pt", "text_color": "#333333", "text_font_style": "bold"}

reactant_label = Label(x=0.0, y=reactant_energy, text="Reactants", x_offset=-10, y_offset=12, **label_style)
product_label = Label(x=0.88, y=product_energy, text="Products", x_offset=-10, y_offset=12, **label_style)
ts_label = Label(x=peak_center, y=transition_energy, text="Transition State", x_offset=-80, y_offset=15, **label_style)
p.add_layout(reactant_label)
p.add_layout(product_label)
p.add_layout(ts_label)

# Activation energy (Ea) double-headed arrow
ea_x = 0.18
arrow_color = "#E66100"
head_size = 18

p.add_layout(
    Arrow(
        end=NormalHead(size=head_size, fill_color=arrow_color, line_color=arrow_color),
        x_start=ea_x,
        y_start=reactant_energy,
        x_end=ea_x,
        y_end=transition_energy,
        line_color=arrow_color,
        line_width=3,
    )
)
p.add_layout(
    Arrow(
        end=NormalHead(size=head_size, fill_color=arrow_color, line_color=arrow_color),
        x_start=ea_x,
        y_start=transition_energy,
        x_end=ea_x,
        y_end=reactant_energy,
        line_color=arrow_color,
        line_width=3,
    )
)

ea_label = Label(
    x=ea_x,
    y=(reactant_energy + transition_energy) / 2,
    text="Eₐ = 70 kJ/mol",
    text_font_size="18pt",
    text_color=arrow_color,
    text_font_style="bold",
    x_offset=12,
    y_offset=-8,
)
p.add_layout(ea_label)

# Enthalpy change (ΔH) double-headed arrow
dh_x = 0.85
dh_color = "#5D3A9B"

p.add_layout(
    Arrow(
        end=NormalHead(size=head_size, fill_color=dh_color, line_color=dh_color),
        x_start=dh_x,
        y_start=product_energy,
        x_end=dh_x,
        y_end=reactant_energy,
        line_color=dh_color,
        line_width=3,
    )
)
p.add_layout(
    Arrow(
        end=NormalHead(size=head_size, fill_color=dh_color, line_color=dh_color),
        x_start=dh_x,
        y_start=reactant_energy,
        x_end=dh_x,
        y_end=product_energy,
        line_color=dh_color,
        line_width=3,
    )
)

dh_label = Label(
    x=dh_x,
    y=(reactant_energy + product_energy) / 2,
    text="ΔH = −30 kJ/mol",
    text_font_size="18pt",
    text_color=dh_color,
    text_font_style="bold",
    x_offset=12,
    y_offset=-8,
)
p.add_layout(dh_label)

# Style
p.title.text_font_size = "28pt"
p.title.text_color = "#2c3e50"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.axis_label_text_color = "#444444"
p.yaxis.axis_label_text_color = "#444444"
p.xaxis.major_label_text_color = "#666666"
p.yaxis.major_label_text_color = "#666666"

p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.outline_line_color = None
p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.2

p.background_fill_color = "#fafafa"
p.border_fill_color = "#ffffff"
p.toolbar_location = None

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="line-reaction-coordinate · bokeh · pyplots.ai")
