""" pyplots.ai
smith-chart-basic: Smith Chart for RF/Impedance
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-15
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_text,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    theme,
    theme_void,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Reference impedance
Z0 = 50  # ohms

# Generate example impedance data: simulated antenna impedance sweep
np.random.seed(42)
n_points = 60
freq = np.linspace(1e9, 6e9, n_points)  # 1-6 GHz

# Simulate realistic antenna impedance that varies with frequency
# Creates a trajectory that traverses both upper (inductive) and lower (capacitive) regions
t = np.linspace(0, 2.5 * np.pi, n_points)
# Resistance transitions from low to high across frequency sweep
r_base = 20 + 80 * (1 - np.exp(-t / 2.5))  # Resistance varies 20-100 ohms
# Reactance oscillates between inductive (+) and capacitive (-) regions
x_base = 50 * np.sin(t) * np.exp(-t / 6)  # Stronger reactance swing
z_real = r_base + 3 * np.random.randn(n_points)
z_imag = x_base + 2 * np.random.randn(n_points)

# Normalize impedance
z_norm_real = z_real / Z0
z_norm_imag = z_imag / Z0

# Convert normalized impedance to reflection coefficient (gamma)
# gamma = (Z - Z0) / (Z + Z0) = (z_norm - 1) / (z_norm + 1)
z_norm = z_norm_real + 1j * z_norm_imag
gamma = (z_norm - 1) / (z_norm + 1)
gamma_real = np.real(gamma)
gamma_imag = np.imag(gamma)

# Create dataframe for impedance locus with full data for tooltips
df_locus = pd.DataFrame(
    {
        "gamma_real": gamma_real,
        "gamma_imag": gamma_imag,
        "freq_ghz": freq / 1e9,
        "z_real": z_real,
        "z_imag": z_imag,
        "vswr": (1 + np.abs(gamma)) / (1 - np.abs(gamma)),
    }
)

# Build Smith chart grid data - constant resistance circles
# Formula: circle centered at (r/(r+1), 0) with radius 1/(r+1)
grid_data = []
r_values = [0, 0.2, 0.5, 1, 2, 5]
for r in r_values:
    center_x = r / (r + 1)
    radius = 1 / (r + 1)
    theta = np.linspace(0, 2 * np.pi, 100)
    x = center_x + radius * np.cos(theta)
    y = radius * np.sin(theta)
    # Clip to unit circle
    mask = (x**2 + y**2) <= 1.001
    for i in np.where(mask)[0]:
        grid_data.append({"x": x[i], "y": y[i], "type": "resistance", "group": f"r_{r}"})

# Build Smith chart grid data - constant reactance arcs
# Formula: circle centered at (1, 1/x) with radius |1/x|
x_values = [0.2, 0.5, 1, 2, 5]
for xv in x_values:
    for sign in [1, -1]:
        x_val = sign * xv
        center_y = 1 / x_val
        radius = abs(1 / x_val)
        theta = np.linspace(0, 2 * np.pi, 100)
        x = 1 + radius * np.cos(theta)
        y = center_y + radius * np.sin(theta)
        # Keep only points inside unit circle
        mask = (x**2 + y**2) <= 1.001
        for i in np.where(mask)[0]:
            grid_data.append({"x": x[i], "y": y[i], "type": "reactance", "group": f"x_{x_val}"})

df_grid = pd.DataFrame(grid_data)

# Unit circle (outer boundary)
theta_circle = np.linspace(0, 2 * np.pi, 200)
df_boundary = pd.DataFrame({"x": np.cos(theta_circle), "y": np.sin(theta_circle)})

# Real axis (horizontal line through center)
df_axis = pd.DataFrame({"x": [-1, 1], "y": [0, 0]})

# Key frequency labels at start, middle, and end (reduced to avoid overlap)
label_indices = [0, n_points // 2, n_points - 1]
df_labels = pd.DataFrame(
    {
        "x": [gamma_real[i] for i in label_indices],
        "y": [gamma_imag[i] for i in label_indices],
        "label": [f"{freq[i] / 1e9:.1f} GHz" for i in label_indices],
    }
)

# Start/end marker dataframes with labels for legend
df_start = df_locus.head(1).copy()
df_start["marker"] = "Start (1.0 GHz)"
df_end = df_locus.tail(1).copy()
df_end["marker"] = "End (6.0 GHz)"

# Center point (matched condition Z = Z0)
df_center = pd.DataFrame({"x": [0], "y": [0]})

# Legend data for markers (positioned outside chart area)
df_legend = pd.DataFrame(
    {
        "x": [1.15, 1.15],
        "y": [0.15, -0.15],
        "color": ["#22C55E", "#DC2626"],
        "label": ["Start (1.0 GHz)", "End (6.0 GHz)"],
    }
)

# Create the Smith chart plot
plot = (
    ggplot()
    # Outer boundary circle
    + geom_path(aes(x="x", y="y"), data=df_boundary, color="#333333", size=1.5)
    # Real axis
    + geom_path(aes(x="x", y="y"), data=df_axis, color="#333333", size=0.8)
    # Grid lines - resistance circles
    + geom_path(
        aes(x="x", y="y", group="group"),
        data=df_grid[df_grid["type"] == "resistance"],
        color="#306998",
        size=0.6,
        alpha=0.5,
    )
    # Grid lines - reactance arcs
    + geom_path(
        aes(x="x", y="y", group="group"),
        data=df_grid[df_grid["type"] == "reactance"],
        color="#306998",
        size=0.6,
        alpha=0.5,
    )
    # Impedance locus curve
    + geom_path(aes(x="gamma_real", y="gamma_imag"), data=df_locus, color="#FFD43B", size=2.5)
    # Interactive points with hover tooltips showing impedance data
    + geom_point(
        aes(x="gamma_real", y="gamma_imag"),
        data=df_locus,
        color="#FFD43B",
        size=4,
        alpha=0.8,
        tooltips=layer_tooltips()
        .line("Freq: @freq_ghz GHz")
        .line("Z: @z_real + j@z_imag Ω")
        .line("VSWR: @vswr")
        .format("z_real", ".1f")
        .format("z_imag", ".1f")
        .format("vswr", ".2f"),
    )
    # Start marker (green)
    + geom_point(aes(x="gamma_real", y="gamma_imag"), data=df_start, color="#22C55E", size=10)
    # End marker (red)
    + geom_point(aes(x="gamma_real", y="gamma_imag"), data=df_end, color="#DC2626", size=10)
    # Center point (matched condition)
    + geom_point(aes(x="x", y="y"), data=df_center, color="#333333", size=6, shape=3)
    # Frequency labels along trajectory
    + geom_text(aes(x="x", y="y", label="label"), data=df_labels, size=14, nudge_x=0.08, nudge_y=0.08, color="#333333")
    # Legend markers (outside chart)
    + geom_point(aes(x="x", y="y"), data=df_legend[df_legend["label"].str.contains("Start")], color="#22C55E", size=8)
    + geom_point(aes(x="x", y="y"), data=df_legend[df_legend["label"].str.contains("End")], color="#DC2626", size=8)
    + geom_text(aes(x="x", y="y", label="label"), data=df_legend, size=12, hjust=0, nudge_x=0.05, color="#333333")
    # Styling
    + labs(title="smith-chart-basic · letsplot · pyplots.ai")
    + theme_void()
    + theme(
        plot_title=element_text(size=24, hjust=0.5),
        plot_background=element_rect(fill="white"),
        panel_background=element_rect(fill="white"),
    )
    + coord_fixed(ratio=1, xlim=(-1.3, 1.8), ylim=(-1.3, 1.3))  # Extend x to accommodate legend
    + ggsize(1200, 1200)  # Square aspect for Smith chart
)

# Save outputs
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
