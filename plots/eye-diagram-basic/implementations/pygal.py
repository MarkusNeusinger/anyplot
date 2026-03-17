"""pyplots.ai
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

n_traces = 400
samples_per_ui = 200
total_samples = samples_per_ui * 2  # 2 UI window
time_ui = np.linspace(0, 2, total_samples)
transition_width = 0.07  # UI, controls bandwidth-limited rise/fall

all_voltages = []
for _ in range(n_traces):
    bits = np.random.randint(0, 2, 6)
    extended_time = np.linspace(-1, 3, samples_per_ui * 4)
    voltage = np.zeros_like(extended_time)

    for bit_idx in range(1, len(bits)):
        boundary = bit_idx - 2
        voltage += (bits[bit_idx] - bits[bit_idx - 1]) / (1.0 + np.exp(-(extended_time - boundary) / transition_width))
    voltage += bits[0]
    voltage = np.clip(voltage, -0.2, 1.2)

    mask = (extended_time >= 0) & (extended_time <= 2)
    trace_voltage = voltage[mask][:total_samples]

    # Gaussian noise (sigma ~5%) and per-trace jitter (~3% of UI)
    trace_voltage = trace_voltage + np.random.normal(0, 0.05, len(trace_voltage))
    jittered_time = time_ui + np.random.normal(0, 0.03)
    all_voltages.append((jittered_time, trace_voltage))

# Build higher-resolution 2D density histogram for smoother rendering
n_xbins, n_ybins = 160, 100
x_edges = np.linspace(-0.05, 2.05, n_xbins + 1)
y_edges = np.linspace(-0.2, 1.2, n_ybins + 1)
density = np.zeros((n_ybins, n_xbins))

for jittered_time, trace_voltage in all_voltages:
    xi = ((jittered_time - x_edges[0]) / (x_edges[-1] - x_edges[0]) * n_xbins).astype(int)
    yi = ((trace_voltage - y_edges[0]) / (y_edges[-1] - y_edges[0]) * n_ybins).astype(int)
    valid = (xi >= 0) & (xi < n_xbins) & (yi >= 0) & (yi < n_ybins)
    for x, y in zip(xi[valid], yi[valid], strict=True):
        density[y, x] += 1

# Smooth density with 3x3 box filter (applied 3 times for smoother gradients)
for _ in range(3):
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

# Viridis-inspired colorblind-safe palette (8 density bands for smoother gradients)
density_colors = ("#440154", "#443983", "#31688e", "#21918c", "#35b779", "#90d743", "#c8e020", "#fde725")
band_names = ["Very Low", "Low", "Low-Med", "Medium", "Med-High", "High", "Very High", "Peak"]
n_bands = len(density_colors)

# Assign density cells to color bands with custom tooltip showing density %
band_data = [[] for _ in range(n_bands)]
for yi in range(n_ybins):
    for xi in range(n_xbins):
        val = density[yi, xi]
        if val < 0.3:
            continue
        t = min(0.999, val / (max_density * 0.65))
        band_idx = min(int(t * n_bands), n_bands - 1)
        x_center = round((x_edges[xi] + x_edges[xi + 1]) / 2, 3)
        y_center = round((y_edges[yi] + y_edges[yi + 1]) / 2, 3)
        pct = round(val / max_density * 100, 1)
        band_data[band_idx].append(
            {"value": (x_center, y_center), "label": f"{x_center:.2f} UI, {y_center:.3f} V — Density: {pct}%"}
        )

# pygal custom Style — dark oscilloscope-style background
custom_style = Style(
    background="#0d0d30",
    plot_background="#0a0a28",
    foreground="#c0c0d0",
    foreground_strong="#e0e0f0",
    foreground_subtle="#404060",
    colors=density_colors,
    title_font_size=56,
    label_font_size=36,
    major_label_font_size=36,
    legend_font_size=36,
    value_font_size=22,
    tooltip_font_size=28,
    stroke_width=0,
    font_family="monospace",
    title_font_family="monospace",
    label_font_family="monospace",
    legend_font_family="monospace",
    value_font_family="monospace",
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
    dots_size=4,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=8,
    legend_box_size=24,
    show_x_guides=False,
    show_y_guides=False,
    x_labels=[0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0],
    range=(-0.2, 1.2),
    x_label_rotation=0,
    truncate_label=-1,
    print_values=False,
    show_dots=True,
    margin=40,
    margin_bottom=100,
    spacing=20,
    js=[],
)

# Add density bands as pygal series (low bands first for correct z-order)
for i in range(n_bands):
    chart.add(band_names[i], band_data[i] if band_data[i] else [], allow_interruptions=True)

# Save PNG
chart.render_to_png("plot.png")

# Save HTML with interactive SVG (pygal native tooltips and hover effects)
svg_content = chart.render(is_unicode=True)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>eye-diagram-basic · pygal · pyplots.ai</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center;
               min-height: 100vh; background: #0d0d30; }}
        .chart {{ max-width: 100%; height: auto; }}
        .chart svg {{ filter: drop-shadow(0 0 20px rgba(253, 231, 37, 0.15)); }}
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
