""" pyplots.ai
smith-chart-basic: Smith Chart for RF/Impedance
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-15
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_text,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Reference impedance
Z0 = 50

# Generate Smith chart grid - constant resistance circles
# For resistance r, circle center at (r/(r+1), 0) with radius 1/(r+1)
r_values = [0, 0.2, 0.5, 1, 2, 5]
theta = np.linspace(0, 2 * np.pi, 200)

r_circle_data = []
for r in r_values:
    cx = r / (r + 1)
    radius = 1 / (r + 1)
    x = cx + radius * np.cos(theta)
    y = radius * np.sin(theta)
    # Clip to unit circle
    mask = x**2 + y**2 <= 1.001
    r_circle_data.append(pd.DataFrame({"x": x[mask], "y": y[mask], "type": "r_circle", "value": f"r={r}"}))

r_circles_df = pd.concat(r_circle_data, ignore_index=True)

# Constant reactance arcs
# For reactance x, circle center at (1, 1/x) with radius 1/|x|
x_values = [0.2, 0.5, 1, 2, 5]
reactance_data = []

for xv in x_values:
    # Positive reactance (upper half)
    radius_x = 1 / abs(xv)
    cy_pos = 1 / xv
    t = np.linspace(0, 2 * np.pi, 500)
    arc_x = 1 + radius_x * np.cos(t)
    arc_y = cy_pos + radius_x * np.sin(t)
    # Keep only points inside unit circle
    mask = (arc_x**2 + arc_y**2 <= 1.001) & (arc_x >= -0.01)
    if np.any(mask):
        reactance_data.append(pd.DataFrame({"x": arc_x[mask], "y": arc_y[mask], "type": "x_arc", "value": f"x={xv}"}))

    # Negative reactance (lower half)
    cy_neg = -1 / xv
    arc_y_neg = cy_neg + radius_x * np.sin(t)
    mask_neg = (arc_x**2 + arc_y_neg**2 <= 1.001) & (arc_x >= -0.01)
    if np.any(mask_neg):
        reactance_data.append(
            pd.DataFrame({"x": arc_x[mask_neg], "y": arc_y_neg[mask_neg], "type": "x_arc", "value": f"x=-{xv}"})
        )

reactance_df = pd.concat(reactance_data, ignore_index=True)

# Outer boundary circle (|gamma| = 1)
boundary_theta = np.linspace(0, 2 * np.pi, 200)
boundary_df = pd.DataFrame(
    {"x": np.cos(boundary_theta), "y": np.sin(boundary_theta), "type": "boundary", "value": "boundary"}
)

# Horizontal axis (real axis)
axis_df = pd.DataFrame({"x": [-1, 1], "y": [0, 0], "type": "axis", "value": "axis"})

# Example impedance data: antenna S11 measurement from 1-6 GHz
np.random.seed(42)
n_points = 50
freq_ghz = np.linspace(1, 6, n_points)

# Simulate antenna impedance variation with frequency
# Creates realistic spiral pattern on Smith chart
z_real = 50 + 30 * np.sin(2 * np.pi * freq_ghz / 2.5) + np.random.randn(n_points) * 3
z_imag = 20 * np.cos(2 * np.pi * freq_ghz / 3) + 15 * (freq_ghz - 3) + np.random.randn(n_points) * 2

# Normalize impedance
z_norm = (z_real + 1j * z_imag) / Z0

# Convert to reflection coefficient (gamma) for Smith chart coordinates
gamma = (z_norm - 1) / (z_norm + 1)
gamma_real = np.real(gamma)
gamma_imag = np.imag(gamma)

impedance_df = pd.DataFrame({"x": gamma_real, "y": gamma_imag, "freq": freq_ghz, "type": "impedance"})

# Select frequency labels at key points
label_indices = [0, 12, 24, 36, 49]
labels_df = impedance_df.iloc[label_indices].copy()
labels_df["label"] = [f"{f:.1f} GHz" for f in labels_df["freq"]]
labels_df["y_offset"] = labels_df["y"] + 0.08

# Combine grid data
grid_df = pd.concat([r_circles_df, reactance_df, boundary_df, axis_df], ignore_index=True)

# Create plot
plot = (
    ggplot()
    # Grid lines
    + geom_path(
        aes(x="x", y="y", group="value"),
        data=grid_df[grid_df["type"] == "r_circle"],
        color="#CCCCCC",
        size=0.5,
        alpha=0.8,
    )
    + geom_path(
        aes(x="x", y="y", group="value"), data=grid_df[grid_df["type"] == "x_arc"], color="#CCCCCC", size=0.5, alpha=0.8
    )
    # Boundary circle
    + geom_path(aes(x="x", y="y"), data=boundary_df, color="#333333", size=1)
    # Real axis
    + geom_path(aes(x="x", y="y"), data=axis_df, color="#333333", size=0.5)
    # Impedance locus curve
    + geom_path(aes(x="x", y="y"), data=impedance_df, color="#306998", size=1.5)
    # Data points
    + geom_point(aes(x="x", y="y"), data=impedance_df, color="#306998", size=2, alpha=0.7)
    # Frequency labels
    + geom_text(aes(x="x", y="y_offset", label="label"), data=labels_df, color="#FFD43B", size=12, fontweight="bold")
    # Center point marker (Z = Z0)
    + annotate("point", x=0, y=0, color="#E74C3C", size=4)
    + annotate("text", x=0.12, y=-0.08, label="Z=Z₀", color="#E74C3C", size=11)
    # Styling
    + coord_fixed(ratio=1, xlim=(-1.3, 1.3), ylim=(-1.3, 1.3))
    + scale_x_continuous(breaks=[])
    + scale_y_continuous(breaks=[])
    + labs(title="smith-chart-basic · plotnine · pyplots.ai", x="", y="")
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=24, ha="center", weight="bold"),
        panel_background=element_rect(fill="white"),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        plot_background=element_rect(fill="white"),
    )
)

# Save
plot.save("plot.png", dpi=300)
