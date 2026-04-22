""" pyplots.ai
eye-diagram-basic: Signal Integrity Eye Diagram
Library: pygal 3.1.0 | Python 3.14.3
Quality: 83/100 | Updated: 2026-03-18
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

# Build high-resolution 2D density histogram for smooth rendering
n_xbins, n_ybins = 240, 140
x_edges = np.linspace(-0.05, 2.05, n_xbins + 1)
y_edges = np.linspace(-0.25, 1.25, n_ybins + 1)
density = np.zeros((n_ybins, n_xbins))

for jittered_time, trace_voltage in all_voltages:
    xi = ((jittered_time - x_edges[0]) / (x_edges[-1] - x_edges[0]) * n_xbins).astype(int)
    yi = ((trace_voltage - y_edges[0]) / (y_edges[-1] - y_edges[0]) * n_ybins).astype(int)
    valid = (xi >= 0) & (xi < n_xbins) & (yi >= 0) & (yi < n_ybins)
    for x, y in zip(xi[valid], yi[valid], strict=True):
        density[y, x] += 1

# Smooth density with 3x3 box filter (applied 4 times for smoother gradients)
for _ in range(4):
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

# Compute eye opening metrics for annotations
# Eye center is at 0.5 UI and 1.5 UI — measure at 0.5 UI
center_col = int(0.5 * n_xbins / 2.1)
col_density = density[:, center_col]
y_centers = (y_edges[:-1] + y_edges[1:]) / 2

# Find eye opening: low-density region between two high-density bands
threshold = max_density * 0.15
low_density_mask = col_density < threshold
low_indices = np.where(low_density_mask)[0]

# Eye opening is between ~0.1V and ~0.9V
eye_region = low_indices[(y_centers[low_indices] > 0.15) & (y_centers[low_indices] < 0.85)]
if len(eye_region) > 2:
    eye_bottom = y_centers[eye_region[0]]
    eye_top = y_centers[eye_region[-1]]
    eye_height = round(eye_top - eye_bottom, 3)
else:
    eye_bottom, eye_top, eye_height = 0.2, 0.8, 0.6

# Eye width: measure horizontal opening at midpoint voltage (0.5V)
mid_row = int((0.5 - y_edges[0]) / (y_edges[-1] - y_edges[0]) * n_ybins)
mid_row = np.clip(mid_row, 0, n_ybins - 1)
row_density = density[mid_row, :]
x_centers = (x_edges[:-1] + x_edges[1:]) / 2
low_x_mask = row_density < threshold
low_x_indices = np.where(low_x_mask)[0]
# First eye opening near 0.5 UI
eye_x_region = low_x_indices[(x_centers[low_x_indices] > 0.2) & (x_centers[low_x_indices] < 0.8)]
if len(eye_x_region) > 2:
    eye_left = x_centers[eye_x_region[0]]
    eye_right = x_centers[eye_x_region[-1]]
    eye_width = round(eye_right - eye_left, 3)
else:
    eye_left, eye_right, eye_width = 0.3, 0.7, 0.4

# Viridis-inspired colorblind-safe palette (10 density bands for smoother gradients)
density_colors = (
    "#440154",
    "#482878",
    "#3e4989",
    "#31688e",
    "#26838f",
    "#1f9e89",
    "#35b779",
    "#6ece58",
    "#b5de2b",
    "#fde725",
)
band_names = ["Minimal", "Very Low", "Low", "Low-Med", "Medium", "Med-High", "High", "Very High", "Intense", "Peak"]
n_bands = len(density_colors)

# Assign density cells to color bands with custom tooltip showing density %
band_data = [[] for _ in range(n_bands)]
for yi in range(n_ybins):
    for xi in range(n_xbins):
        val = density[yi, xi]
        if val < 0.2:
            continue
        t = min(0.999, val / (max_density * 0.55))
        band_idx = min(int(t * n_bands), n_bands - 1)
        x_center = round((x_edges[xi] + x_edges[xi + 1]) / 2, 3)
        y_center = round((y_edges[yi] + y_edges[yi + 1]) / 2, 3)
        pct = round(val / max_density * 100, 1)
        band_data[band_idx].append(
            {"value": (x_center, y_center), "label": f"{x_center:.2f} UI, {y_center:.3f} V — Density: {pct}%"}
        )

# Eye measurement annotation series — use pygal secondary_series for distinct rendering
eye_height_line = [
    {"value": (0.5, round(eye_bottom, 3)), "label": f"Eye Height: {eye_height:.3f} V"},
    {"value": (0.5, round(eye_top, 3)), "label": f"Eye Height: {eye_height:.3f} V"},
]
eye_width_line = [
    {"value": (round(eye_left, 3), 0.5), "label": f"Eye Width: {eye_width:.3f} UI"},
    {"value": (round(eye_right, 3), 0.5), "label": f"Eye Width: {eye_width:.3f} UI"},
]

# pygal custom Style — dark oscilloscope-style background
custom_style = Style(
    background="#0a0a2e",
    plot_background="#080825",
    foreground="#c0c0d0",
    foreground_strong="#e8e8f8",
    foreground_subtle="#30304a",
    colors=density_colors + ("#ff4444", "#44ddff"),
    title_font_size=56,
    label_font_size=36,
    major_label_font_size=36,
    legend_font_size=32,
    value_font_size=22,
    tooltip_font_size=28,
    stroke_width=0,
    font_family="'Courier New', monospace",
    title_font_family="'Courier New', monospace",
    label_font_family="'Courier New', monospace",
    legend_font_family="'Courier New', monospace",
    value_font_family="'Courier New', monospace",
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
    dots_size=5,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=6,
    legend_box_size=22,
    show_x_guides=False,
    show_y_guides=False,
    x_labels=[0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0],
    range=(-0.25, 1.25),
    x_label_rotation=0,
    truncate_label=-1,
    print_values=False,
    show_dots=True,
    margin=30,
    margin_bottom=90,
    spacing=15,
    js=[],
    interpolate="hermite",
)

# Add density bands as pygal series (low bands first for correct z-order)
for i in range(n_bands):
    chart.add(band_names[i], band_data[i] if band_data[i] else [], allow_interruptions=True)

# Add eye measurement annotation lines using pygal stroke series
chart.add(
    f"Eye Height ({eye_height:.2f} V)",
    eye_height_line,
    stroke=True,
    show_dots=True,
    dots_size=8,
    stroke_style={"width": 3, "dasharray": "8, 4"},
    allow_interruptions=False,
)
chart.add(
    f"Eye Width ({eye_width:.2f} UI)",
    eye_width_line,
    stroke=True,
    show_dots=True,
    dots_size=8,
    stroke_style={"width": 3, "dasharray": "8, 4"},
    allow_interruptions=False,
)

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
               min-height: 100vh; background: #0a0a2e; }}
        .chart {{ max-width: 100%; height: auto; }}
        .chart svg {{ filter: drop-shadow(0 0 20px rgba(253, 231, 37, 0.12)); }}
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
