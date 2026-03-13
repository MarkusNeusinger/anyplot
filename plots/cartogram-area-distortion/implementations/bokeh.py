""" pyplots.ai
cartogram-area-distortion: Cartogram with Area Distortion by Data Value
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 80/100 | Created: 2026-03-13
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import BasicTicker, ColorBar, ColumnDataSource, Label, LinearColorMapper, Range1d
from bokeh.plotting import figure, save
from bokeh.transform import transform


np.random.seed(42)


def _hex_to_rgb(h):
    h = h.lstrip("#")
    return [int(h[i : i + 2], 16) for i in (0, 2, 4)]


def _interp_palette(colors, n):
    """Interpolate a list of hex colors to n steps."""
    rgbs = np.array([_hex_to_rgb(c) for c in colors], dtype=float)
    x_old = np.linspace(0, 1, len(colors))
    x_new = np.linspace(0, 1, n)
    result = []
    for i in range(n):
        r = int(np.interp(x_new[i], x_old, rgbs[:, 0]))
        g = int(np.interp(x_new[i], x_old, rgbs[:, 1]))
        b = int(np.interp(x_new[i], x_old, rgbs[:, 2]))
        result.append(f"#{r:02x}{g:02x}{b:02x}")
    return result


# Custom warm-to-cool diverging palette (light cream -> warm amber -> deep brown -> dark slate -> ocean teal)
palette = _interp_palette(["#faf3e0", "#f0c75e", "#c97b2a", "#7b3a1e", "#3b2e3b", "#1c4f6e", "#0a97b5"], 256)

# Data - US states: (lon, lat, population in millions)
# Includes all 50 states with AK and HI in inset positions
states = {
    "WA": (-122.0, 47.5, 7.7),
    "OR": (-120.5, 44.0, 4.2),
    "CA": (-119.5, 37.0, 39.0),
    "NV": (-116.8, 39.0, 3.2),
    "ID": (-114.5, 44.0, 2.0),
    "MT": (-109.5, 47.0, 1.1),
    "WY": (-107.5, 43.0, 0.6),
    "UT": (-111.5, 39.5, 3.4),
    "CO": (-105.5, 39.0, 5.8),
    "AZ": (-111.5, 34.0, 7.4),
    "NM": (-106.0, 34.5, 2.1),
    "ND": (-100.5, 47.5, 0.8),
    "SD": (-100.0, 44.5, 0.9),
    "NE": (-99.5, 41.5, 2.0),
    "KS": (-98.5, 38.5, 2.9),
    "OK": (-97.5, 35.5, 4.0),
    "TX": (-99.0, 31.0, 30.5),
    "MN": (-94.5, 46.0, 5.7),
    "IA": (-93.5, 42.0, 3.2),
    "MO": (-92.5, 38.5, 6.2),
    "AR": (-92.5, 34.8, 3.0),
    "LA": (-92.0, 31.0, 4.6),
    "WI": (-89.5, 44.5, 5.9),
    "IL": (-89.0, 40.0, 12.6),
    "MI": (-84.5, 44.5, 10.0),
    "IN": (-86.0, 40.0, 6.8),
    "OH": (-82.5, 40.5, 11.8),
    "KY": (-85.5, 37.8, 4.5),
    "TN": (-86.0, 35.8, 7.1),
    "MS": (-89.5, 32.5, 2.9),
    "AL": (-86.8, 32.8, 5.1),
    "GA": (-83.5, 33.0, 11.0),
    "FL": (-81.5, 28.0, 22.6),
    "SC": (-80.5, 34.0, 5.3),
    "NC": (-79.0, 35.5, 10.7),
    "VA": (-78.5, 37.5, 8.6),
    "WV": (-80.5, 38.5, 1.8),
    "PA": (-77.5, 41.0, 13.0),
    "NY": (-75.5, 43.0, 19.7),
    "NJ": (-74.5, 40.0, 9.3),
    "DE": (-75.5, 39.0, 1.0),
    "MD": (-76.6, 39.0, 6.2),
    "CT": (-72.7, 41.6, 3.6),
    "RI": (-71.5, 41.7, 1.1),
    "MA": (-71.8, 42.3, 7.0),
    "VT": (-72.6, 44.0, 0.6),
    "NH": (-71.5, 43.5, 1.4),
    "ME": (-69.0, 45.0, 1.4),
    # Alaska and Hawaii in inset positions (lower-left)
    "AK": (-124.0, 30.0, 0.7),
    "HI": (-118.0, 28.0, 1.4),
}

names = list(states.keys())
lons = [states[s][0] for s in names]
lats = [states[s][1] for s in names]
populations = [states[s][2] for s in names]

# Scale circle sizes: area proportional to population
min_pop, max_pop = min(populations), max(populations)
min_size, max_size = 25, 95
sizes = [min_size + (max_size - min_size) * np.sqrt((p - min_pop) / (max_pop - min_pop)) for p in populations]

# Reference sizes: uniform small circles showing "equal area" baseline
ref_size = 14

source = ColumnDataSource(
    data={
        "lon": lons,
        "lat": lats,
        "population": populations,
        "size": sizes,
        "ref_size": [ref_size] * len(names),
        "name": names,
        "pop_label": [f"{p:.1f}M" for p in populations],
    }
)

# Color mapper
color_mapper = LinearColorMapper(palette=palette, low=min_pop, high=max_pop)

# Plot with expanded range to avoid clipping
p = figure(
    width=4800,
    height=2700,
    title="US States by Population · cartogram-area-distortion · bokeh · pyplots.ai",
    x_axis_label="Longitude (°W)",
    y_axis_label="Latitude (°N)",
    x_range=Range1d(-128, -66),
    y_range=Range1d(25, 50),
    tools="hover,pan,wheel_zoom,reset",
    tooltips=[("State", "@name"), ("Population", "@pop_label")],
)

# Reference circles: thin outlines showing equal-area baseline for comparison
p.scatter(
    x="lon",
    y="lat",
    size="ref_size",
    source=source,
    fill_color=None,
    line_color="#999999",
    line_width=1,
    line_dash="dotted",
    line_alpha=0.5,
)

# Main cartogram circles: sized by population
p.scatter(
    x="lon",
    y="lat",
    size="size",
    source=source,
    fill_color=transform("population", color_mapper),
    fill_alpha=0.88,
    line_color="#2c2c2c",
    line_width=1.2,
)

# Label major states (pop > 7M), with offsets for crowded northeast
label_offsets = {
    "NY": (1.5, 1.2),
    "PA": (0, -1.8),
    "NJ": (2.0, -0.8),
    "VA": (0, -1.5),
    "MA": (2.5, 0.5),
    "OH": (0, -1.5),
}
for i, name in enumerate(names):
    if populations[i] > 7.0:
        dx, dy = label_offsets.get(name, (0, 0))
        label = Label(
            x=lons[i] + dx,
            y=lats[i] + dy,
            text=name,
            text_font_size="15pt",
            text_align="center",
            text_baseline="middle",
            text_color="#1a1a1a",
            text_font_style="bold",
        )
        p.add_layout(label)

# Annotation: reference circle explanation
ref_note = Label(
    x=-127, y=49, text="○ = equal area reference", text_font_size="13pt", text_color="#777777", text_font_style="italic"
)
p.add_layout(ref_note)

# Inset labels for AK and HI
for abbr in ("AK", "HI"):
    ix = states[abbr][0]
    iy = states[abbr][1]
    inset_label = Label(x=ix, y=iy - 1.5, text=abbr, text_font_size="12pt", text_align="center", text_color="#555555")
    p.add_layout(inset_label)

# Color bar with better spacing
color_bar = ColorBar(
    color_mapper=color_mapper,
    ticker=BasicTicker(desired_num_ticks=6),
    label_standoff=16,
    major_label_text_font_size="16pt",
    title="Population (millions)",
    title_text_font_size="18pt",
    width=35,
    padding=50,
    margin=20,
)
p.add_layout(color_bar, "right")

# Typography and style
p.title.text_font_size = "28pt"
p.title.text_color = "#222222"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.axis_label_text_color = "#444444"
p.yaxis.axis_label_text_color = "#444444"

# Refined grid and background
p.xgrid.grid_line_alpha = 0.12
p.ygrid.grid_line_alpha = 0.12
p.xgrid.grid_line_width = 1
p.ygrid.grid_line_width = 1
p.xgrid.grid_line_color = "#bbbbbb"
p.ygrid.grid_line_color = "#bbbbbb"

p.background_fill_color = "#f5f3ef"
p.border_fill_color = "#ffffff"
p.outline_line_color = None

# Remove minor ticks for cleaner look
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.major_tick_line_color = "#aaaaaa"
p.yaxis.major_tick_line_color = "#aaaaaa"

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", title="Cartogram Area Distortion - Bokeh")
