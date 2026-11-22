"""anyplot.ai
smith-chart-basic: Smith Chart for RF/Impedance
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-11-22
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    arrow,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
Z0 = 50  # reference impedance in ohms (spec default)
R_VALUES = [0, 0.2, 0.5, 1, 2, 5]  # constant-resistance circles
X_VALUES = [0.2, 0.5, 1, 2, 5]  # constant-reactance arcs (both signs)
LABEL_FRACTIONS = [0.0, 0.3, 0.7, 1.0]  # labelled points as shares of the frequency sweep
LABEL_NUDGE_X = [0.00, 0.13, -0.13, 0.00]  # keeps neighbouring frequency labels apart
LABEL_NUDGE_Y = [0.15, 0.15, 0.15, 0.14]
LIM = 1.25  # half-width of the square view around the unit disc

# Columns: set these to your table's column names
FREQUENCY = "Frequency (GHz)"  # role: frequency
Z_REAL = "Resistance (ohm)"  # role: z_real
Z_IMAG = "Reactance (ohm)"  # role: z_imag
GAMMA_RE = "Re(Γ)"  # role: extra
GAMMA_IM = "Im(Γ)"  # role: extra
GROUP = "group"  # role: extra
TEXT = "text"  # role: extra
X_LABEL = "x_label"  # role: extra
Y_LABEL = "y_label"  # role: extra
X_END = "x_end"  # role: extra
Y_END = "y_end"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("s11.csv")
# Patch antenna S11 measurement from 1-6 GHz
np.random.seed(42)
n_points = 50
freq_ghz = np.linspace(1, 6, n_points)
z_real = 50 + 30 * np.sin(2 * np.pi * freq_ghz / 2.5) + np.random.randn(n_points) * 3
z_imag = 20 * np.cos(2 * np.pi * freq_ghz / 3) + 15 * (freq_ghz - 3) + np.random.randn(n_points) * 2
df = pd.DataFrame({FREQUENCY: freq_ghz, Z_REAL: z_real, Z_IMAG: z_imag})

# Plot: reads only df and the constants above
z_norm = (df[Z_REAL] + 1j * df[Z_IMAG]) / Z0
gamma = (z_norm - 1) / (z_norm + 1)
locus_df = pd.DataFrame({GAMMA_RE: np.real(gamma), GAMMA_IM: np.imag(gamma), FREQUENCY: df[FREQUENCY]})

# Smith chart grid: resistance circles
theta = np.linspace(0, 2 * np.pi, 200)
r_circle_data = []
for r in R_VALUES:
    cx = r / (r + 1)
    radius = 1 / (r + 1)
    x = cx + radius * np.cos(theta)
    y = radius * np.sin(theta)
    mask = x**2 + y**2 <= 1.001
    r_circle_data.append(pd.DataFrame({GAMMA_RE: x[mask], GAMMA_IM: y[mask], GROUP: f"r_{r}"}))
r_circles_df = pd.concat(r_circle_data, ignore_index=True)

# Smith chart grid: reactance arcs
reactance_data = []
for xv in X_VALUES:
    radius_x = 1 / abs(xv)
    t = np.linspace(0, 2 * np.pi, 500)
    arc_x = 1 + radius_x * np.cos(t)
    for sign, tag in [(1, "p"), (-1, "n")]:
        arc_y = (sign / xv) + radius_x * np.sin(t)
        mask = (arc_x**2 + arc_y**2 <= 1.001) & (arc_x >= -0.01)
        if np.any(mask):
            reactance_data.append(pd.DataFrame({GAMMA_RE: arc_x[mask], GAMMA_IM: arc_y[mask], GROUP: f"x_{tag}_{xv}"}))
reactance_df = pd.concat(reactance_data, ignore_index=True)

boundary_theta = np.linspace(0, 2 * np.pi, 300)
boundary_df = pd.DataFrame({GAMMA_RE: np.cos(boundary_theta), GAMMA_IM: np.sin(boundary_theta)})
axis_df = pd.DataFrame({GAMMA_RE: [-1.0, 1.0], GAMMA_IM: [0.0, 0.0]})

# Frequency labels at key points of the sweep
f_min, f_max = df[FREQUENCY].min(), df[FREQUENCY].max()
label_idx = [int(np.argmin(np.abs(df[FREQUENCY].to_numpy() - (f_min + p * (f_max - f_min))))) for p in LABEL_FRACTIONS]
labels_df = locus_df.iloc[label_idx].copy()
labels_df[TEXT] = [f"{f:.1f} GHz" for f in labels_df[FREQUENCY]]
labels_df[X_LABEL] = labels_df[GAMMA_RE].to_numpy() + np.array(LABEL_NUDGE_X)
labels_df[Y_LABEL] = labels_df[GAMMA_IM].to_numpy() + np.array(LABEL_NUDGE_Y)

# Resistance circle labels just above the real axis at each circle's leftmost point
r_labels_df = pd.DataFrame(
    {GAMMA_RE: [(r - 1) / (r + 1) + 0.05 for r in R_VALUES], GAMMA_IM: 0.09, TEXT: [str(r) for r in R_VALUES]}
)

# Mid-locus directional arrow to indicate increasing frequency
mid = len(locus_df) // 2
arr_df = pd.DataFrame(
    {
        GAMMA_RE: [locus_df[GAMMA_RE].iloc[mid - 2]],
        X_END: [locus_df[GAMMA_RE].iloc[mid]],
        GAMMA_IM: [locus_df[GAMMA_IM].iloc[mid - 2]],
        Y_END: [locus_df[GAMMA_IM].iloc[mid]],
    }
)

# Matched-load label next to the chart center (Z = Z0 sits at gamma = 0)
center_df = pd.DataFrame({GAMMA_RE: [0.15], GAMMA_IM: [-0.20], TEXT: ["Z=Z₀"]})

# Style
plot = (
    ggplot()
    + geom_path(aes(x=GAMMA_RE, y=GAMMA_IM, group=GROUP), data=r_circles_df, color=INK_SOFT, size=0.4, alpha=0.6)
    + geom_path(aes(x=GAMMA_RE, y=GAMMA_IM, group=GROUP), data=reactance_df, color=INK_SOFT, size=0.4, alpha=0.4)
    + geom_path(aes(x=GAMMA_RE, y=GAMMA_IM), data=boundary_df, color=INK, size=1.0)
    + geom_path(aes(x=GAMMA_RE, y=GAMMA_IM), data=axis_df, color=INK_SOFT, size=0.5)
    + geom_path(aes(x=GAMMA_RE, y=GAMMA_IM), data=locus_df, color=IMPRINT_PALETTE[0], size=1.5)
    + geom_point(aes(x=GAMMA_RE, y=GAMMA_IM), data=locus_df, color=IMPRINT_PALETTE[0], size=2.5, alpha=0.65)
    + geom_segment(
        aes(x=GAMMA_RE, xend=X_END, y=GAMMA_IM, yend=Y_END),
        data=arr_df,
        color=IMPRINT_PALETTE[0],
        size=2.0,
        arrow=arrow(length=0.10),
    )
    + geom_text(aes(x=X_LABEL, y=Y_LABEL, label=TEXT), data=labels_df, color=INK, size=9, fontweight="bold")
    + geom_text(aes(x=GAMMA_RE, y=GAMMA_IM, label=TEXT), data=r_labels_df, color=INK_MUTED, size=9)
    + annotate("point", x=0, y=0, color=IMPRINT_PALETTE[1], size=4)
    + geom_text(aes(x=GAMMA_RE, y=GAMMA_IM, label=TEXT), data=center_df, color=IMPRINT_PALETTE[1], size=9)
    + coord_fixed(ratio=1, xlim=(-LIM, LIM), ylim=(-LIM, LIM))
    + scale_x_continuous(breaks=[])
    + scale_y_continuous(breaks=[])
    + labs(title="smith-chart-basic · python · plotnine · anyplot.ai", x="", y="")
    + theme(
        figure_size=(6, 6),
        plot_title=element_text(size=12, ha="center", color=INK, fontweight="bold"),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_title=element_text(color=INK),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in")
