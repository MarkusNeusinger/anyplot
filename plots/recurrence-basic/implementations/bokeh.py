"""pyplots.ai
recurrence-basic: Recurrence Plot for Nonlinear Time Series
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-14
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import BasicTicker, ColorBar, ColumnDataSource, HoverTool, Label, LinearColorMapper
from bokeh.palettes import Cividis256
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Lorenz attractor x-component
np.random.seed(42)
dt = 0.01
num_steps = 5000
lx, ly, lz = 1.0, 1.0, 1.0
sigma, rho, beta = 10.0, 28.0, 8.0 / 3.0

trajectory = np.empty(num_steps)
for step in range(num_steps):
    dx = sigma * (ly - lx) * dt
    dy = (lx * (rho - lz) - ly) * dt
    dz = (lx * ly - beta * lz) * dt
    lx, ly, lz = lx + dx, ly + dy, lz + dz
    trajectory[step] = lx

# Downsample to 500 points for clear visualization
signal = trajectory[::10]
n_points = len(signal)

# Time-delay embedding (Takens' theorem)
tau = 5
dim = 3
n_embedded = n_points - (dim - 1) * tau
embedded = np.empty((n_embedded, dim))
for d in range(dim):
    embedded[:, d] = signal[d * tau : d * tau + n_embedded]

# Compute pairwise Euclidean distance matrix
diff = embedded[:, np.newaxis, :] - embedded[np.newaxis, :, :]
dist_matrix = np.sqrt(np.sum(diff**2, axis=2))

# Binary recurrence threshold for storytelling overlay
threshold = np.percentile(dist_matrix, 10)

# Normalize distances for color mapping (0 = identical, 1 = max distance)
max_dist = dist_matrix.max()
dist_normalized = dist_matrix / max_dist

# Flip vertically so origin is top-left (row 0 at top)
dist_flipped = dist_normalized[::-1, :]

# Perceptually uniform colormap - reversed so dark = recurrent (close), light = distant
palette = list(reversed(Cividis256))

color_mapper = LinearColorMapper(palette=palette, low=0.0, high=1.0)

# Create square figure
n = n_embedded
p = figure(
    width=3600,
    height=3600,
    title="Lorenz Attractor · recurrence-basic · bokeh · pyplots.ai",
    x_axis_label="Time Index (Lorenz x-component, dt=0.01)",
    y_axis_label="Time Index (Lorenz x-component, dt=0.01)",
    toolbar_location=None,
    tools="",
    x_range=(0, n),
    y_range=(0, n),
)

# Plot distance-based recurrence matrix as image
p.image(image=[dist_flipped], x=0, y=0, dw=n, dh=n, color_mapper=color_mapper)

# Add ColorBar to show distance scale
color_bar = ColorBar(
    color_mapper=color_mapper,
    ticker=BasicTicker(desired_num_ticks=6),
    label_standoff=16,
    border_line_color=None,
    location=(0, 0),
    title="Normalized Distance",
    title_text_font_size="18pt",
    major_label_text_font_size="16pt",
    width=40,
    padding=30,
)
p.add_layout(color_bar, "right")

# Add threshold contour line annotation for storytelling
# Mark the recurrence threshold on the colorbar
threshold_norm = threshold / max_dist

# Storytelling: annotate key recurrence features visible against the colormap
label_block = Label(
    x=200,
    y=260,
    text="Laminar regime",
    text_font_size="22pt",
    text_color="white",
    text_font_style="bold",
    text_alpha=0.85,
    background_fill_color="#306998",
    background_fill_alpha=0.6,
)
p.add_layout(label_block)

label_diag = Label(
    x=120,
    y=160,
    text="Deterministic diagonals",
    text_font_size="22pt",
    text_color="white",
    text_font_style="bold",
    text_alpha=0.85,
    background_fill_color="#306998",
    background_fill_alpha=0.6,
    angle=0.78,
)
p.add_layout(label_diag)

# Threshold annotation in top-left corner
label_threshold = Label(
    x=10,
    y=n - 20,
    text=f"Recurrence threshold \u03b5 = {threshold:.1f} (10th percentile)",
    text_font_size="18pt",
    text_color="white",
    text_alpha=0.9,
    background_fill_color="#2c3e50",
    background_fill_alpha=0.7,
)
p.add_layout(label_threshold)

# HoverTool on a transparent scatter overlay for interactivity
# Sample grid points for hover info (every 20th point for performance)
hover_step = 20
hover_xs, hover_ys, hover_dists, hover_recs = [], [], [], []
for i in range(0, n, hover_step):
    for j in range(0, n, hover_step):
        hover_xs.append(i + hover_step // 2)
        hover_ys.append(j + hover_step // 2)
        d = dist_matrix[i, j]
        hover_dists.append(round(float(d), 2))
        hover_recs.append("Yes" if d <= threshold else "No")

hover_source = ColumnDataSource(data={"x": hover_xs, "y": hover_ys, "distance": hover_dists, "recurrent": hover_recs})

invisible_scatter = p.scatter(x="x", y="y", source=hover_source, size=hover_step, fill_alpha=0, line_alpha=0)

hover = HoverTool(
    renderers=[invisible_scatter],
    tooltips=[
        ("Time i", "@x"),
        ("Time j", "@y"),
        ("Distance", "@distance"),
        ("Recurrent (d < {:.1f})".format(threshold), "@recurrent"),
    ],
)
p.add_tools(hover)

# Styling
p.title.text_font_size = "28pt"
p.title.text_color = "#2c3e50"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
p.axis.minor_tick_line_color = None
p.axis.axis_line_color = "#666666"
p.axis.major_tick_line_color = "#666666"
p.outline_line_color = None
p.background_fill_color = "#fafafa"
p.border_fill_color = "white"
p.min_border_right = 120

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="recurrence-basic · bokeh · pyplots.ai")
