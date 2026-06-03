"""anyplot.ai
feynman-basic: Feynman Diagram for Particle Interactions
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-06-03
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    arrow,
    coord_fixed,
    element_rect,
    element_text,
    geom_label,
    geom_path,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_color_identity,
    scale_fill_identity,
    theme,
    theme_void,
    xlim,
    ylim,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — particle type colors (canonical order, first series = brand green)
FERMION_COLOR = "#009E73"  # brand green — fermions (e-, e+, q, q̄)
BOSON_COLOR = "#C475FD"  # lavender — Z* boson (dashed propagator, key mediator)
GLUON_COLOR = "#4467A3"  # blue — gluon (curly bremsstrahlung)
PHOTON_COLOR = "#BD8233"  # ochre — photon γ (wavy, shown in legend)

# Diagram: e+e- → Z* → qq̄g  (QED+QCD: annihilation, Z-mediated pair creation, gluon emission)
v1x, v1y = 0.28, 0.50  # V1: e+e- annihilation vertex
v2x, v2y = 0.58, 0.50  # V2: qq̄ pair creation vertex
v3x, v3y = 0.76, 0.63  # V3: gluon bremsstrahlung vertex
ext = 0.20  # external leg length

# Fermion segments (arrow convention: particle → vertex, antiparticle ← vertex)
# e-: arrow at V1 (electron arrives); e+: arrow at lower-left (positron arrow reversal)
# q: arrows away from V2/V3; q̄: arrow toward V2 (antiquark fermion-flow reversal)
fermion_df = pd.DataFrame(
    {
        "x": [0.06, v1x, v2x, v3x, 0.95],
        "y": [v1y + ext, v1y, v2y, v3y, v1y - ext],
        "xend": [v1x, 0.06, v3x, 0.95, v2x],
        "yend": [v1y, v1y - ext, v3y, v3y + 0.14, v2y],
        "particle": ["e⁻ (electron)", "e⁺ (positron)", "q (up quark)", "q (up quark cont.)", "q̅ (down antiquark)"],
    }
)
fermion_df["color"] = FERMION_COLOR

# Z* boson propagator — the key interaction mediator (emphasized: thicker, dashed)
boson_df = pd.DataFrame({"x": [v1x], "xend": [v2x], "y": [v1y], "yend": [v2y]})

# Gluon bremsstrahlung: V3 → lower-right (curly/looped via geom_path)
t_g = np.linspace(0, 1, 600)
gluon_dx, gluon_dy = 0.19, -0.21
gluon_df = pd.DataFrame(
    {
        "x": v3x + t_g * gluon_dx + 0.011 * np.sin(t_g * 10 * 2 * np.pi),
        "y": v3y + t_g * gluon_dy + 0.019 * np.sin(t_g * 10 * 2 * np.pi + np.pi / 2),
        "grp": 1,
    }
)

# Vertex dots (interactive tooltips in HTML export)
vertex_df = pd.DataFrame(
    {
        "x": [v1x, v2x, v3x],
        "y": [v1y, v2y, v3y],
        "vertex": ["V₁: e⁻e⁺ annihilation", "V₂: qq̅ pair creation", "V₃: gluon emission"],
    }
)

# Particle endpoint labels
labels_df = pd.DataFrame(
    {
        "x": [0.03, 0.03, (v1x + v2x) / 2, 0.97, 0.97, 0.97],
        "y": [v1y + ext + 0.02, v1y - ext - 0.02, v1y + 0.065, v3y + 0.15, v3y + gluon_dy + 0.02, v1y - ext - 0.02],
        "label": ["e⁻", "e⁺", "Z*", "q", "g", "q̅"],
        "fill": [ELEVATED_BG] * 6,
    }
)

# Time axis
time_df = pd.DataFrame({"x": [0.23], "xend": [0.63], "y": [0.10], "yend": [0.10]})
time_lbl = pd.DataFrame({"x": [0.43], "y": [0.055], "label": ["time"]})

# Legend (consolidated: one DataFrame per line type, one text DataFrame)
leg_x0, leg_len = 0.06, 0.065
leg_top, leg_dy = 0.97, 0.054

leg_fermion = pd.DataFrame({"x": [leg_x0], "xend": [leg_x0 + leg_len], "y": [leg_top], "yend": [leg_top]})
leg_boson_seg = pd.DataFrame(
    {"x": [leg_x0], "xend": [leg_x0 + leg_len], "y": [leg_top - leg_dy], "yend": [leg_top - leg_dy]}
)

t_lp = np.linspace(0, 1, 200)
leg_photon = pd.DataFrame(
    {"x": leg_x0 + t_lp * leg_len, "y": (leg_top - 2 * leg_dy) + 0.009 * np.sin(t_lp * 5 * 2 * np.pi), "grp": 1}
)

t_lg = np.linspace(0, 1, 300)
leg_gluon = pd.DataFrame(
    {
        "x": leg_x0 + t_lg * leg_len + 0.004 * np.sin(t_lg * 9 * 2 * np.pi),
        "y": (leg_top - 3 * leg_dy) + 0.009 * np.sin(t_lg * 9 * 2 * np.pi + np.pi / 2),
        "grp": 1,
    }
)

leg_text = pd.DataFrame(
    {
        "x": [leg_x0 + leg_len + 0.013] * 4,
        "y": [leg_top - i * leg_dy for i in range(4)],
        "label": ["Fermion", "Boson (Z*)", "Photon (γ)", "Gluon (g)"],
    }
)

# Reaction equation — data storytelling focal point (bold, right of legend)
eq_df = pd.DataFrame({"x": [0.57], "y": [0.975], "label": ["e⁻e⁺ → Z* → qq̅g"]})

title = "feynman-basic · python · letsplot · anyplot.ai"

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    plot_title=element_text(size=13, color=INK_SOFT),
    plot_margin=[20, 15, 15, 15],
    legend_position="none",
)

plot = (
    ggplot()
    + theme_void()
    # Z* boson: the key mediator — emphasized with thicker dashed line
    + geom_segment(
        data=boson_df,
        mapping=aes(x="x", y="y", xend="xend", yend="yend"),
        size=3.8,
        color=BOSON_COLOR,
        linetype="dashed",
    )
    # Fermion lines with direction arrows (lets-plot distinctive: native arrow())
    + geom_segment(
        data=fermion_df,
        mapping=aes(x="x", y="y", xend="xend", yend="yend", color="color"),
        size=2.5,
        arrow=arrow(angle=20, length=10, type="closed"),
        tooltips=layer_tooltips().line("@particle"),
    )
    + scale_color_identity()
    # Gluon bremsstrahlung (curly loops via geom_path)
    + geom_path(data=gluon_df, mapping=aes(x="x", y="y", group="grp"), size=2.5, color=GLUON_COLOR)
    # Vertex dots with interactive hover (lets-plot distinctive: layer_tooltips)
    + geom_point(
        data=vertex_df,
        mapping=aes(x="x", y="y"),
        size=10,
        color=INK,
        shape=16,
        tooltips=layer_tooltips().line("@vertex"),
    )
    # Particle labels with rounded backgrounds (lets-plot distinctive: geom_label)
    + geom_label(
        data=labels_df,
        mapping=aes(x="x", y="y", label="label", fill="fill"),
        size=22,
        color=INK,
        fontface="italic",
        label_padding=0.2,
        label_r=0.15,
        alpha=0.92,
    )
    + scale_fill_identity()
    # Time axis arrow
    + geom_segment(
        data=time_df,
        mapping=aes(x="x", y="y", xend="xend", yend="yend"),
        size=0.8,
        color=INK_SOFT,
        arrow=arrow(angle=20, length=7, type="open"),
    )
    + geom_text(data=time_lbl, mapping=aes(x="x", y="y", label="label"), size=10, color=INK_SOFT, fontface="italic")
    # Legend
    + geom_segment(
        data=leg_fermion,
        mapping=aes(x="x", y="y", xend="xend", yend="yend"),
        size=1.8,
        color=FERMION_COLOR,
        arrow=arrow(angle=20, length=6, type="closed"),
    )
    + geom_segment(
        data=leg_boson_seg,
        mapping=aes(x="x", y="y", xend="xend", yend="yend"),
        size=1.8,
        color=BOSON_COLOR,
        linetype="dashed",
    )
    + geom_path(data=leg_photon, mapping=aes(x="x", y="y", group="grp"), size=1.8, color=PHOTON_COLOR)
    + geom_path(data=leg_gluon, mapping=aes(x="x", y="y", group="grp"), size=1.8, color=GLUON_COLOR)
    + geom_text(data=leg_text, mapping=aes(x="x", y="y", label="label"), size=10, color=INK_SOFT, hjust=0)
    # Reaction equation — bold focal point showing the full QED+QCD process
    + geom_text(data=eq_df, mapping=aes(x="x", y="y", label="label"), size=18, color=INK, fontface="bold")
    + coord_fixed(ratio=0.5625)
    + xlim(-0.02, 1.08)
    + ylim(0.02, 1.05)
    + labs(title=title)
    + anyplot_theme
    + ggsize(800, 450)
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
