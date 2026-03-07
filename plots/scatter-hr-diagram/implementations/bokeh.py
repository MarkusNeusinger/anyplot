""" pyplots.ai
scatter-hr-diagram: Hertzsprung-Russell Diagram
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-07
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, Label, Range1d, Title
from bokeh.plotting import figure, save


# Data
np.random.seed(42)

spectral_colors = {
    "O": "#6699ff",
    "B": "#99bbff",
    "A": "#ccddff",
    "F": "#ffffcc",
    "G": "#ffff66",
    "K": "#ffaa33",
    "M": "#ff4400",
}

# Temperature ranges by spectral type (K)
spectral_temp_ranges = {
    "O": (30000, 50000),
    "B": (10000, 30000),
    "A": (7500, 10000),
    "F": (6000, 7500),
    "G": (5200, 6000),
    "K": (3700, 5200),
    "M": (2400, 3700),
}

temperatures = []
luminosities = []
spectral_types = []
colors = []
regions = []

# Main sequence (~200 stars along diagonal)
for spec_type, (t_min, t_max) in spectral_temp_ranges.items():
    n = 30
    temps = np.random.uniform(t_min, t_max, n)
    for t in temps:
        temperatures.append(t)
        log_lum = 4.0 * np.log10(t / 5778) + np.random.normal(0, 0.3)
        luminosities.append(10**log_lum)
        spectral_types.append(spec_type)
        colors.append(spectral_colors[spec_type])
        regions.append("Main Sequence")

# Red giants (~40 stars)
for _ in range(40):
    t = np.random.uniform(3000, 5500)
    lum = 10 ** np.random.uniform(1.5, 3.5)
    temperatures.append(t)
    luminosities.append(lum)
    if t < 3700:
        spec = "M"
    elif t < 5200:
        spec = "K"
    else:
        spec = "G"
    spectral_types.append(spec)
    colors.append(spectral_colors[spec])
    regions.append("Red Giants")

# Supergiants (~20 stars)
for _ in range(20):
    t = np.random.uniform(3500, 30000)
    lum = 10 ** np.random.uniform(3.5, 5.5)
    temperatures.append(t)
    luminosities.append(lum)
    if t > 10000:
        spec = "B"
    elif t > 7500:
        spec = "A"
    elif t > 6000:
        spec = "F"
    elif t > 5200:
        spec = "G"
    elif t > 3700:
        spec = "K"
    else:
        spec = "M"
    spectral_types.append(spec)
    colors.append(spectral_colors[spec])
    regions.append("Supergiants")

# White dwarfs (~30 stars)
for _ in range(30):
    t = np.random.uniform(5000, 40000)
    lum = 10 ** np.random.uniform(-4, -1.5)
    temperatures.append(t)
    luminosities.append(lum)
    if t > 30000:
        spec = "O"
    elif t > 10000:
        spec = "B"
    elif t > 7500:
        spec = "A"
    elif t > 6000:
        spec = "F"
    else:
        spec = "G"
    spectral_types.append(spec)
    colors.append(spectral_colors[spec])
    regions.append("White Dwarfs")

temperatures = np.array(temperatures)
luminosities = np.array(luminosities)

# Plot
source = ColumnDataSource(
    data={
        "temperature": temperatures,
        "luminosity": luminosities,
        "spectral_type": spectral_types,
        "color": colors,
        "region": regions,
    }
)

p = figure(
    width=4800,
    height=2700,
    x_axis_type="log",
    y_axis_type="log",
    x_range=Range1d(55000, 2000),
    y_range=Range1d(1e-4, 2e6),
    x_axis_label="Surface Temperature (K)",
    y_axis_label="Luminosity (L☉)",
    tools="pan,wheel_zoom,box_zoom,reset,hover,save",
    tooltips=[
        ("Temperature", "@temperature{0} K"),
        ("Luminosity", "@luminosity{0.0000} L☉"),
        ("Spectral Type", "@spectral_type"),
        ("Region", "@region"),
    ],
    background_fill_color="#0a0a2a",
    border_fill_color="#0a0a2a",
)

p.scatter(
    x="temperature",
    y="luminosity",
    source=source,
    size=12,
    fill_color="color",
    line_color="white",
    line_width=0.5,
    fill_alpha=0.85,
)

# Sun marker
sun_source = ColumnDataSource(data={"temperature": [5778], "luminosity": [1.0]})
p.scatter(
    x="temperature",
    y="luminosity",
    source=sun_source,
    size=22,
    fill_color="#ffff00",
    line_color="white",
    line_width=2,
    marker="star",
)
p.add_layout(
    Label(
        x=5778,
        y=1.0,
        text="Sun ☀",
        x_offset=15,
        y_offset=-5,
        text_font_size="18pt",
        text_color="#ffff00",
        x_units="data",
        y_units="data",
    )
)

# Region labels
region_labels = [
    ("Main Sequence", 8500, 8, "#aaaacc"),
    ("Red Giants", 3600, 800, "#ffaa33"),
    ("Supergiants", 6000, 150000, "#ccddff"),
    ("White Dwarfs", 15000, 0.001, "#99bbff"),
]
for label_text, lx, ly, lcolor in region_labels:
    p.add_layout(
        Label(
            x=lx,
            y=ly,
            text=label_text,
            text_font_size="22pt",
            text_font_style="italic",
            text_color=lcolor,
            text_alpha=0.8,
            x_units="data",
            y_units="data",
        )
    )

# Spectral class markers along top
spectral_boundaries = [("O", 40000), ("B", 20000), ("A", 8750), ("F", 6750), ("G", 5600), ("K", 4450), ("M", 3050)]
for spec_label, spec_temp in spectral_boundaries:
    p.add_layout(
        Label(
            x=spec_temp,
            y=1.2e6,
            text=spec_label,
            text_font_size="20pt",
            text_font_style="bold",
            text_color=spectral_colors[spec_label],
            text_align="center",
            x_units="data",
            y_units="data",
        )
    )

# Style
p.title = Title(text="scatter-hr-diagram · bokeh · pyplots.ai", text_font_size="28pt", text_color="#ccccee")

p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.axis_label_text_color = "#ccccee"
p.yaxis.axis_label_text_color = "#ccccee"
p.xaxis.major_label_text_color = "#aaaacc"
p.yaxis.major_label_text_color = "#aaaacc"
p.xaxis.axis_line_color = "#555577"
p.yaxis.axis_line_color = "#555577"
p.xaxis.major_tick_line_color = "#555577"
p.yaxis.major_tick_line_color = "#555577"
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xgrid.grid_line_color = "#333355"
p.ygrid.grid_line_color = "#333355"
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.outline_line_color = None

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", title="HR Diagram - Bokeh")
