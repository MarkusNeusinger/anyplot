"""pyplots.ai
heatmap-rainflow: Rainflow Counting Matrix for Fatigue Analysis
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-02
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, HoverTool, Label, LogColorMapper, LogTicker
from bokeh.palettes import Inferno256
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data — Simulated rainflow counting matrix for a vehicle suspension component
np.random.seed(42)

n_bins = 20
amplitude_edges = np.linspace(10, 210, n_bins + 1)
mean_edges = np.linspace(-100, 300, n_bins + 1)
amplitude_centers = (amplitude_edges[:-1] + amplitude_edges[1:]) / 2
mean_centers = (mean_edges[:-1] + mean_edges[1:]) / 2

# Build a realistic rainflow matrix with concentration at low amplitude / moderate mean
amplitude_grid, mean_grid = np.meshgrid(amplitude_centers, mean_centers, indexing="ij")

# Most cycles are low-amplitude near the mean load
cycle_density = np.exp(-0.5 * ((amplitude_grid - 40) / 30) ** 2 - 0.5 * ((mean_grid - 80) / 60) ** 2) * 5000

# Secondary cluster at moderate amplitude
cycle_density += np.exp(-0.5 * ((amplitude_grid - 90) / 25) ** 2 - 0.5 * ((mean_grid - 120) / 45) ** 2) * 800

# Sparse high-amplitude cycles (rare severe events)
cycle_density += np.exp(-0.5 * ((amplitude_grid - 150) / 20) ** 2 - 0.5 * ((mean_grid - 100) / 50) ** 2) * 50

# Convert to integer counts — threshold low values to zero for sparse edges
cycle_counts = np.round(cycle_density).astype(int)
cycle_counts[cycle_counts < 3] = 0

# Flatten for ColumnDataSource — only include non-zero bins
amp_flat = []
mean_flat = []
count_flat = []
amp_label = []
mean_label = []

for i in range(n_bins):
    for j in range(n_bins):
        if cycle_counts[i, j] > 0:
            amp_flat.append(amplitude_centers[i])
            mean_flat.append(mean_centers[j])
            count_flat.append(cycle_counts[i, j])
            amp_label.append(f"{amplitude_centers[i]:.0f}")
            mean_label.append(f"{mean_centers[j]:.0f}")

source = ColumnDataSource(
    data={
        "amplitude": amp_flat,
        "mean": mean_flat,
        "count": count_flat,
        "amp_label": amp_label,
        "mean_label": mean_label,
    }
)

# Bin dimensions for rect glyphs
amp_bin_width = amplitude_centers[1] - amplitude_centers[0]
mean_bin_width = mean_centers[1] - mean_centers[0]

# Sequential colormap — Inferno palette for distinctive thermal/engineering aesthetic (log scale)
palette = list(Inferno256)

# Log color mapper for wide count range
min_count = max(1, min(count_flat))
max_count = max(count_flat)
color_mapper = LogColorMapper(palette=palette, low=min_count, high=max_count, nan_color="#f5f5f5")

# Plot — square format for symmetric heatmap
p = figure(
    width=3600,
    height=3600,
    title="heatmap-rainflow · bokeh · pyplots.ai",
    x_axis_label="Cycle Mean Stress (MPa)",
    y_axis_label="Cycle Amplitude (MPa)",
    toolbar_location=None,
    tools="",
    x_range=(mean_edges[0] - mean_bin_width / 2, mean_edges[-1] + mean_bin_width / 2),
    y_range=(amplitude_edges[0] - amp_bin_width / 2, amplitude_edges[-1] + amp_bin_width / 2),
)

# Heatmap rectangles
r = p.rect(
    x="mean",
    y="amplitude",
    width=mean_bin_width,
    height=amp_bin_width,
    source=source,
    fill_color={"field": "count", "transform": color_mapper},
    line_color=None,
)

# Color bar
color_bar = r.construct_color_bar(
    width=80,
    ticker=LogTicker(),
    label_standoff=24,
    major_label_text_font_size="18pt",
    border_line_color=None,
    padding=30,
    title="Cycle Count",
    title_text_font_size="22pt",
    title_standoff=40,
)
p.add_layout(color_bar, "right")

# Hover tool for interactive HTML version
hover = HoverTool(
    tooltips=[("Amplitude", "@amp_label MPa"), ("Mean", "@mean_label MPa"), ("Count", "@count")], renderers=[r]
)
p.add_tools(hover)

# Styling
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid and axes — clean heatmap look
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
p.axis.minor_tick_line_color = None
p.outline_line_color = None

# Annotations — data storytelling to guide viewer
dominant_label = Label(
    x=120,
    y=25,
    text="↑ Dominant loading cluster (~5000 cycles)",
    text_font_size="20pt",
    text_color="white",
    text_font_style="bold",
    text_align="left",
    background_fill_color="#333333",
    background_fill_alpha=0.8,
)
p.add_layout(dominant_label)

rare_label = Label(
    x=-60,
    y=185,
    text="Rare severe events →",
    text_font_size="20pt",
    text_color="white",
    text_font_style="bold",
    text_align="left",
    background_fill_color="#333333",
    background_fill_alpha=0.75,
)
p.add_layout(rare_label)

# Background — light gray for zero-count bins to stand out against dark Inferno palette
p.background_fill_color = "#f5f5f5"
p.border_fill_color = "white"
p.min_border_right = 200
p.min_border_bottom = 80

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="heatmap-rainflow · bokeh · pyplots.ai")
