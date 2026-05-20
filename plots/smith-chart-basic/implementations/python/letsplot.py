"""anyplot.ai
smith-chart-basic: Smith Chart for RF/Impedance
Library: letsplot | Python 3.13
Quality: 91/100 | Updated: 2026-05-20
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
COLOR_START = "#0072B2"  # Okabe-Ito position 3
COLOR_END = "#D55E00"  # Okabe-Ito position 2

Z0 = 50  # Reference impedance (ohms)

# Simulated antenna impedance sweep 1–6 GHz
np.random.seed(42)
n_points = 60
freq = np.linspace(1e9, 6e9, n_points)
t = np.linspace(0, 2.5 * np.pi, n_points)
r_base = 20 + 80 * (1 - np.exp(-t / 2.5))
x_base = 50 * np.sin(t) * np.exp(-t / 6)
z_real = r_base + 3 * np.random.randn(n_points)
z_imag = x_base + 2 * np.random.randn(n_points)

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
        theta = np.linspace(0, 2 * np.pi, 120)
        x = 1 + rad * np.cos(theta)
        y = cy + rad * np.sin(theta)
        mask = (x**2 + y**2) <= 1.001
        for i in np.where(mask)[0]:
            grid_data.append({"x": x[i], "y": y[i], "type": "reactance", "group": f"x_{x_val}"})

df_grid = pd.DataFrame(grid_data)

theta_circle = np.linspace(0, 2 * np.pi, 200)
df_boundary = pd.DataFrame({"x": np.cos(theta_circle), "y": np.sin(theta_circle)})
df_axis = pd.DataFrame({"x": [-1, 1], "y": [0, 0]})

# Resistance labels at leftmost point of each r-circle on the real axis
df_r_labels = pd.DataFrame([{"x": (r - 1) / (r + 1), "y": 0, "label": str(r)} for r in r_values])

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
df_freq_labels = pd.DataFrame(
    {
        "x": [gamma_real[i] for i in label_indices],
        "y": [gamma_imag[i] for i in label_indices],
        "label": [f"{freq[i] / 1e9:.1f} GHz" for i in label_indices],
    }
)

df_start = df_locus.iloc[[0]]
df_end = df_locus.iloc[[-1]]
df_center = pd.DataFrame({"x": [0], "y": [0]})

df_legend = pd.DataFrame(
    {
        "x": [1.15, 1.15, 1.15],
        "y": [0.25, 0.05, -0.15],
        "grp": ["locus", "start", "end"],
        "label": ["Impedance locus", "Start (1.0 GHz)", "End (6.0 GHz)"],
    }
)

plot = (
    ggplot()
    # Outer boundary
    + geom_path(aes(x="x", y="y"), data=df_boundary, color=INK, size=1.5)
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
    + geom_text(aes(x="x", y="y", label="label"), data=df_r_labels, size=8, nudge_y=-0.08, color=INK_SOFT)
    # Reactance labels at chart boundary
    + geom_text(aes(x="x", y="y", label="label"), data=df_x_labels, size=7, color=INK_SOFT)
    # Impedance locus path
    + geom_path(aes(x="gamma_real", y="gamma_imag"), data=df_locus, color=BRAND, size=2.5)
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
    # Start marker
    + geom_point(aes(x="gamma_real", y="gamma_imag"), data=df_start, color=COLOR_START, size=10)
    # End marker
    + geom_point(aes(x="gamma_real", y="gamma_imag"), data=df_end, color=COLOR_END, size=10)
    # Matched condition marker at chart center
    + geom_point(aes(x="x", y="y"), data=df_center, color=INK_SOFT, size=6, shape=3)
    # Frequency labels along trajectory
    + geom_text(aes(x="x", y="y", label="label"), data=df_freq_labels, size=11, nudge_x=0.08, nudge_y=0.08, color=INK)
    # Manual legend outside chart area
    + geom_point(aes(x="x", y="y"), data=df_legend[df_legend["grp"] == "locus"], color=BRAND, size=5)
    + geom_point(aes(x="x", y="y"), data=df_legend[df_legend["grp"] == "start"], color=COLOR_START, size=7)
    + geom_point(aes(x="x", y="y"), data=df_legend[df_legend["grp"] == "end"], color=COLOR_END, size=7)
    + geom_text(aes(x="x", y="y", label="label"), data=df_legend, size=10, hjust=0, nudge_x=0.06, color=INK)
    + labs(title="smith-chart-basic · python · letsplot · anyplot.ai")
    + theme_void()
    + theme(
        plot_title=element_text(size=16, hjust=0.5, color=INK),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
    )
    + coord_fixed(ratio=1, xlim=(-1.35, 2.1), ylim=(-1.35, 1.35))
    + ggsize(720, 600)
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
