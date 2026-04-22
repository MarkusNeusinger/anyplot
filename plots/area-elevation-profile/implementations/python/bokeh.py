""" pyplots.ai
area-elevation-profile: Terrain Elevation Profile Along Transect
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-15
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Span
from bokeh.palettes import Cividis256
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

# Compute slope (gradient) for color mapping
slope = np.gradient(elevation, distance)
abs_slope = np.abs(slope)

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

elev_min = float(min(elevation))
elev_max = float(max(elevation))

# Map slope to colorblind-safe Cividis palette for line segments
slope_95 = float(np.percentile(abs_slope, 95))
seg_colors = []
for s in abs_slope:
    idx = int(np.clip(s / slope_95, 0, 1) * 255)
    seg_colors.append(Cividis256[idx])

source = ColumnDataSource(
    data={
        "distance": distance,
        "elevation": elevation,
        "slope": abs_slope,
        "color": seg_colors,
        "elev_fmt": [f"{e:.0f}" for e in elevation],
        "slope_fmt": [f"{s:.1f}" for s in abs_slope],
    }
)

# Build multi-line segments colored by slope (no scatter noise)
seg_xs = [[distance[i], distance[i + 1]] for i in range(n_points - 1)]
seg_ys = [[elevation[i], elevation[i + 1]] for i in range(n_points - 1)]
seg_col = [seg_colors[i] for i in range(n_points - 1)]
seg_source = ColumnDataSource(data={"xs": seg_xs, "ys": seg_ys, "color": seg_col})

# Plot
p = figure(
    width=4800,
    height=2700,
    title="Alpine Trail Profile · area-elevation-profile · bokeh · pyplots.ai",
    x_axis_label="Distance (km)",
    y_axis_label="Elevation (m)",
)

# Filled terrain silhouette with gradient effect using layered varea
y_floor = max(0, elev_min - 100)
p.varea(x="distance", y1=y_floor, y2="elevation", source=source, fill_color="#306998", fill_alpha=0.18)

# Second lighter fill for depth
mid_elev = (np.array(elevation) + y_floor) / 2
mid_source = ColumnDataSource(data={"distance": distance, "mid": mid_elev})
p.varea(x="distance", y1=y_floor, y2="mid", source=mid_source, fill_color="#1d3557", fill_alpha=0.15)

# Slope-colored profile line segments (colorblind-safe Cividis)
p.multi_line(xs="xs", ys="ys", source=seg_source, line_color="color", line_width=5, line_alpha=0.95)

# HoverTool for interactive HTML version
hover = HoverTool(
    tooltips=[("Distance", "@distance{0.1} km"), ("Elevation", "@elev_fmt m"), ("Slope", "@slope_fmt m/km")],
    mode="vline",
)
p.add_tools(hover)

# Landmark vertical markers and labels
for i, (lm_dist, lm_elev, lm_name) in enumerate(
    zip(landmark_distances, landmark_elevations, landmark_names, strict=True)
):
    vline = Span(
        location=lm_dist, dimension="height", line_color="#6d597a", line_width=2, line_alpha=0.35, line_dash="dashed"
    )
    p.add_layout(vline)

    label_text = f"{lm_name}\n{int(lm_elev)} m"
    x_off = 0
    align = "center"
    if i == 0:
        align = "left"
        x_off = 10
    elif i == len(landmarks) - 1:
        align = "right"
        x_off = -40
    label = Label(
        x=lm_dist,
        y=lm_elev,
        text=label_text,
        text_font_size="22pt",
        text_color="#2b2d42",
        text_font_style="bold",
        text_align=align,
        x_offset=x_off,
        y_offset=45,
    )
    p.add_layout(label)

    # Marker dot at landmark position
    p.scatter(x=[lm_dist], y=[lm_elev], size=20, fill_color="#6d597a", line_color="white", line_width=3)

# Style - text sizing for 4800x2700 canvas
p.title.text_font_size = "42pt"
p.title.text_color = "#1a1a2e"
p.xaxis.axis_label_text_font_size = "32pt"
p.yaxis.axis_label_text_font_size = "32pt"
p.xaxis.major_label_text_font_size = "26pt"
p.yaxis.major_label_text_font_size = "26pt"

# Grid - subtle y-axis grid only
p.xgrid.grid_line_alpha = 0
p.ygrid.grid_line_alpha = 0.12
p.ygrid.grid_line_dash = [4, 4]
p.ygrid.grid_line_color = "#888888"

# Clean frame
p.outline_line_color = None
p.toolbar_location = None
p.background_fill_color = "#fafafa"

# Axis styling
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2
p.xaxis.axis_line_color = "#444444"
p.yaxis.axis_line_color = "#444444"

# Y-axis starts near minimum elevation to use vertical space efficiently
p.y_range.start = y_floor
p.y_range.end = elev_max * 1.15

# Generous margins — extra right margin for Kandersteg label
p.min_border_left = 150
p.min_border_bottom = 120
p.min_border_top = 100
p.min_border_right = 250

# Vertical exaggeration note
exag_label = Label(
    x=5,
    y=elev_max * 1.08,
    text="Note: Vertical exaggeration ~10×",
    text_font_size="26pt",
    text_color="#555555",
    text_font_style="italic",
)
p.add_layout(exag_label)

# Slope legend annotation (updated for Cividis)
slope_note = Label(
    x=5,
    y=elev_max * 1.03,
    text="Profile color: dark (flat) → bright (steep)  [Cividis — colorblind-safe]",
    text_font_size="22pt",
    text_color="#666666",
    text_font_style="italic",
)
p.add_layout(slope_note)

# Save
export_png(p, filename="plot.png")

output_file("plot.html")
save(p)
