""" pyplots.ai
eye-diagram-basic: Signal Integrity Eye Diagram
Library: pygal 3.1.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-17
"""

import importlib
import sys

import numpy as np


# Import pygal avoiding name collision with this filename
_cwd = sys.path[0]
sys.path[:] = [p for p in sys.path if p != _cwd]
pygal = importlib.import_module("pygal")
Style = importlib.import_module("pygal.style").Style
sys.path.insert(0, _cwd)

# Data — Simulated NRZ eye diagram
np.random.seed(42)

n_traces = 300
samples_per_ui = 150
total_samples = samples_per_ui * 2  # 2 UI window
time_ui = np.linspace(0, 2, total_samples)
transition_width = 0.08  # UI, controls bandwidth-limited rise/fall

all_voltages = []
for _ in range(n_traces):
    bits = np.random.randint(0, 2, 6)
    extended_time = np.linspace(-1, 3, samples_per_ui * 4)
    voltage = np.zeros_like(extended_time)

    # Vectorized sigmoid transitions at each bit boundary
    for bit_idx in range(1, len(bits)):
        boundary = bit_idx - 2
        voltage += (bits[bit_idx] - bits[bit_idx - 1]) / (1.0 + np.exp(-(extended_time - boundary) / transition_width))
    voltage += bits[0]
    voltage = np.clip(voltage, -0.2, 1.2)

    # Extract the 2-UI window
    mask = (extended_time >= 0) & (extended_time <= 2)
    trace_voltage = voltage[mask][:total_samples]

    # Add Gaussian noise (sigma ~5% of amplitude) and jitter (~3% of UI)
    trace_voltage = trace_voltage + np.random.normal(0, 0.05, len(trace_voltage))
    jittered_time = time_ui + np.random.normal(0, 0.03)
    all_voltages.append((jittered_time, trace_voltage))

# Build 2D density histogram
n_xbins, n_ybins = 100, 65
x_edges = np.linspace(-0.1, 2.1, n_xbins + 1)
y_edges = np.linspace(-0.3, 1.3, n_ybins + 1)
density = np.zeros((n_ybins, n_xbins))

for jittered_time, trace_voltage in all_voltages:
    xi = ((jittered_time - x_edges[0]) / (x_edges[-1] - x_edges[0]) * n_xbins).astype(int)
    yi = ((trace_voltage - y_edges[0]) / (y_edges[-1] - y_edges[0]) * n_ybins).astype(int)
    valid = (xi >= 0) & (xi < n_xbins) & (yi >= 0) & (yi < n_ybins)
    for x, y in zip(xi[valid], yi[valid], strict=True):
        density[y, x] += 1

# Smooth density with box filter (3x3, applied twice)
for _ in range(2):
    padded = np.pad(density, 1, mode="edge")
    density = (
        padded[:-2, :-2]
        + padded[:-2, 1:-1]
        + padded[:-2, 2:]
        + padded[1:-1, :-2]
        + padded[1:-1, 1:-1]
        + padded[1:-1, 2:]
        + padded[2:, :-2]
        + padded[2:, 1:-1]
        + padded[2:, 2:]
    ) / 9.0

max_density = density.max()

# Viridis-inspired colorblind-safe palette (6 density bands)
density_colors = ("#440154", "#31688e", "#21918c", "#5ec962", "#b5de2b", "#fde725")
band_names = ["Very Low", "Low", "Medium", "High", "Very High", "Peak"]
n_bands = len(density_colors)

# Assign density cells to color bands
band_data = [[] for _ in range(n_bands)]
for yi in range(n_ybins):
    for xi in range(n_xbins):
        val = density[yi, xi]
        if val < 0.5:
            continue
        t = min(0.999, val / (max_density * 0.7))
        band_idx = min(int(t * n_bands), n_bands - 1)
        x_center = (x_edges[xi] + x_edges[xi + 1]) / 2
        y_center = (y_edges[yi] + y_edges[yi + 1]) / 2
        band_data[band_idx].append({"value": (x_center, y_center)})

# pygal custom Style — dark plot background for eye diagram contrast
custom_style = Style(
    background="#ffffff",
    plot_background="#0a0a28",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#555555",
    colors=density_colors,
    title_font_size=56,
    label_font_size=34,
    major_label_font_size=34,
    legend_font_size=28,
    value_font_size=20,
    tooltip_font_size=22,
    stroke_width=0,
)

# Create pygal XY scatter chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="eye-diagram-basic · pygal · pyplots.ai",
    x_title="Time (UI)",
    y_title="Voltage (V)",
    stroke=False,
    dots_size=12,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=6,
    show_x_guides=False,
    show_y_guides=False,
    x_labels=[0.0, 0.5, 1.0, 1.5, 2.0],
    x_label_rotation=0,
    truncate_label=-1,
    print_values=False,
    show_dots=True,
)

# Add density bands as pygal series
for i in range(n_bands):
    if band_data[i]:
        chart.add(band_names[i], band_data[i])
    else:
        chart.add(band_names[i], [])

# Save PNG
chart.render_to_png("plot.png")

# Save HTML with interactive SVG (pygal native tooltips)
svg_content = chart.render(is_unicode=True)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>eye-diagram-basic - pygal</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center;
               min-height: 100vh; background: #f5f5f5; }}
        .chart {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <figure class="chart">
        {svg_content}
    </figure>
</body>
</html>
"""

with open("plot.html", "w", encoding="utf-8") as fout:
    fout.write(html_content)
