"""pyplots.ai
spectrum-nmr: NMR Spectrum (Nuclear Magnetic Resonance)
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-09
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Span
from bokeh.plotting import figure


# Data - synthetic 1H NMR spectrum of ethanol (CH3-CH2-OH)
np.random.seed(42)
ppm = np.linspace(-0.5, 12.0, 6000)
w = 0.008  # Lorentzian peak width
j = 0.07  # J-coupling constant

# Build spectrum by summing Lorentzian peaks: intensity * w^2 / ((x - center)^2 + w^2)
# TMS reference peak at 0 ppm (singlet, narrower)
w_tms = 0.006
spectrum = 0.3 * w_tms**2 / ((ppm - 0.0) ** 2 + w_tms**2)

# CH3 triplet near 1.18 ppm (intensity ratio 1:2:1)
spectrum += 0.5 * w**2 / ((ppm - (1.18 - j)) ** 2 + w**2)
spectrum += 1.0 * w**2 / ((ppm - 1.18) ** 2 + w**2)
spectrum += 0.5 * w**2 / ((ppm - (1.18 + j)) ** 2 + w**2)

# OH singlet near 2.61 ppm
spectrum += 0.4 * w**2 / ((ppm - 2.61) ** 2 + w**2)

# CH2 quartet near 3.69 ppm (intensity ratio 1:3:3:1)
spectrum += 0.3 * w**2 / ((ppm - (3.69 - 1.5 * j)) ** 2 + w**2)
spectrum += 0.9 * w**2 / ((ppm - (3.69 - 0.5 * j)) ** 2 + w**2)
spectrum += 0.9 * w**2 / ((ppm - (3.69 + 0.5 * j)) ** 2 + w**2)
spectrum += 0.3 * w**2 / ((ppm - (3.69 + 1.5 * j)) ** 2 + w**2)

# Add subtle baseline noise
spectrum += np.random.normal(0, 0.003, len(ppm))
spectrum = np.maximum(spectrum, 0)

source = ColumnDataSource(data={"ppm": ppm, "intensity": spectrum})

# Create figure (4800 x 2700 px) with reversed x-axis (NMR convention)
p = figure(
    width=4800,
    height=2700,
    title="¹H NMR Spectrum of Ethanol · spectrum-nmr · bokeh · pyplots.ai",
    x_axis_label="Chemical Shift (ppm)",
    y_axis_label="Intensity (a.u.)",
    x_range=(12.0, -0.5),
    background_fill_color="#f8f9fb",
)

# Filled area under the spectrum curve for visual depth
p.varea(x="ppm", y1=0, y2="intensity", source=source, fill_color="#306998", fill_alpha=0.1)

# Spectrum line
p.line(x="ppm", y="intensity", source=source, line_color="#306998", line_width=3)

# TMS reference line using Span (distinctive Bokeh feature)
tms_line = Span(
    location=0.0, dimension="height", line_color="#999999", line_width=1.5, line_dash="dashed", line_alpha=0.5
)
p.add_layout(tms_line)

# Peak labels with chemical shift values
peak_labels = [
    (0.0, 0.3, "TMS\n0.00 ppm"),
    (1.18, 1.0, "CH₃ (triplet)\n1.18 ppm"),
    (2.61, 0.4, "OH (singlet)\n2.61 ppm"),
    (3.69, 0.9, "CH₂ (quartet)\n3.69 ppm"),
]

for ppm_val, intensity_val, text in peak_labels:
    label = Label(
        x=ppm_val,
        y=intensity_val + 0.06,
        text=text,
        text_font_size="26pt",
        text_color="#1a3d5c",
        text_font_style="bold",
        text_align="center",
    )
    p.add_layout(label)

# HoverTool for interactive exploration
hover = HoverTool(tooltips=[("Chemical Shift", "@ppm{0.00} ppm"), ("Intensity", "@intensity{0.000}")], mode="vline")
p.add_tools(hover)

# Text sizing scaled for 4800x2700 canvas
p.title.text_font_size = "42pt"
p.title.text_color = "#1a3d5c"
p.xaxis.axis_label_text_font_size = "32pt"
p.yaxis.axis_label_text_font_size = "32pt"
p.xaxis.major_label_text_font_size = "26pt"
p.yaxis.major_label_text_font_size = "26pt"
p.xaxis.axis_label_text_color = "#333333"
p.yaxis.axis_label_text_color = "#333333"

# Grid styling - y-axis only, subtle
p.xgrid.grid_line_alpha = 0
p.ygrid.grid_line_alpha = 0.12
p.ygrid.grid_line_color = "#aaaaaa"

# Clean frame - remove outline and border fill
p.outline_line_color = None
p.border_fill_color = "#ffffff"

# Axis line styling
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.axis_line_color = "#555555"
p.yaxis.axis_line_color = "#555555"
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2
p.xaxis.major_tick_line_color = "#555555"
p.yaxis.major_tick_line_color = "#555555"
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Remove toolbar for clean export
p.toolbar_location = None

# Y-axis starts at 0 with headroom for labels
p.y_range.start = -0.02
p.y_range.end = 1.3

# Add padding to margins
p.min_border_left = 140
p.min_border_bottom = 120
p.min_border_top = 100

# Save as PNG
export_png(p, filename="plot.png")

# Save as HTML for interactive viewing
output_file("plot.html")
save(p)
