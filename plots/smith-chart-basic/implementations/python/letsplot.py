"""anyplot.ai
smith-chart-basic: Smith Chart for RF/Impedance
Library: letsplot 4.11.0 | Python 3.14.10
Quality: pending | Updated: 2026-11-26
"""

import os

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
    gggrid,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    theme,
    theme_void,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Constants
Z0 = 50  # Reference impedance (ohms)

# Columns: set these to your table's column names
FREQUENCY = "Frequency (Hz)"  # role: frequency
Z_REAL = "Resistance (Ω)"  # role: z_real
Z_IMAG = "Reactance (Ω)"  # role: z_imag

# Data: replace this block with your own table, for example df = pd.read_csv("s11.csv")
# Simulated antenna impedance sweep 1-6 GHz
n_points = 60
t = np.linspace(0, 2.5 * np.pi, n_points)
r_base = 20 + 80 * (1 - np.exp(-t / 2.5))
x_base = 50 * np.sin(t) * np.exp(-t / 6)
df = pd.DataFrame({FREQUENCY: np.linspace(1e9, 6e9, n_points), Z_REAL: r_base, Z_IMAG: x_base})

# Plot: reads only df and the constants above
n_points = len(df)
freq = df[FREQUENCY].to_numpy()
z_real = df[Z_REAL].to_numpy()
z_imag = df[Z_IMAG].to_numpy()
z_norm = (z_real + 1j * z_imag) / Z0
gamma = (z_norm - 1) / (z_norm + 1)
gamma_real = np.real(gamma)
gamma_imag = np.imag(gamma)

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

# Smith chart grid — constant resistance circles
# Circle centered at (r/(r+1), 0) with radius 1/(r+1)
grid_data = []
r_values = [0, 0.2, 0.5, 1, 2, 5]
for r in r_values:
    cx = r / (r + 1)
    rad = 1 / (r + 1)
    theta = np.linspace(0, 2 * np.pi, 120)
    x = cx + rad * np.cos(theta)
    y = rad * np.sin(theta)
    mask = (x**2 + y**2) <= 1.001
    for i in np.where(mask)[0]:
        grid_data.append({"x": x[i], "y": y[i], "type": "resistance", "group": f"r_{r}"})

# Constant reactance arcs
# Arc centered at (1, 1/x_val) with radius |1/x_val|
xv_values = [0.2, 0.5, 1, 2, 5]
for xv in xv_values:
    for sign in [1, -1]:
        x_val = sign * xv
        cy = 1 / x_val
        rad = abs(1 / x_val)
        # Arc runs from (1, 0) to its exact intersection with the unit circle
        x_hit = (xv**2 - 1) / (xv**2 + 1)
        y_hit = sign * xv * (1 - x_hit)
        start = -sign * np.pi / 2
        end = np.arctan2(y_hit - cy, x_hit - 1)
        end = start + (end - start + np.pi) % (2 * np.pi) - np.pi
        theta = np.linspace(start, end, 300)
        x = 1 + rad * np.cos(theta)
        y = cy + rad * np.sin(theta)
        for xi, yi in zip(x, y, strict=True):
            grid_data.append({"x": xi, "y": yi, "type": "reactance", "group": f"x_{x_val}"})

df_grid = pd.DataFrame(grid_data)

theta_circle = np.linspace(0, 2 * np.pi, 200)
df_boundary = pd.DataFrame({"x": np.cos(theta_circle), "y": np.sin(theta_circle)})
df_axis = pd.DataFrame({"x": [-1, 1], "y": [0, 0]})

# Resistance labels at the top of each r-circle (clear of the locus near the real axis);
# the r=0 circle is the boundary, labelled at its left end
df_r_labels = pd.DataFrame(
    [{"x": r / (r + 1), "y": 1 / (r + 1) + 0.06, "label": str(r)} for r in r_values if r > 0]
    + [{"x": -1.06, "y": 0, "label": "0"}]
)

# Reactance labels at unit-circle boundary intersection
# For xv: boundary at x2=(xv²-1)/(xv²+1), y2=xv*(1-x2)
xv_label_rows = []
for xv in xv_values:
    x2 = (xv**2 - 1) / (xv**2 + 1)
    y2 = xv * (1 - x2)
    scale = 1.12
    xv_label_rows.append({"x": x2 * scale, "y": y2 * scale, "label": f"+j{xv}"})
    xv_label_rows.append({"x": x2 * scale, "y": -y2 * scale, "label": f"-j{xv}"})
df_x_labels = pd.DataFrame(xv_label_rows)

label_indices = [0, n_points // 2, n_points - 1]
# Per-label nudge: each label sits right beside its own point
label_nudges = [(-0.02, -0.1), (-0.1, -0.12), (0.2, 0.07)]
df_freq_labels = pd.DataFrame(
    {
        "x": [gamma_real[i] + nx for i, (nx, ny) in zip(label_indices, label_nudges, strict=True)],
        "y": [gamma_imag[i] + ny for i, (nx, ny) in zip(label_indices, label_nudges, strict=True)],
        "label": [f"{freq[i] / 1e9:.1f} GHz" for i in label_indices],
    }
)

df_center = pd.DataFrame({"x": [0], "y": [0]})
df_freq_points = df_locus.iloc[label_indices]

plot = (
    ggplot()
    # Outer boundary
    + geom_path(aes(x="x", y="y"), data=df_boundary, color=INK, size=2.0)
    # Real axis
    + geom_path(aes(x="x", y="y"), data=df_axis, color=INK_SOFT, size=0.8)
    # Resistance circles
    + geom_path(
        aes(x="x", y="y", group="group"),
        data=df_grid[df_grid["type"] == "resistance"],
        color=INK_SOFT,
        size=0.5,
        alpha=0.5,
    )
    # Reactance arcs
    + geom_path(
        aes(x="x", y="y", group="group"),
        data=df_grid[df_grid["type"] == "reactance"],
        color=INK_SOFT,
        size=0.5,
        alpha=0.5,
    )
    # Resistance labels along real axis
    + geom_text(aes(x="x", y="y", label="label"), data=df_r_labels, size=10, color=INK_SOFT)
    # Reactance labels at chart boundary
    + geom_text(aes(x="x", y="y", label="label"), data=df_x_labels, size=9, color=INK_SOFT)
    # Impedance locus path
    + geom_path(aes(x="gamma_real", y="gamma_imag"), data=df_locus, color=BRAND, size=2)
    # Interactive hover points
    + geom_point(
        aes(x="gamma_real", y="gamma_imag"),
        data=df_locus,
        color=BRAND,
        size=3,
        alpha=0.8,
        tooltips=layer_tooltips()
        .line("Freq: @freq_ghz GHz")
        .line("Z: @z_real + j@z_imag Ω")
        .line("VSWR: @vswr")
        .format("z_real", ".1f")
        .format("z_imag", ".1f")
        .format("vswr", ".2f"),
    )
    # Key frequency points
    + geom_point(aes(x="gamma_real", y="gamma_imag"), data=df_freq_points, color=INK, size=5)
    # Matched condition marker at chart center
    + geom_point(aes(x="x", y="y"), data=df_center, color=INK_SOFT, size=6, shape=3)
    # Frequency labels along trajectory (pre-nudged per-label to avoid crowding)
    + geom_text(aes(x="x", y="y", label="label"), data=df_freq_labels, size=10, color=INK)
    + labs(title="smith-chart-basic · python · letsplot · anyplot.ai")
    + theme_void()
    + theme(
        plot_title=element_text(size=20, hjust=0.5, color=INK),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
    )
    + coord_fixed(ratio=1, xlim=(-1.25, 1.25), ylim=(-1.25, 1.25))
)
# The one-panel grid paints the whole square canvas with the page color
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
