"""pyplots.ai
area-elevation-profile: Terrain Elevation Profile Along Transect
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-03-15
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Label, Span
from bokeh.plotting import figure


# Data - Alpine hiking trail (120 km) with realistic terrain
np.random.seed(42)
n_points = 480
distance = np.linspace(0, 120, n_points)

# Build realistic elevation profile with multiple peaks and valleys
base_elevation = 800
elevation = np.full(n_points, base_elevation, dtype=float)

# Broad terrain features using sine waves
elevation += 600 * np.sin(distance * np.pi / 40) ** 2
elevation += 400 * np.sin(distance * np.pi / 25 + 1.2) ** 2
elevation += 300 * np.sin(distance * np.pi / 60 + 0.5)

# Add smaller ridges and undulations
elevation += 120 * np.sin(distance * np.pi / 8)
elevation += 80 * np.sin(distance * np.pi / 3.5 + 2.0)

# Smooth noise for natural texture
noise = np.convolve(np.random.randn(n_points + 20) * 30, np.ones(20) / 20, mode="valid")[:n_points]
elevation += noise

# Ensure minimum elevation
elevation = np.maximum(elevation, 450)

# Landmarks along the trail
landmarks = [
    (0.0, "Grindelwald"),
    (18.5, "Kleine Scheidegg"),
    (38.0, "Männlichen"),
    (55.0, "Lauterbrunnen"),
    (72.0, "Mürren"),
    (92.0, "Schilthorn Pass"),
    (120.0, "Kandersteg"),
]

landmark_distances = [lm[0] for lm in landmarks]
landmark_elevations = [float(np.interp(lm[0], distance, elevation)) for lm in landmarks]
landmark_names = [lm[1] for lm in landmarks]

source = ColumnDataSource(data={"distance": distance, "elevation": elevation})

# Plot
p = figure(
    width=4800,
    height=2700,
    title="Alpine Trail Profile · area-elevation-profile · bokeh · pyplots.ai",
    x_axis_label="Distance (km)",
    y_axis_label="Elevation (m)",
)

# Filled terrain silhouette
p.varea(x="distance", y1=0, y2="elevation", source=source, fill_color="#306998", fill_alpha=0.35)

# Profile line on top
p.line(x="distance", y="elevation", source=source, line_color="#306998", line_width=5)

# Landmark vertical markers and labels
for i, (lm_dist, lm_elev, lm_name) in enumerate(
    zip(landmark_distances, landmark_elevations, landmark_names, strict=True)
):
    vline = Span(
        location=lm_dist, dimension="height", line_color="#8B4513", line_width=2, line_alpha=0.4, line_dash="dashed"
    )
    p.add_layout(vline)

    label_text = f"{lm_name}\n{int(lm_elev)} m"
    x_off = 0
    align = "center"
    if i == 0:
        align = "left"
    elif i == len(landmarks) - 1:
        align = "right"
    label = Label(
        x=lm_dist,
        y=lm_elev,
        text=label_text,
        text_font_size="22pt",
        text_color="#333333",
        text_font_style="bold",
        text_align=align,
        x_offset=x_off,
        y_offset=40,
    )
    p.add_layout(label)

    # Small marker dot at landmark position
    p.scatter(x=[lm_dist], y=[lm_elev], size=18, fill_color="#8B4513", line_color="white", line_width=3)

# Style - text sizing for 4800x2700 canvas
p.title.text_font_size = "42pt"
p.xaxis.axis_label_text_font_size = "32pt"
p.yaxis.axis_label_text_font_size = "32pt"
p.xaxis.major_label_text_font_size = "26pt"
p.yaxis.major_label_text_font_size = "26pt"

# Grid - subtle y-axis grid only
p.xgrid.grid_line_alpha = 0
p.ygrid.grid_line_alpha = 0.2

# Clean frame
p.outline_line_color = None
p.toolbar_location = None

# Axis styling
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2

# Y-axis starts at 0 for terrain profile
p.y_range.start = 0
p.y_range.end = max(elevation) * 1.25

# Padding
p.min_border_left = 140
p.min_border_bottom = 120
p.min_border_top = 100
p.min_border_right = 100

# Vertical exaggeration note
exag_label = Label(
    x=5,
    y=max(elevation) * 1.15,
    text="Note: Vertical exaggeration ~10×",
    text_font_size="18pt",
    text_color="#888888",
    text_font_style="italic",
)
p.add_layout(exag_label)

# Save
export_png(p, filename="plot.png")

output_file("plot.html")
save(p)
