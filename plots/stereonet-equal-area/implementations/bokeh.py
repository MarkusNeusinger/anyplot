""" pyplots.ai
stereonet-equal-area: Structural Geology Stereonet (Equal-Area Projection)
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-15
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColorBar, ColumnDataSource, HoverTool, Label, Legend, LegendItem, LinearColorMapper
from bokeh.plotting import figure
from scipy.ndimage import gaussian_filter
from scipy.stats import gaussian_kde


# Data - Synthetic structural geology measurements (strike, dip, feature_type)
np.random.seed(42)

# Bedding planes: consistent NE strike with moderate dip
bedding_strike = np.random.normal(45, 12, 40) % 360
bedding_dip = np.random.normal(35, 8, 40).clip(5, 85)

# Joint set 1: roughly E-W strike, steep dip
joints_strike = np.random.normal(270, 15, 35) % 360
joints_dip = np.random.normal(75, 10, 35).clip(5, 89)

# Fault set: NW strike, moderate-steep dip
faults_strike = np.random.normal(315, 10, 25) % 360
faults_dip = np.random.normal(60, 12, 25).clip(5, 89)

all_strikes = np.concatenate([bedding_strike, joints_strike, faults_strike])
all_dips = np.concatenate([bedding_dip, joints_dip, faults_dip])
all_types = ["Bedding"] * 40 + ["Joints"] * 35 + ["Faults"] * 25
colors_map = {"Bedding": "#306998", "Joints": "#E8833A", "Faults": "#8B5CF6"}

# Equal-area projection: convert pole (plunge, trend) to x, y
R_net = 1.0

pole_trends = (all_strikes + 90 + 180) % 360
pole_plunges = 90.0 - all_dips
pole_trends_rad = np.radians(pole_trends)
pole_plunges_rad = np.radians(pole_plunges)

pole_r = R_net * np.sqrt(2) * np.sin((np.pi / 2 - pole_plunges_rad) / 2)
pole_x = pole_r * np.sin(pole_trends_rad)
pole_y = pole_r * np.cos(pole_trends_rad)

# Great circles for each plane
gc_xs = []
gc_ys = []
gc_types = []

for i in range(len(all_strikes)):
    strike_rad = np.radians(all_strikes[i])
    dip_rad = np.radians(all_dips[i])
    dd_rad = strike_rad + np.pi / 2

    sx = np.sin(strike_rad)
    sy = np.cos(strike_rad)

    dx = np.sin(dd_rad) * np.cos(dip_rad)
    dy = np.cos(dd_rad) * np.cos(dip_rad)
    dz = -np.sin(dip_rad)

    alpha = np.linspace(0, np.pi, 90)
    vx = np.cos(alpha) * sx + np.sin(alpha) * dx
    vy = np.cos(alpha) * sy + np.sin(alpha) * dy
    vz = np.sin(alpha) * dz

    horiz = np.sqrt(vx**2 + vy**2)
    plunge = np.arctan2(-vz, horiz)
    trend = np.arctan2(vx, vy)

    r = R_net * np.sqrt(2) * np.sin((np.pi / 2 - plunge) / 2)
    gx = r * np.sin(trend)
    gy = r * np.cos(trend)

    # Clip great circle points near the primitive circle to reduce edge clutter
    gc_dist = np.sqrt(gx**2 + gy**2)
    keep = gc_dist <= 0.94 * R_net
    gc_xs.append(gx[keep].tolist())
    gc_ys.append(gy[keep].tolist())
    gc_types.append(all_types[i])

# Density grid for pole data using KDE
grid_n = 300
gx_lin = np.linspace(-R_net, R_net, grid_n)
gy_lin = np.linspace(-R_net, R_net, grid_n)
gx_grid, gy_grid = np.meshgrid(gx_lin, gy_lin)

dist_grid = np.sqrt(gx_grid**2 + gy_grid**2)
mask = dist_grid <= R_net

pole_xy = np.vstack([pole_x, pole_y])
kde = gaussian_kde(pole_xy, bw_method=0.2)
density = kde(np.vstack([gx_grid.ravel(), gy_grid.ravel()])).reshape(grid_n, grid_n)
density = gaussian_filter(density, sigma=3)

# Create RGBA density overlay (masked to circle)
density_masked = density.copy()
density_masked[~mask] = np.nan
d_min = np.nanmin(density_masked[mask])
d_max = np.nanmax(density_masked[mask])
d_norm = (density_masked - d_min) / (d_max - d_min)

# Build uint32 RGBA array for Bokeh image_rgba (vectorized)
img = np.zeros((grid_n, grid_n), dtype=np.uint32)
view = img.view(dtype=np.uint8).reshape((grid_n, grid_n, 4))
visible = mask & (d_norm > 0.08)
v = np.where(visible, d_norm, 0.0)
view[visible, 0] = (220 - v[visible] * 100).astype(np.uint8)  # R: warm orange-red
view[visible, 1] = (160 - v[visible] * 130).astype(np.uint8)  # G: decreasing for warmth
view[visible, 2] = (80 - v[visible] * 60).astype(np.uint8)  # B: low for warm tones
view[visible, 3] = (v[visible] * 220).astype(np.uint8)  # A: stronger alpha

# Plot - Square format for circular stereonet
p = figure(
    width=3600,
    height=3600,
    title="stereonet-equal-area · bokeh · pyplots.ai",
    x_range=(-1.35, 1.35),
    y_range=(-1.38, 1.40),
    tools="pan,wheel_zoom,reset,save",
    toolbar_location=None,
    match_aspect=True,
)

# Density heatmap as Bokeh image_rgba (distinctive Bokeh feature)
p.image_rgba(image=[img], x=-R_net, y=-R_net, dw=2 * R_net, dh=2 * R_net, level="image")

# Density colorbar to quantify KDE levels
density_colors = ["#FFFFFF", "#FDDCB5", "#F5A66A", "#E07030", "#B8391A", "#781414"]
color_mapper = LinearColorMapper(palette=density_colors, low=0.0, high=float(d_max))
color_bar = ColorBar(
    color_mapper=color_mapper,
    location=(0, 0),
    title="Density",
    title_text_font_size="22pt",
    title_text_font_style="italic",
    title_text_color="#333333",
    major_label_text_font_size="20pt",
    major_label_text_color="#444444",
    label_standoff=18,
    width=44,
    height=900,
    padding=20,
    background_fill_alpha=0.0,
    border_line_color=None,
    major_tick_line_color="#666666",
    major_tick_line_width=2,
)
p.add_layout(color_bar, "right")

# Equal-area net grid lines (small circles at 10° dip intervals)
for dip_angle in range(10, 90, 10):
    dip_rad = np.radians(dip_angle)
    grid_r = R_net * np.sqrt(2) * np.sin(dip_rad / 2)
    theta = np.linspace(0, 2 * np.pi, 180)
    gx = grid_r * np.cos(theta)
    gy = grid_r * np.sin(theta)
    p.line(gx, gy, line_color="#CCCCCC", line_width=1, line_alpha=0.55)

# Great circle grid lines at every 30° azimuth
for az_deg in range(0, 180, 30):
    az_rad = np.radians(az_deg)
    alpha = np.linspace(0, np.pi, 90)
    vx = np.cos(alpha) * np.sin(az_rad)
    vy = np.cos(alpha) * np.cos(az_rad)
    vz = -np.sin(alpha)
    horiz = np.sqrt(vx**2 + vy**2)
    plunge = np.arctan2(-vz, horiz)
    trend = np.arctan2(vx, vy)
    r = R_net * np.sqrt(2) * np.sin((np.pi / 2 - plunge) / 2)
    grid_gx = r * np.sin(trend)
    grid_gy = r * np.cos(trend)
    p.line(grid_gx, grid_gy, line_color="#CCCCCC", line_width=1, line_alpha=0.55)

# Primitive circle (outer boundary)
theta_circle = np.linspace(0, 2 * np.pi, 360)
circle_x = R_net * np.cos(theta_circle)
circle_y = R_net * np.sin(theta_circle)
p.line(circle_x, circle_y, line_color="#222222", line_width=4)

# Tick marks every 10 degrees around perimeter
for deg in range(0, 360, 10):
    rad = np.radians(deg)
    tick_len = 0.06 if deg % 30 == 0 else 0.04
    x_inner = (1.0 - tick_len) * R_net * np.sin(rad)
    y_inner = (1.0 - tick_len) * R_net * np.cos(rad)
    x_outer = 1.04 * R_net * np.sin(rad)
    y_outer = 1.04 * R_net * np.cos(rad)
    lw = 4 if deg % 90 == 0 else (3 if deg % 30 == 0 else 2)
    p.line([x_inner, x_outer], [y_inner, y_outer], line_color="#222222", line_width=lw)

# Degree labels every 30 degrees
for deg in range(0, 360, 30):
    if deg % 90 == 0:
        continue
    rad = np.radians(deg)
    lx = 1.13 * R_net * np.sin(rad)
    ly = 1.13 * R_net * np.cos(rad)
    p.add_layout(
        Label(
            x=lx,
            y=ly,
            text=f"{deg}°",
            text_font_size="22pt",
            text_align="center",
            text_baseline="middle",
            text_color="#555555",
        )
    )

# Cardinal direction labels
for deg, label in [(0, "N"), (90, "E"), (180, "S"), (270, "W")]:
    rad = np.radians(deg)
    lx = 1.18 * R_net * np.sin(rad)
    ly = 1.18 * R_net * np.cos(rad)
    fs = "38pt" if label == "N" else "30pt"
    p.add_layout(
        Label(
            x=lx,
            y=ly,
            text=label,
            text_font_size=fs,
            text_font_style="bold",
            text_align="center",
            text_baseline="middle",
            text_color="#222222",
        )
    )

# Great circles by feature type
renderers_gc = {}
for ftype in ["Bedding", "Joints", "Faults"]:
    idxs = [j for j, t in enumerate(gc_types) if t == ftype]
    fxs = [gc_xs[j] for j in idxs]
    fys = [gc_ys[j] for j in idxs]
    r = p.multi_line(fxs, fys, line_color=colors_map[ftype], line_width=1.5, line_alpha=0.18)
    renderers_gc[ftype] = r

# Poles by feature type with HoverTool
renderers_pole = {}
for ftype in ["Bedding", "Joints", "Faults"]:
    idxs = [j for j, t in enumerate(all_types) if t == ftype]
    px = pole_x[idxs]
    py = pole_y[idxs]
    strikes = all_strikes[idxs]
    dips = all_dips[idxs]
    source = ColumnDataSource(
        data={"x": px, "y": py, "strike": np.round(strikes, 1), "dip": np.round(dips, 1), "type": [ftype] * len(idxs)}
    )
    r = p.scatter(
        "x", "y", source=source, size=22, color=colors_map[ftype], line_color="white", line_width=2, alpha=0.9
    )
    renderers_pole[ftype] = r

# HoverTool for pole data (Bokeh distinctive feature)
hover = HoverTool(
    renderers=list(renderers_pole.values()),
    tooltips=[("Type", "@type"), ("Strike", "@strike°"), ("Dip", "@dip°")],
    point_policy="snap_to_data",
)
p.add_tools(hover)

# Interactive legend (Bokeh distinctive feature - click to hide/show)
legend_items = []
for ftype in ["Bedding", "Joints", "Faults"]:
    legend_items.append(LegendItem(label=ftype, renderers=[renderers_gc[ftype], renderers_pole[ftype]]))

legend = Legend(items=legend_items, location="top_right")
legend.label_text_font_size = "26pt"
legend.glyph_height = 40
legend.glyph_width = 40
legend.spacing = 16
legend.background_fill_alpha = 0.92
legend.background_fill_color = "#FAFAFA"
legend.border_line_color = "#AAAAAA"
legend.border_line_width = 2
legend.padding = 24
legend.margin = 20
legend.click_policy = "hide"
p.add_layout(legend)

# Style
p.title.text_font_size = "38pt"
p.title.align = "center"
p.title.text_color = "#222222"
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None
p.background_fill_color = "white"
p.border_fill_color = "white"
p.min_border_left = 40
p.min_border_right = 180
p.min_border_top = 10
p.min_border_bottom = 40

# Subtitle annotation
p.add_layout(
    Label(
        x=0,
        y=-1.30,
        text="Lower-hemisphere equal-area (Schmidt) projection · Click legend to toggle",
        text_font_size="22pt",
        text_align="center",
        text_color="#777777",
        text_font_style="italic",
    )
)

# Save
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
