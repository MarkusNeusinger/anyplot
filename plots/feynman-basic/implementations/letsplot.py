"""pyplots.ai
feynman-basic: Feynman Diagram for Particle Interactions
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-07
"""

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

# --- Colors ---
BLUE = "#306998"
GOLD = "#D4973B"
TEAL = "#2A9D8F"
PURPLE = "#7B2D8E"
DARK = "#1A1A1A"
GRAY = "#AAAAAA"
LIGHT_BG = "#FAFAFA"

# --- Vertex positions ---
v1x, v1y = 0.30, 0.50
v2x, v2y = 0.70, 0.50
ext = 0.24

# --- Fermion segments with color column for identity scale ---
segments = pd.DataFrame(
    {
        "x": [v1x - ext, v1x, v2x, v2x + ext],
        "y": [v1y + ext, v1y, v2y, v2y - ext],
        "xend": [v1x, v1x - ext, v2x + ext, v2x],
        "yend": [v1y, v1y - ext, v2y + ext, v2y],
        "color": [BLUE] * 4,
        "particle": ["e\u207b (fermion)", "e\u207a (fermion)", "\u03bc\u207b (fermion)", "\u03bc\u207a (fermion)"],
    }
)

# --- Photon wavy line (v1 → v2) ---
t = np.linspace(0, 1, 400)
photon_x = v1x + t * (v2x - v1x)
photon_y = v1y + 0.035 * np.sin(t * 7 * 2 * np.pi)
photon_df = pd.DataFrame({"x": photon_x, "y": photon_y, "grp": 1})

# --- Vertices with tooltip data ---
vertex_df = pd.DataFrame(
    {"x": [v1x, v2x], "y": [v1y, v2y], "vertex": ["V\u2081 (annihilation)", "V\u2082 (pair creation)"]}
)

# --- Particle labels using geom_label (lets-plot distinctive: background fill) ---
labels_df = pd.DataFrame(
    {
        "x": [v1x - ext - 0.04, v1x - ext - 0.04, v2x + ext + 0.03, v2x + ext + 0.03, (v1x + v2x) / 2],
        "y": [v1y + ext + 0.03, v1y - ext - 0.03, v2y + ext + 0.04, v2y - ext - 0.04, v1y + 0.065],
        "label": ["e\u207b", "e\u207a", "\u03bc\u207b", "\u03bc\u207a", "\u03b3"],
        "fill": ["white", "white", "white", "white", LIGHT_BG],
    }
)

# --- Time arrow (bottom) ---
time_y = 0.14
time_df = pd.DataFrame({"x": [0.28], "xend": [0.72], "y": [time_y], "yend": [time_y]})
time_lbl = pd.DataFrame({"x": [0.50], "y": [time_y - 0.04], "label": ["time"]})

# --- Legend lines (compact, upper-left) ---
leg_x0, leg_len = 0.10, 0.08
leg_ys = {"fermion": 0.94, "photon": 0.88, "gluon": 0.82, "boson": 0.76}
leg_label_x = leg_x0 + leg_len + 0.02

# Fermion legend line (with native arrow)
leg_fermion = pd.DataFrame(
    {"x": [leg_x0], "xend": [leg_x0 + leg_len], "y": [leg_ys["fermion"]], "yend": [leg_ys["fermion"]]}
)

# Photon legend wavy line
t_pw = np.linspace(0, 1, 200)
leg_photon = pd.DataFrame(
    {"x": leg_x0 + t_pw * leg_len, "y": leg_ys["photon"] + 0.012 * np.sin(t_pw * 5 * 2 * np.pi), "grp": 1}
)

# Gluon legend curly line
t_g = np.linspace(0, 1, 500)
leg_gluon = pd.DataFrame(
    {
        "x": leg_x0 + t_g * leg_len + 0.006 * np.sin(t_g * 9 * 2 * np.pi),
        "y": leg_ys["gluon"] + 0.015 * np.sin(t_g * 9 * 2 * np.pi + np.pi / 2),
        "grp": 1,
    }
)

# Boson legend dashed line
leg_boson = pd.DataFrame({"x": [leg_x0], "xend": [leg_x0 + leg_len], "y": [leg_ys["boson"]], "yend": [leg_ys["boson"]]})

# Legend text
leg_labels = pd.DataFrame(
    {"x": [leg_label_x] * 4, "y": list(leg_ys.values()), "label": ["Fermion", "Photon", "Gluon", "Boson"]}
)

# --- Reaction equation annotation ---
equation_df = pd.DataFrame(
    {"x": [0.50], "y": [0.96], "label": ["e\u207be\u207a \u2192 \u03b3 \u2192 \u03bc\u207b\u03bc\u207a"]}
)

# --- Build plot using lets-plot distinctive features ---
plot = (
    ggplot()
    + theme_void()
    # Fermion lines with native arrow() (lets-plot distinctive feature)
    + geom_segment(
        data=segments,
        mapping=aes(x="x", y="y", xend="xend", yend="yend", color="color"),
        size=2.5,
        arrow=arrow(angle=25, length=12, type="closed"),
        tooltips=layer_tooltips().line("@particle"),
    )
    + scale_color_identity()
    # Photon wavy line
    + geom_path(data=photon_df, mapping=aes(x="x", y="y", group="grp"), size=2.5, color=GOLD)
    # Vertices with tooltips (lets-plot distinctive: interactive hover in HTML)
    + geom_point(
        data=vertex_df,
        mapping=aes(x="x", y="y"),
        size=12,
        color=DARK,
        shape=16,
        tooltips=layer_tooltips().line("@vertex"),
    )
    # Particle labels with geom_label (lets-plot distinctive: label backgrounds)
    + geom_label(
        data=labels_df,
        mapping=aes(x="x", y="y", label="label", fill="fill"),
        size=24,
        color=DARK,
        fontface="italic",
        label_padding=0.3,
        label_r=0.2,
        alpha=0.85,
    )
    + scale_fill_identity()
    # Time arrow using native arrow() (lets-plot distinctive)
    + geom_segment(
        data=time_df,
        mapping=aes(x="x", y="y", xend="xend", yend="yend"),
        size=1.0,
        color=GRAY,
        arrow=arrow(angle=25, length=10, type="closed"),
    )
    + geom_text(data=time_lbl, mapping=aes(x="x", y="y", label="label"), size=16, color=GRAY, fontface="italic")
    # --- Legend (top-left, compact) ---
    + geom_segment(
        data=leg_fermion,
        mapping=aes(x="x", y="y", xend="xend", yend="yend"),
        size=2.0,
        color=BLUE,
        arrow=arrow(angle=25, length=8, type="closed"),
    )
    + geom_path(data=leg_photon, mapping=aes(x="x", y="y", group="grp"), size=2.0, color=GOLD)
    + geom_path(data=leg_gluon, mapping=aes(x="x", y="y", group="grp"), size=2.0, color=TEAL)
    + geom_segment(
        data=leg_boson, mapping=aes(x="x", y="y", xend="xend", yend="yend"), size=2.0, color=PURPLE, linetype="dashed"
    )
    + geom_text(data=leg_labels, mapping=aes(x="x", y="y", label="label"), size=14, color=DARK, hjust=0)
    # Reaction equation
    + geom_text(data=equation_df, mapping=aes(x="x", y="y", label="label"), size=20, color="#4A6B82")
    # Styling with coord_fixed (lets-plot distinctive: maintains aspect ratio)
    + coord_fixed(ratio=0.5625)
    + xlim(-0.05, 1.05)
    + ylim(0.05, 1.00)
    + labs(title="feynman-basic \u00b7 letsplot \u00b7 pyplots.ai")
    + theme(
        panel_background=element_rect(fill=LIGHT_BG, color=LIGHT_BG),
        plot_background=element_rect(fill="white", color="white"),
        plot_title=element_text(size=24, face="bold", color="#1A3A5C"),
        plot_margin=[40, 20, 20, 20],
        legend_position="none",
    )
    + ggsize(1600, 900)
)

ggsave(plot, filename="plot.png", path=".", scale=3)
ggsave(plot, filename="plot.html", path=".")
