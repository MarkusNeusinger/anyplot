"""pyplots.ai
recurrence-basic: Recurrence Plot for Nonlinear Time Series
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-03-14
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import LinearColorMapper
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

# Binary recurrence matrix: 1 where distance < threshold (recurrent), 0 otherwise
threshold = np.percentile(dist_matrix, 10)
recurrence = (dist_matrix <= threshold).astype(np.float64)

# Flip vertically so origin is top-left (row 0 at top)
recurrence_flipped = recurrence[::-1, :]

# Color palette - dark blue for recurrent points, light background
palette = ["#f0f4f8", "#306998"]

color_mapper = LinearColorMapper(palette=palette, low=0, high=1)

# Create square figure
n = n_embedded
p = figure(
    width=3600,
    height=3600,
    title="Lorenz Attractor · recurrence-basic · bokeh · pyplots.ai",
    x_axis_label="Time Index",
    y_axis_label="Time Index",
    toolbar_location=None,
    tools="",
    x_range=(0, n),
    y_range=(0, n),
)

# Plot binary recurrence matrix as image
p.image(image=[recurrence_flipped], x=0, y=0, dw=n, dh=n, color_mapper=color_mapper)

# Styling
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
p.axis.minor_tick_line_color = None
p.outline_line_color = None
p.background_fill_color = "#fafafa"
p.border_fill_color = "white"
p.min_border_right = 60

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="recurrence-basic · bokeh · pyplots.ai")
