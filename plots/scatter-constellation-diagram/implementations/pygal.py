"""pyplots.ai
scatter-constellation-diagram: Digital Modulation Constellation Diagram
Library: pygal 3.1.0 | Python 3.14.3
Quality: 78/100 | Created: 2026-03-17
"""

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
noise_std = np.sqrt(10 ** (-snr_db / 10) * np.mean(ideal_i**2 + ideal_q**2))
received_i = ideal_i[symbol_indices] + np.random.normal(0, noise_std, n_symbols)
received_q = ideal_q[symbol_indices] + np.random.normal(0, noise_std, n_symbols)

# Compute EVM (Error Vector Magnitude) per symbol
error_vectors = np.sqrt((received_i - ideal_i[symbol_indices]) ** 2 + (received_q - ideal_q[symbol_indices]) ** 2)
avg_power = np.sqrt(np.mean(ideal_i**2 + ideal_q**2))
evm_percent = float(np.mean(error_vectors) / avg_power * 100)

# Classify symbols by error magnitude for visual storytelling
evm_per_symbol = error_vectors / avg_power * 100
low_mask = evm_per_symbol <= np.percentile(evm_per_symbol, 50)
mid_mask = (evm_per_symbol > np.percentile(evm_per_symbol, 50)) & (evm_per_symbol <= np.percentile(evm_per_symbol, 85))
high_mask = evm_per_symbol > np.percentile(evm_per_symbol, 85)

# Style — refined palette with teal/amber/coral hierarchy
font = "DejaVu Sans, Helvetica, Arial, sans-serif"
boundary_color = "#8090a0"
custom_style = Style(
    background="white",
    plot_background="#f5f7fa",
    foreground="#1a1a2e",
    foreground_strong="#1a1a2e",
    foreground_subtle="#d0d5dd",
    guide_stroke_color="#c8cdd5",
    guide_stroke_dasharray="4, 6",
    colors=(
        boundary_color,
        boundary_color,
        boundary_color,
        boundary_color,
        boundary_color,
        boundary_color,
        "#0077b6",  # Low EVM — deep blue
        "#f4a261",  # Medium EVM — amber
        "#e63946",  # High EVM — coral red
        "#16697a",  # Ideal points — dark teal
        "#2a9d8f",  # EVM annotation — teal accent
    ),
    font_family=font,
    title_font_family=font,
    title_font_size=52,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=30,
    legend_font_family=font,
    value_font_size=26,
    tooltip_font_size=28,
    tooltip_font_family=font,
    opacity=0.55,
    opacity_hover=0.9,
    stroke_opacity=1,
    stroke_opacity_hover=1,
)

# Chart — square canvas for equal aspect ratio
chart = pygal.XY(
    width=3600,
    height=3600,
    style=custom_style,
    title="scatter-constellation-diagram · pygal · pyplots.ai",
    x_title="In-Phase (I)",
    y_title="Quadrature (Q)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=20,
    stroke=False,
    dots_size=5,
    show_x_guides=True,
    show_y_guides=True,
    x_value_formatter=lambda x: f"{x:+.1f}",
    value_formatter=lambda y: f"{y:+.1f}",
    margin_bottom=120,
    margin_left=70,
    margin_right=50,
    margin_top=60,
    range=(-5, 5),
    xrange=(-5, 5),
    print_values=False,
    print_zeroes=False,
    truncate_legend=-1,
    js=[],
)

# Decision boundaries — clearly visible dashed lines at +/-2, 0
boundary_vals = [-2.0, 0.0, 2.0]
for bv in boundary_vals:
    chart.add(
        None,
        [{"value": (bv, -4.8)}, {"value": (bv, 4.8)}],
        stroke=True,
        show_dots=False,
        stroke_style={"width": 5, "dasharray": "16, 8", "linecap": "butt"},
    )
    chart.add(
        None,
        [{"value": (-4.8, bv)}, {"value": (4.8, bv)}],
        stroke=True,
        show_dots=False,
        stroke_style={"width": 5, "dasharray": "16, 8", "linecap": "butt"},
    )

# Received symbols split by error magnitude — creates visual heat effect
low_points = [
    {"value": (float(received_i[i]), float(received_q[i])), "label": f"EVM: {evm_per_symbol[i]:.1f}%"}
    for i in range(n_symbols)
    if low_mask[i]
]
mid_points = [
    {"value": (float(received_i[i]), float(received_q[i])), "label": f"EVM: {evm_per_symbol[i]:.1f}%"}
    for i in range(n_symbols)
    if mid_mask[i]
]
high_points = [
    {"value": (float(received_i[i]), float(received_q[i])), "label": f"EVM: {evm_per_symbol[i]:.1f}%"}
    for i in range(n_symbols)
    if high_mask[i]
]

chart.add(f"Low EVM (n={len(low_points)})", low_points, stroke=False, dots_size=5)
chart.add(f"Mid EVM (n={len(mid_points)})", mid_points, stroke=False, dots_size=6)
chart.add(f"High EVM (n={len(high_points)})", high_points, stroke=False, dots_size=7)

# Ideal constellation points — large, prominent markers
ideal_points = [
    {"value": (float(ideal_i[k]), float(ideal_q[k])), "label": f"Ideal ({int(ideal_i[k]):+d}, {int(ideal_q[k]):+d})"}
    for k in range(16)
]
chart.add("Ideal 16-QAM", ideal_points, stroke=False, dots_size=16)

# EVM annotation — single labeled point in upper-left corner
chart.add(
    f"EVM = {evm_percent:.1f}%",
    [{"value": (-4.2, 4.5), "label": f"Mean EVM = {evm_percent:.1f}%"}],
    stroke=False,
    dots_size=0,
    show_dots=False,
)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
