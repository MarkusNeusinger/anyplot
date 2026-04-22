""" pyplots.ai
smith-chart-basic: Smith Chart for RF/Impedance
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-15
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Label
from bokeh.plotting import figure


# Reference impedance
Z0 = 50  # ohms

# Create figure (square for Smith chart)
p = figure(
    width=3600,
    height=3600,
    title="smith-chart-basic · bokeh · pyplots.ai",
    x_axis_label="Real(Γ)",
    y_axis_label="Imag(Γ)",
    x_range=(-1.35, 1.35),
    y_range=(-1.35, 1.35),
    match_aspect=True,
)

# Style settings
p.title.text_font_size = "32pt"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Smith chart grid colors
GRID_COLOR = "#808080"
GRID_ALPHA = 0.4
BOUNDARY_COLOR = "#306998"

# Draw unit circle (outer boundary - |Γ| = 1)
theta_circle = np.linspace(0, 2 * np.pi, 500)
unit_x = np.cos(theta_circle)
unit_y = np.sin(theta_circle)
p.line(unit_x, unit_y, line_width=3, line_color=BOUNDARY_COLOR, alpha=0.9)

# Constant resistance circles: r = 0, 0.2, 0.5, 1, 2, 5
r_values = [0, 0.2, 0.5, 1, 2, 5]
for r in r_values:
    if r == 0:
        # r=0 is the unit circle (already drawn)
        continue
    # Circle center at (r/(1+r), 0) with radius 1/(1+r)
    center = r / (1 + r)
    radius = 1 / (1 + r)
    theta = np.linspace(0, 2 * np.pi, 300)
    cx = center + radius * np.cos(theta)
    cy = radius * np.sin(theta)
    # Only keep points inside unit circle
    mask = cx**2 + cy**2 <= 1.001
    cx, cy = cx[mask], cy[mask]
    if len(cx) > 0:
        p.line(cx, cy, line_width=1.5, line_color=GRID_COLOR, alpha=GRID_ALPHA)

# Constant reactance arcs: x = ±0.2, ±0.5, ±1, ±2, ±5
x_values = [0.2, 0.5, 1, 2, 5]
for x in x_values:
    # Positive reactance arc: center at (1, 1/x) with radius |1/x|
    center_y = 1.0 / x
    radius = 1.0 / x
    # Generate arc points
    theta = np.linspace(-np.pi, np.pi, 500)
    ax = 1.0 + radius * np.cos(theta)
    ay = center_y + radius * np.sin(theta)
    # Keep only points inside unit circle
    mask = (ax**2 + ay**2 <= 1.001) & (ax >= -0.001)
    ax, ay = ax[mask], ay[mask]
    if len(ax) > 1:
        # Sort by angle from center for smooth arc
        angles = np.arctan2(ay - center_y, ax - 1.0)
        order = np.argsort(angles)
        p.line(ax[order], ay[order], line_width=1.5, line_color=GRID_COLOR, alpha=GRID_ALPHA)

    # Negative reactance arc: center at (1, -1/x)
    center_y = -1.0 / x
    radius = 1.0 / x
    theta = np.linspace(-np.pi, np.pi, 500)
    ax = 1.0 + radius * np.cos(theta)
    ay = center_y + radius * np.sin(theta)
    mask = (ax**2 + ay**2 <= 1.001) & (ax >= -0.001)
    ax, ay = ax[mask], ay[mask]
    if len(ax) > 1:
        angles = np.arctan2(ay - center_y, ax - 1.0)
        order = np.argsort(angles)
        p.line(ax[order], ay[order], line_width=1.5, line_color=GRID_COLOR, alpha=GRID_ALPHA)

# Draw horizontal axis (pure resistance line, x = 0)
p.line([-1, 1], [0, 0], line_width=2, line_color="#444444", alpha=0.6)

# Generate example impedance data (antenna S11 sweep from 1-6 GHz)
np.random.seed(42)
n_points = 50
freq = np.linspace(1e9, 6e9, n_points)  # 1-6 GHz

# Simulate realistic antenna impedance: resonance around 3.5 GHz
f_res = 3.5e9
Q = 5

# Series RLC model: Z = R + jX
# Resistance peaks near resonance, reactance crosses zero at resonance
R = 45 + 10 * np.exp(-((freq - f_res) ** 2) / (0.5e9) ** 2)
X = Z0 * Q * (freq / f_res - f_res / freq) + 5 * np.sin(2 * np.pi * freq / 2e9)

# Normalize impedance and convert to reflection coefficient Γ
z_norm = (R + 1j * X) / Z0
gamma = (z_norm - 1) / (z_norm + 1)
gamma_real = np.real(gamma)
gamma_imag = np.imag(gamma)

# Create data source for impedance locus
source = ColumnDataSource(data={"gamma_real": gamma_real, "gamma_imag": gamma_imag, "freq_ghz": freq / 1e9})

# Plot impedance locus curve
p.line("gamma_real", "gamma_imag", source=source, line_width=5, line_color="#FFD43B", alpha=0.9)
p.scatter(
    "gamma_real",
    "gamma_imag",
    source=source,
    size=14,
    fill_color="#FFD43B",
    line_color="#306998",
    line_width=2,
    alpha=0.85,
)

# Add frequency labels at key points along the locus
label_indices = [0, n_points // 4, n_points // 2, 3 * n_points // 4, n_points - 1]
for idx in label_indices:
    # Offset label position to avoid overlap with data points
    offset_y = 0.08 if gamma_imag[idx] >= 0 else -0.12
    freq_label = Label(
        x=gamma_real[idx],
        y=gamma_imag[idx] + offset_y,
        text=f"{freq[idx] / 1e9:.1f} GHz",
        text_font_size="18pt",
        text_color="#306998",
        text_font_style="bold",
    )
    p.add_layout(freq_label)

# Mark the matched condition (center point: Z = Z0, Γ = 0)
p.scatter([0], [0], size=22, fill_color="#306998", line_color="white", line_width=3, alpha=0.95)
center_label = Label(x=0.06, y=0.06, text="Z=Z₀", text_font_size="20pt", text_color="#306998", text_font_style="bold")
p.add_layout(center_label)

# Add resistance value labels on horizontal axis
for r in [0.2, 0.5, 1, 2]:
    gamma_r = r / (1 + r)
    r_label = Label(x=gamma_r, y=-0.1, text=f"r={r}", text_font_size="16pt", text_color="#666666", text_align="center")
    p.add_layout(r_label)

# Add reactance labels at chart boundary
for x in [0.5, 1, 2]:
    # Calculate position on unit circle for positive x
    # Intersection of x-arc with unit circle
    angle = 2 * np.arctan(1 / x)
    lx = np.cos(angle)
    ly = np.sin(angle)
    x_label = Label(x=lx + 0.05, y=ly + 0.02, text=f"x={x}", text_font_size="14pt", text_color="#666666")
    p.add_layout(x_label)
    # Negative x
    x_label_neg = Label(x=lx + 0.05, y=-ly - 0.06, text=f"x=-{x}", text_font_size="14pt", text_color="#666666")
    p.add_layout(x_label_neg)

# Grid and background styling
p.grid.visible = False
p.background_fill_color = "#fafafa"
p.border_fill_color = "#fafafa"

# Save PNG
export_png(p, filename="plot.png")

# Save HTML for interactive viewing
output_file("plot.html", title="Smith Chart - bokeh - pyplots.ai")
save(p)
