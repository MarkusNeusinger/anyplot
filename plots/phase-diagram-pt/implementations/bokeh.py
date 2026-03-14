"""pyplots.ai
phase-diagram-pt: Thermodynamic Phase Diagram (Pressure-Temperature)
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-14
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import Arrow, ColumnDataSource, HoverTool, Label, NormalHead, Span
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Water phase diagram (realistic values)
# Triple point: 273.16 K, 611.73 Pa
# Critical point: 647.1 K, 22.064 MPa = 22064000 Pa

triple_T = 273.16
triple_P = 611.73
critical_T = 647.1
critical_P = 22.064e6

# Solid-Gas boundary (sublimation curve) - Clausius-Clapeyron approximation
# From ~200 K up to triple point
T_solid_gas = np.linspace(200, triple_T, 100)
L_sub = 51059  # J/mol sublimation enthalpy of water (approximate)
R = 8.314
P_solid_gas = triple_P * np.exp((L_sub / R) * (1 / triple_T - 1 / T_solid_gas))

# Liquid-Gas boundary (vaporization curve) - from triple point to critical point
T_liquid_gas = np.linspace(triple_T, critical_T, 150)
L_vap = 40700  # J/mol vaporization enthalpy of water
P_liquid_gas = triple_P * np.exp((L_vap / R) * (1 / triple_T - 1 / T_liquid_gas))

# Solid-Liquid boundary (melting curve) - nearly vertical, negative slope for water
P_solid_liquid_values = np.logspace(np.log10(triple_P), np.log10(critical_P * 5), 100)
delta_P = np.maximum(P_solid_liquid_values - triple_P, 0)
T_solid_liquid = triple_T - delta_P * 7.4e-8 + np.power(delta_P / 1e9, 1.5) * 5

# Plot - extended x_range to 760 for supercritical region breathing room
p = figure(
    width=4800,
    height=2700,
    title="phase-diagram-pt · bokeh · pyplots.ai",
    x_axis_label="Temperature (K)",
    y_axis_label="Pressure (Pa)",
    y_axis_type="log",
    toolbar_location=None,
    tools="",
    x_range=(180, 800),
    y_range=(50, 5e8),
)

# Phase region fills using patches
# Solid region - left side
solid_T = [180, 180] + T_solid_gas.tolist() + T_solid_liquid.tolist()[::-1]
solid_P = [5e8, 100] + P_solid_gas.tolist() + P_solid_liquid_values.tolist()[::-1]
p.patch(solid_T, solid_P, fill_color="#A8D8EA", fill_alpha=0.35, line_color=None)

# Gas region - bottom right
gas_T = T_solid_gas.tolist() + [triple_T] + T_liquid_gas.tolist() + [800, 800, 180]
gas_P = P_solid_gas.tolist() + [triple_P] + P_liquid_gas.tolist() + [critical_P, 100, 100]
p.patch(gas_T, gas_P, fill_color="#FFE0B2", fill_alpha=0.3, line_color=None)

# Liquid region - middle/upper
liquid_T = [triple_T] + T_liquid_gas.tolist() + [critical_T] + T_solid_liquid.tolist()[::-1]
liquid_P = [triple_P] + P_liquid_gas.tolist() + [5e8] + P_solid_liquid_values.tolist()[::-1]
p.patch(liquid_T, liquid_P, fill_color="#C5E1A5", fill_alpha=0.3, line_color=None)

# Supercritical region - upper right beyond critical point
sc_T = [critical_T, 800, 800, critical_T]
sc_P = [critical_P, critical_P, 5e8, 5e8]
p.patch(sc_T, sc_P, fill_color="#E1BEE7", fill_alpha=0.25, line_color=None)

# Phase boundary lines
# Solid-Gas (sublimation)
p.line(T_solid_gas, P_solid_gas, line_width=4, line_color="#306998", line_alpha=0.9)

# Liquid-Gas (vaporization)
p.line(T_liquid_gas, P_liquid_gas, line_width=4, line_color="#306998", line_alpha=0.9)

# Solid-Liquid (melting)
p.line(T_solid_liquid, P_solid_liquid_values, line_width=4, line_color="#306998", line_alpha=0.9)

# Boundary curve labels - placed after patches, with level="overlay" to ensure visibility
sub_label = Label(
    x=218,
    y=120,
    text="Sublimation",
    text_font_size="24pt",
    text_color="#1A5276",
    text_alpha=0.95,
    text_font_style="italic",
    angle=0.75,
    level="overlay",
    background_fill_color="white",
    background_fill_alpha=0.6,
)
p.add_layout(sub_label)

vap_label = Label(
    x=380,
    y=5e4,
    text="Vaporization",
    text_font_size="24pt",
    text_color="#1A5276",
    text_alpha=0.95,
    text_font_style="italic",
    angle=0.50,
    level="overlay",
    background_fill_color="white",
    background_fill_alpha=0.6,
)
p.add_layout(vap_label)

melt_label = Label(
    x=252,
    y=2e7,
    text="Melting",
    text_font_size="24pt",
    text_color="#1A5276",
    text_alpha=0.95,
    text_font_style="italic",
    angle=1.45,
    level="overlay",
    background_fill_color="white",
    background_fill_alpha=0.6,
)
p.add_layout(melt_label)

# Triple point - red marker with glow effect and HoverTool
tp_source = ColumnDataSource(
    data={
        "x": [triple_T],
        "y": [triple_P],
        "name": ["Triple Point"],
        "temp": ["273.16 K"],
        "pres": ["611.73 Pa"],
        "desc": ["All three phases coexist"],
    }
)
# Glow ring behind triple point
p.scatter(x="x", y="y", source=tp_source, size=38, color="#D32F2F", alpha=0.15, marker="circle")
tp_glyph = p.scatter(
    x="x", y="y", source=tp_source, size=26, color="#D32F2F", marker="circle", line_color="white", line_width=3
)

# Critical point - larger diamond with glow for prominence
cp_source = ColumnDataSource(
    data={
        "x": [critical_T],
        "y": [critical_P],
        "name": ["Critical Point"],
        "temp": ["647.1 K"],
        "pres": ["22.064 MPa"],
        "desc": ["Liquid-gas distinction vanishes"],
    }
)
# Glow ring behind critical point
p.scatter(x="x", y="y", source=cp_source, size=44, color="#1A237E", alpha=0.15, marker="diamond")
cp_glyph = p.scatter(
    x="x", y="y", source=cp_source, size=32, color="#1A237E", marker="diamond", line_color="white", line_width=3
)

# HoverTool for special points - Bokeh distinctive feature
hover = HoverTool(
    renderers=[tp_glyph, cp_glyph],
    tooltips=[("Point", "@name"), ("Temperature", "@temp"), ("Pressure", "@pres"), ("Significance", "@desc")],
    point_policy="snap_to_data",
)
p.add_tools(hover)

# Span lines at critical point coordinates - distinctive Bokeh feature for visual reference
cp_h_span = Span(
    location=critical_P, dimension="width", line_color="#1A237E", line_width=1.5, line_alpha=0.15, line_dash="dotted"
)
cp_v_span = Span(
    location=critical_T, dimension="height", line_color="#1A237E", line_width=1.5, line_alpha=0.15, line_dash="dotted"
)
p.add_layout(cp_h_span)
p.add_layout(cp_v_span)

# Dashed line from critical point upward to indicate boundary ends
p.line(
    [critical_T, critical_T], [critical_P, 5e8], line_width=3, line_color="#306998", line_alpha=0.5, line_dash="dashed"
)

# Phase region labels
solid_label = Label(
    x=210, y=5e6, text="SOLID", text_font_size="32pt", text_color="#37474F", text_alpha=0.6, text_font_style="bold"
)
p.add_layout(solid_label)

liquid_label = Label(
    x=400, y=5e7, text="LIQUID", text_font_size="32pt", text_color="#37474F", text_alpha=0.6, text_font_style="bold"
)
p.add_layout(liquid_label)

gas_label = Label(
    x=500, y=500, text="GAS", text_font_size="32pt", text_color="#37474F", text_alpha=0.6, text_font_style="bold"
)
p.add_layout(gas_label)

sc_label = Label(
    x=680,
    y=1.5e8,
    text="SUPERCRITICAL\nFLUID",
    text_font_size="22pt",
    text_color="#6A1B9A",
    text_alpha=0.55,
    text_font_style="bold",
)
p.add_layout(sc_label)

# Triple point annotation - positioned below to avoid congestion with curves
tp_label = Label(
    x=triple_T + 30,
    y=triple_P * 0.15,
    text="Triple Point\n(273.16 K, 611.73 Pa)",
    text_font_size="18pt",
    text_color="#D32F2F",
    text_font_style="bold",
    background_fill_color="white",
    background_fill_alpha=0.7,
)
p.add_layout(tp_label)

# Arrow from triple point annotation to the point
p.add_layout(
    Arrow(
        end=NormalHead(size=12, fill_color="#D32F2F", line_color="#D32F2F"),
        x_start=triple_T + 30,
        y_start=triple_P * 0.6,
        x_end=triple_T + 2,
        y_end=triple_P * 0.95,
        line_color="#D32F2F",
        line_alpha=0.6,
        line_width=2,
    )
)

# Critical point annotation
cp_label = Label(
    x=critical_T - 170,
    y=critical_P * 4,
    text="Critical Point\n(647.1 K, 22.06 MPa)",
    text_font_size="18pt",
    text_color="#1A237E",
    text_font_style="bold",
    background_fill_color="white",
    background_fill_alpha=0.7,
)
p.add_layout(cp_label)

# Arrow from critical point annotation to the point
p.add_layout(
    Arrow(
        end=NormalHead(size=12, fill_color="#1A237E", line_color="#1A237E"),
        x_start=critical_T - 60,
        y_start=critical_P * 3.5,
        x_end=critical_T - 2,
        y_end=critical_P * 1.1,
        line_color="#1A237E",
        line_alpha=0.6,
        line_width=2,
    )
)

# Style - publication-quality typography and refinement
p.title.text_font_size = "30pt"
p.title.text_color = "#2C3E50"
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = "#34495E"
p.yaxis.axis_label_text_color = "#34495E"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = "#555555"
p.yaxis.major_label_text_color = "#555555"

p.xgrid.grid_line_color = "#cccccc"
p.ygrid.grid_line_color = "#cccccc"
p.xgrid.grid_line_alpha = 0.15
p.ygrid.grid_line_alpha = 0.15
p.xgrid.grid_line_dash = [6, 4]
p.ygrid.grid_line_dash = [6, 4]

p.axis.axis_line_color = "#888888"
p.axis.axis_line_width = 1.5
p.axis.major_tick_line_color = "#888888"
p.axis.minor_tick_line_color = "#aaaaaa"
p.background_fill_color = "#FAFBFC"
p.border_fill_color = "white"
p.outline_line_color = None
p.min_border_left = 100
p.min_border_bottom = 80

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="phase-diagram-pt · bokeh · pyplots.ai")
