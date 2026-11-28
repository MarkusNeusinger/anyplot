"""anyplot.ai
mohr-circle: Mohr's Circle for Stress Analysis
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 88/100 | Created: 2026-05-30
"""

import os
import sys

import numpy as np
import pandas as pd


# Work around naming conflict: plotnine.py vs plotnine package
script_dir = os.path.dirname(os.path.abspath(__file__))
for _p in (script_dir, "", "."):
    if _p in sys.path:
        sys.path.remove(_p)

from plotnine import (  # noqa: E402
    aes,
    coord_fixed,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    theme,
)


# Theme tokens — Imprint palette
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]  # Mohr's circle — always first categorical series

# Constants
ROLES = ["Stress State", "Principal Stress", "Max Shear"]  # legend entries of a Mohr's circle

# Columns: set these to your table's column names
SIGMA_X = "σx (MPa)"  # role: sigma_x
SIGMA_Y = "σy (MPa)"  # role: sigma_y
TAU_XY = "τxy (MPa)"  # role: tau_xy

# Data: replace this block with your own stress state, for example df = pd.read_csv("stress.csv")
# Retaining wall panel under compressive loading: both normal stresses negative (MPa)
df = pd.DataFrame({SIGMA_X: [-120.0], SIGMA_Y: [-40.0], TAU_XY: [45.0]})

# Plot: reads only df and the constants above
sigma_x = df[SIGMA_X].iloc[0]
sigma_y = df[SIGMA_Y].iloc[0]
tau_xy = df[TAU_XY].iloc[0]

# Derived stress quantities
sigma_c = (sigma_x + sigma_y) / 2
radius = np.hypot((sigma_x - sigma_y) / 2, tau_xy)
sigma_1 = sigma_c + radius
sigma_2 = sigma_c - radius
tau_max = radius
angle_A = np.arctan2(tau_xy, sigma_x - sigma_c)  # CA direction, measured from the +σ axis
two_theta_p = np.degrees(abs(angle_A))


def fmt(value):
    """Signed number with a true minus sign."""
    return f"{value:.0f}".replace("-", "−")


# Mohr's circle path
angles = np.linspace(0, 2 * np.pi, 361)
circle_df = pd.DataFrame({"sigma": sigma_c + radius * np.cos(angles), "tau": radius * np.sin(angles)})

# Angle arc from the σ axis to line CA (visualising 2θp)
arc_r = radius * 0.34
arc_angles = np.linspace(0, angle_A, 60)
arc_df = pd.DataFrame({"sigma": sigma_c + arc_r * np.cos(arc_angles), "tau": arc_r * np.sin(arc_angles)})

# Reference lines: horizontal σ-axis and vertical through center
pad = radius * 0.36
ref_df = pd.DataFrame(
    {
        "x": [sigma_2 - pad, sigma_c],
        "xend": [sigma_1 + pad, sigma_c],
        "y": [0.0, -tau_max - pad],
        "yend": [0.0, tau_max + pad],
    }
)

# Diameter from A(σx, τxy) to B(σy, −τxy)
diam_df = pd.DataFrame({"x": [sigma_x], "xend": [sigma_y], "y": [tau_xy], "yend": [-tau_xy]})

# Key points with engineering roles
points_df = pd.DataFrame(
    {
        "sigma": [sigma_x, sigma_y, sigma_1, sigma_2, sigma_c, sigma_c],
        "tau": [tau_xy, -tau_xy, 0.0, 0.0, tau_max, -tau_max],
        "role": [ROLES[0], ROLES[0], ROLES[1], ROLES[1], ROLES[2], ROLES[2]],
    }
)

center_df = pd.DataFrame({"sigma": [sigma_c], "tau": [0.0]})

# Accent segment along the σ axis between σ2 and σ1 — draws the eye to the principal stress span
span_df = pd.DataFrame({"x": [sigma_2], "xend": [sigma_1], "y": [0.0], "yend": [0.0]})

# 2θp arc label — on the arc's bisector, outside the arc
angle_mid = angle_A / 2
arc_lbl_df = pd.DataFrame(
    {
        "sigma": [sigma_c + arc_r * 1.75 * np.cos(angle_mid)],
        "tau": [arc_r * 1.75 * np.sin(angle_mid)],
        "label": [f"2θp = {two_theta_p:.1f}°"],
    }
)

# Point labels: A sits on the side of σx relative to the center, B opposite; ha says which way the text extends
off = radius * 0.08
side = 1.0 if sigma_x >= sigma_c else -1.0
labels_df = pd.DataFrame(
    {
        "sigma": [
            sigma_x + side * off,
            sigma_y - side * off,
            sigma_1 + off,
            sigma_2 - off,
            sigma_c + off,
            sigma_c + off,
        ],
        "tau": [tau_xy + off, -tau_xy - off * 1.5, off * 0.9, off * 0.9, tau_max + off * 1.1, -tau_max - off * 1.5],
        "label": [
            f"A ({fmt(sigma_x)}, {fmt(tau_xy)})",
            f"B ({fmt(sigma_y)}, {fmt(-tau_xy)})",
            f"σ1 = {fmt(sigma_1)} MPa",
            f"σ2 = {fmt(sigma_2)} MPa",
            f"τmax = {fmt(tau_max)} MPa",
            f"−τmax = {fmt(-tau_max)} MPa",
        ],
        "ha": ["left" if side > 0 else "right", "right" if side > 0 else "left", "left", "right", "left", "left"],
    }
)

# Equal-aspect view centered on the circle, with room for the labels
reach = radius * 1.5
title = "mohr-circle · python · plotnine · anyplot.ai"

anyplot_theme = theme(
    figure_size=(6, 6),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.12),
    panel_grid_minor=element_blank(),
    panel_border=element_blank(),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(color=INK, size=12, ha="center"),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=8),
    legend_title=element_blank(),
    legend_position="bottom",
)

plot = (
    ggplot(circle_df, aes(x="sigma", y="tau"))
    # Accent segment from σ2 to σ1 — guides eye to the principal stress result
    + geom_segment(data=span_df, mapping=aes(x="x", xend="xend", y="y", yend="yend"), color=BRAND, size=4.0, alpha=0.25)
    # Dashed reference lines through center
    + geom_segment(
        data=ref_df, mapping=aes(x="x", xend="xend", y="y", yend="yend"), color=INK_MUTED, size=0.5, linetype="dashed"
    )
    # Diameter line from A to B
    + geom_segment(
        data=diam_df, mapping=aes(x="x", xend="xend", y="y", yend="yend"), color=INK_SOFT, size=0.8, alpha=0.7
    )
    # Mohr's circle — Imprint position 1 (brand green)
    + geom_path(color=BRAND, size=1.4)
    # Angle arc annotating 2θp
    + geom_path(data=arc_df, color=INK_SOFT, size=0.8)
    # Key points colored by engineering role
    + geom_point(data=points_df, mapping=aes(color="role"), size=4.0)
    + scale_color_manual(values=dict(zip(ROLES, IMPRINT_PALETTE[1:], strict=False)), limits=ROLES, name="")
    # Center mark C
    + geom_point(data=center_df, color=INK, size=2.5)
    # Angle arc label
    + geom_text(data=arc_lbl_df, mapping=aes(label="label"), ha="left", size=4.8, color=INK_SOFT)
    + labs(x="Normal Stress σ (MPa)", y="Shear Stress τ (MPa)", title=title)
    + coord_fixed(ratio=1, xlim=(sigma_c - reach, sigma_c + reach), ylim=(-reach, reach))
    + anyplot_theme
)
for ha, group in labels_df.groupby("ha", sort=False):
    plot += geom_text(data=group, mapping=aes(x="sigma", y="tau", label="label"), ha=ha, size=5.0, color=INK)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in")
