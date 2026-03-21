""" pyplots.ai
titration-curve: Acid-Base Titration Curve
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-21
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import BoxAnnotation, ColumnDataSource, HoverTool, Label, LinearAxis, Range1d, Span
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Strong acid/strong base titration: 25 mL of 0.1 M HCl with 0.1 M NaOH
acid_volume_ml = 25.0
acid_concentration = 0.1
base_concentration = 0.1
equivalence_volume = acid_volume_ml * acid_concentration / base_concentration  # 25 mL

volume_ml = np.unique(
    np.concatenate([np.linspace(0.1, 24.0, 80), np.linspace(24.0, 26.0, 40), np.linspace(26.0, 50.0, 80)])
)

moles_acid = acid_concentration * acid_volume_ml / 1000
moles_base = base_concentration * volume_ml / 1000
total_volume_L = (acid_volume_ml + volume_ml) / 1000

ph = np.empty_like(volume_ml)
for i in range(len(volume_ml)):
    if moles_base[i] < moles_acid - 1e-10:
        h_plus = (moles_acid - moles_base[i]) / total_volume_L[i]
        ph[i] = -np.log10(h_plus)
    elif moles_base[i] > moles_acid + 1e-10:
        oh_minus = (moles_base[i] - moles_acid) / total_volume_L[i]
        ph[i] = 14.0 + np.log10(oh_minus)
    else:
        ph[i] = 7.0

# Derivative dpH/dV using central differences
dph_dv = np.gradient(ph, volume_ml)
dph_dv = np.where(np.isfinite(dph_dv), dph_dv, 0.0)
eq_ph = 7.0

# Colors
CURVE_COLOR = "#306998"
DERIV_COLOR = "#D55E00"
EQ_COLOR = "#009E73"
ACID_BUFFER_COLOR = "#E69F00"
BASE_BUFFER_COLOR = "#56B4E9"
BG_COLOR = "#F7F7F7"
AXIS_COLOR = "#444444"

source = ColumnDataSource(data={"volume": volume_ml, "ph": ph, "dph_dv": dph_dv})

# Plot
p = figure(
    width=4800,
    height=2700,
    x_axis_label="Volume of NaOH added (mL)",
    y_axis_label="pH",
    y_range=Range1d(0, 14),
    title="titration-curve · bokeh · pyplots.ai",
    toolbar_location=None,
)

# Buffer region shading - vertical spans for where pH changes slowly
# Acidic buffer zone: 0-15 mL (pH slowly rises from ~1 to ~2)
acid_buffer = BoxAnnotation(
    left=0,
    right=15,
    fill_color=ACID_BUFFER_COLOR,
    fill_alpha=0.05,
    line_color=ACID_BUFFER_COLOR,
    line_alpha=0.15,
    line_width=1,
    line_dash="dashed",
)
p.add_layout(acid_buffer)

# Basic buffer zone: 35-50 mL (pH plateaus around ~12-13)
basic_buffer = BoxAnnotation(
    left=35,
    right=50,
    fill_color=BASE_BUFFER_COLOR,
    fill_alpha=0.05,
    line_color=BASE_BUFFER_COLOR,
    line_alpha=0.15,
    line_width=1,
    line_dash="dashed",
)
p.add_layout(basic_buffer)

# Buffer region labels
p.add_layout(
    Label(
        x=7.5,
        y=4.5,
        text="Acidic Buffer Region",
        text_font_size="16pt",
        text_color=ACID_BUFFER_COLOR,
        text_alpha=0.65,
        text_align="center",
        text_font_style="italic",
    )
)
p.add_layout(
    Label(
        x=42.5,
        y=9.5,
        text="Basic Buffer Region",
        text_font_size="16pt",
        text_color=BASE_BUFFER_COLOR,
        text_alpha=0.65,
        text_align="center",
        text_font_style="italic",
    )
)

# Secondary y-axis for derivative
deriv_max = float(np.max(dph_dv)) * 1.15
p.extra_y_ranges = {"deriv": Range1d(start=-deriv_max * 0.05, end=deriv_max)}
deriv_axis = LinearAxis(
    y_range_name="deriv",
    axis_label="dpH/dV (mL⁻¹)",
    axis_label_text_font_size="22pt",
    major_label_text_font_size="18pt",
    axis_line_color=DERIV_COLOR,
    axis_label_text_color=DERIV_COLOR,
    major_label_text_color=DERIV_COLOR,
    major_tick_line_color=None,
    minor_tick_line_color=None,
)
p.add_layout(deriv_axis, "right")

# Derivative curve
deriv_source = ColumnDataSource(data={"volume": volume_ml, "dph_dv": dph_dv})
p.line(
    "volume",
    "dph_dv",
    source=deriv_source,
    line_width=4,
    color=DERIV_COLOR,
    line_alpha=0.7,
    line_dash="dotdash",
    y_range_name="deriv",
    legend_label="dpH/dV",
)

# Main titration curve
p.line("volume", "ph", source=source, line_width=5, color=CURVE_COLOR, legend_label="pH")

# Equivalence point vertical dashed line
p.add_layout(
    Span(
        location=equivalence_volume,
        dimension="height",
        line_color=EQ_COLOR,
        line_width=3,
        line_dash="dashed",
        line_alpha=0.8,
    )
)

# Equivalence point marker
p.scatter([equivalence_volume], [eq_ph], size=26, color=EQ_COLOR, marker="diamond", line_color="white", line_width=2)

# Equivalence point annotation
p.add_layout(
    Label(
        x=equivalence_volume,
        y=eq_ph,
        text=f"Equivalence Point\n{equivalence_volume:.0f} mL, pH {eq_ph:.1f}",
        text_font_size="20pt",
        text_font_style="bold",
        text_color=EQ_COLOR,
        x_offset=25,
        y_offset=-10,
    )
)

# pH 7 reference line
p.add_layout(
    Span(location=7, dimension="width", line_color="#999999", line_width=1.5, line_dash="dotted", line_alpha=0.35)
)

# Hover tool
p.add_tools(
    HoverTool(tooltips=[("Volume", "@volume{0.1} mL"), ("pH", "@ph{0.2}")], mode="vline", line_policy="nearest")
)

# Style
p.title.text_font_size = "30pt"
p.title.text_font_style = "normal"
p.title.text_color = "#2B2B2B"

p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

p.xaxis.axis_line_color = AXIS_COLOR
p.yaxis.axis_line_color = AXIS_COLOR
p.xaxis.axis_line_width = 1.5
p.yaxis.axis_line_width = 1.5

p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.outline_line_color = None
p.background_fill_color = BG_COLOR
p.border_fill_color = "#FFFFFF"

p.ygrid.grid_line_alpha = 0.15
p.ygrid.grid_line_width = 1
p.ygrid.grid_line_dash = [4, 4]
p.xgrid.grid_line_alpha = 0.12
p.xgrid.grid_line_width = 1
p.xgrid.grid_line_dash = [4, 4]

p.min_border_left = 120
p.min_border_right = 180
p.min_border_bottom = 80
p.min_border_top = 60

# Legend
p.legend.location = "top_left"
p.legend.label_text_font_size = "20pt"
p.legend.glyph_height = 30
p.legend.glyph_width = 45
p.legend.spacing = 12
p.legend.padding = 18
p.legend.background_fill_alpha = 0.85
p.legend.background_fill_color = "#FFFFFF"
p.legend.border_line_color = "#DDDDDD"
p.legend.border_line_width = 1

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="titration-curve · bokeh · pyplots.ai")
