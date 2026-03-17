""" pyplots.ai
scatter-constellation-diagram: Digital Modulation Constellation Diagram
Library: pygal 3.1.0 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-17
"""

import re

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# Data — 16-QAM constellation with received symbols under additive Gaussian noise
np.random.seed(42)

# Ideal 16-QAM constellation points on a 4x4 grid at +/-1, +/-3
ideal_vals = [-3, -1, 1, 3]
ideal_i = np.array([i for i in ideal_vals for _ in ideal_vals])
ideal_q = np.array([q for _ in ideal_vals for q in ideal_vals])

# Generate received symbols — 1000 symbols with Gaussian noise (SNR ~20 dB)
n_symbols = 1000
symbol_indices = np.random.randint(0, 16, n_symbols)
snr_db = 20
signal_power = np.mean(ideal_i**2 + ideal_q**2)
noise_std = np.sqrt(signal_power * 10 ** (-snr_db / 10))
received_i = ideal_i[symbol_indices] + np.random.normal(0, noise_std, n_symbols)
received_q = ideal_q[symbol_indices] + np.random.normal(0, noise_std, n_symbols)

# Add slight phase offset to outer symbols for realistic impairment
phase_offset = 0.015  # radians — subtle but visible on outer constellation
r = np.sqrt(ideal_i[symbol_indices] ** 2 + ideal_q[symbol_indices] ** 2)
received_i += -phase_offset * received_q * (r / r.max())
received_q += phase_offset * received_i * (r / r.max())

# Compute EVM (Error Vector Magnitude) per symbol
error_vectors = np.sqrt((received_i - ideal_i[symbol_indices]) ** 2 + (received_q - ideal_q[symbol_indices]) ** 2)
avg_power = np.sqrt(signal_power)
evm_percent = float(np.mean(error_vectors) / avg_power * 100)

# Classify symbols by error magnitude for visual storytelling
evm_per_symbol = error_vectors / avg_power * 100
p50, p85 = np.percentile(evm_per_symbol, 50), np.percentile(evm_per_symbol, 85)
low_mask = evm_per_symbol <= p50
mid_mask = (evm_per_symbol > p50) & (evm_per_symbol <= p85)
high_mask = evm_per_symbol > p85

# Style — colorblind-safe palette: teal / purple / orange hierarchy
font = "DejaVu Sans, Helvetica, Arial, sans-serif"
boundary_color = "#9ca8b5"
custom_style = Style(
    background="white",
    plot_background="#f4f6f9",
    foreground="#16213e",
    foreground_strong="#16213e",
    foreground_subtle="#d8dce4",
    guide_stroke_color="#d0d5de",
    guide_stroke_dasharray="2, 6",
    colors=(
        boundary_color,
        boundary_color,
        boundary_color,
        boundary_color,
        boundary_color,
        boundary_color,
        "#1b7a8a",  # Low EVM — teal
        "#7b4dba",  # Medium EVM — purple
        "#e36414",  # High EVM — orange
        "#c1272d",  # Ideal points — deep red
    ),
    font_family=font,
    title_font_family=font,
    title_font_size=54,
    label_font_size=44,
    major_label_font_size=40,
    legend_font_size=36,
    legend_font_family=font,
    value_font_size=32,
    tooltip_font_size=30,
    tooltip_font_family=font,
    opacity=0.68,
    opacity_hover=0.95,
    stroke_opacity=1,
    stroke_opacity_hover=1,
)

# Custom axis labels — pygal dict-based label format for precise control
axis_labels = [{"value": v, "label": f"{v:+.0f}"} for v in [-4, -3, -2, -1, 0, 1, 2, 3, 4]]

# Chart — square canvas for equal aspect ratio (constellation geometry)
chart = pygal.XY(
    width=3600,
    height=3600,
    style=custom_style,
    title="scatter-constellation-diagram · pygal · pyplots.ai",
    x_title="In-Phase (I)",
    y_title="Quadrature (Q)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=26,
    stroke=False,
    dots_size=7,
    show_x_guides=True,
    show_y_guides=True,
    x_labels=axis_labels,
    y_labels=axis_labels,
    x_value_formatter=lambda x: f"{x:+.1f}",
    value_formatter=lambda y: f"{y:+.1f}",
    margin_bottom=140,
    margin_left=90,
    margin_right=55,
    margin_top=65,
    range=(-5, 5),
    xrange=(-5, 5),
    print_values=False,
    print_zeroes=False,
    truncate_legend=-1,
    js=[],
)

# Decision boundaries — subtle dashed lines at +/-2, 0
boundary_vals = [-2.0, 0.0, 2.0]
for bv in boundary_vals:
    chart.add(
        None,
        [{"value": (bv, -4.8)}, {"value": (bv, 4.8)}],
        stroke=True,
        show_dots=False,
        stroke_style={"width": 3, "dasharray": "12, 8", "linecap": "butt"},
    )
    chart.add(
        None,
        [{"value": (-4.8, bv)}, {"value": (4.8, bv)}],
        stroke=True,
        show_dots=False,
        stroke_style={"width": 3, "dasharray": "12, 8", "linecap": "butt"},
    )

# Received symbols split by error magnitude — creates visual heat effect
low_points = [
    {
        "value": (float(received_i[i]), float(received_q[i])),
        "label": f"I={received_i[i]:+.2f}  Q={received_q[i]:+.2f}  EVM={evm_per_symbol[i]:.1f}%",
    }
    for i in range(n_symbols)
    if low_mask[i]
]
mid_points = [
    {
        "value": (float(received_i[i]), float(received_q[i])),
        "label": f"I={received_i[i]:+.2f}  Q={received_q[i]:+.2f}  EVM={evm_per_symbol[i]:.1f}%",
    }
    for i in range(n_symbols)
    if mid_mask[i]
]
high_points = [
    {
        "value": (float(received_i[i]), float(received_q[i])),
        "label": f"I={received_i[i]:+.2f}  Q={received_q[i]:+.2f}  EVM={evm_per_symbol[i]:.1f}%",
    }
    for i in range(n_symbols)
    if high_mask[i]
]

chart.add(f"Low EVM (n={len(low_points)})", low_points, stroke=False, dots_size=7)
chart.add(f"Mid EVM (n={len(mid_points)})", mid_points, stroke=False, dots_size=10)
chart.add(f"High EVM (n={len(high_points)})", high_points, stroke=False, dots_size=13)

# Ideal constellation points — large prominent cross-markers via SVG post-processing
ideal_points = [
    {"value": (float(ideal_i[k]), float(ideal_q[k])), "label": f"Ideal ({int(ideal_i[k]):+d}, {int(ideal_q[k]):+d})"}
    for k in range(16)
]
chart.add("Ideal 16-QAM", ideal_points, stroke=False, dots_size=20)

# Render SVG — pygal's native format
svg_content = chart.render(is_unicode=True)

# Inject styled EVM annotation box into SVG (leveraging pygal's SVG-native architecture)
evm_box = (
    f'<g transform="translate(420, 180)">'
    f'<rect x="0" y="0" width="320" height="60" rx="8" ry="8" '
    f'fill="white" fill-opacity="0.88" stroke="#16213e" stroke-width="2"/>'
    f'<text x="160" y="42" font-size="40" font-family="{font}" '
    f'font-weight="bold" fill="#16213e" text-anchor="middle">'
    f"EVM = {evm_percent:.1f}%</text></g>"
)
svg_content = svg_content.replace("</svg>", f"{evm_box}</svg>")


# Replace ideal point circles (r=20) with cross markers via SVG post-processing
# This leverages pygal's SVG-native architecture for custom marker shapes
def replace_circle_with_cross(m):
    full = m.group(0)
    coords = re.search(r'cx="([^"]+)".*?cy="([^"]+)"', full)
    if not coords:
        return full
    cx, cy = float(coords.group(1)), float(coords.group(2))
    arm = 30
    return (
        f'<g><line x1="{cx - arm}" y1="{cy}" x2="{cx + arm}" y2="{cy}" '
        f'stroke="#c1272d" stroke-width="8" stroke-linecap="round"/>'
        f'<line x1="{cx}" y1="{cy - arm}" x2="{cx}" y2="{cy + arm}" '
        f'stroke="#c1272d" stroke-width="8" stroke-linecap="round"/></g>'
    )


svg_content = re.sub(r"<circle[^>]*r=\"20\"[^>]*/?>", replace_circle_with_cross, svg_content)

# Save PNG via cairosvg and write HTML with embedded SVG
cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to="plot.png")
with open("plot.html", "w") as f:
    f.write(svg_content)
