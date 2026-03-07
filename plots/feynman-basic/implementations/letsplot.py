""" pyplots.ai
feynman-basic: Feynman Diagram for Particle Interactions
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-07
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_polygon,
    geom_segment,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
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

# --- Vertex positions (centered, using more vertical space) ---
v1x, v1y = 0.30, 0.50
v2x, v2y = 0.70, 0.50
ext = 0.24  # longer fermion lines to fill canvas

# --- Fermion segments: (x, y, xend, yend) ---
segments = pd.DataFrame(
    {
        "x": [v1x - ext, v1x, v2x, v2x + ext],
        "y": [v1y + ext, v1y, v2y, v2y - ext],
        "xend": [v1x, v1x - ext, v2x + ext, v2x],
        "yend": [v1y, v1y - ext, v2y + ext, v2y],
    }
)

# --- Arrowheads via geom_polygon (cleaner than segment pairs) ---
hl, hw = 0.025, 0.013
dx = segments["xend"] - segments["x"]
dy = segments["yend"] - segments["y"]
lens = np.sqrt(dx**2 + dy**2)
ux, uy = dx / lens, dy / lens
px, py = -uy, ux
mid_frac = 0.55
mx = segments["x"] + mid_frac * dx
my = segments["y"] + mid_frac * dy

arrow_polys = pd.DataFrame(
    {
        "x": np.concatenate([mx - hl * ux + hw * px, mx, mx - hl * ux - hw * px]),
        "y": np.concatenate([my - hl * uy + hw * py, my, my - hl * uy - hw * py]),
        "grp": np.tile(np.arange(4), 3),
    }
)

# --- Photon wavy line (v1 → v2) ---
t = np.linspace(0, 1, 400)
photon_x = v1x + t * (v2x - v1x)
photon_y = v1y + 0.035 * np.sin(t * 7 * 2 * np.pi)
photon_df = pd.DataFrame({"x": photon_x, "y": photon_y, "grp": 1})

# --- Vertices ---
vertex_df = pd.DataFrame({"x": [v1x, v2x], "y": [v1y, v2y]})

# --- Particle labels ---
labels_df = pd.DataFrame(
    {
        "x": [v1x - ext - 0.04, v1x - ext - 0.04, v2x + ext + 0.03, v2x + ext + 0.03, (v1x + v2x) / 2],
        "y": [v1y + ext + 0.03, v1y - ext - 0.03, v2y + ext + 0.04, v2y - ext - 0.04, v1y + 0.055],
        "label": ["e\u207b", "e\u207a", "\u03bc\u207b", "\u03bc\u207a", "\u03b3"],
    }
)

# --- Time arrow (bottom, integrated into diagram area) ---
time_y = 0.14
time_df = pd.DataFrame({"x": [0.28], "xend": [0.72], "y": [time_y], "yend": [time_y]})
time_arrow = pd.DataFrame({"x": [0.71, 0.71, 0.72], "y": [time_y + 0.012, time_y - 0.012, time_y], "grp": [0, 0, 0]})
time_lbl = pd.DataFrame({"x": [0.50], "y": [time_y - 0.04], "label": ["time"]})

# --- Legend (compact, integrated below title on the left) ---
leg_x0, leg_len = 0.10, 0.08
leg_ys = {"fermion": 0.94, "photon": 0.88, "gluon": 0.82, "boson": 0.76}
leg_label_x = leg_x0 + leg_len + 0.02

# Fermion legend line
leg_fermion = pd.DataFrame(
    {"x": [leg_x0], "xend": [leg_x0 + leg_len], "y": [leg_ys["fermion"]], "yend": [leg_ys["fermion"]]}
)
# Fermion legend arrow
fa_mx = leg_x0 + leg_len * 0.6
fa_hl, fa_hw = 0.015, 0.008
leg_fermion_arrow = pd.DataFrame(
    {
        "x": [fa_mx - fa_hl, fa_mx, fa_mx - fa_hl],
        "y": [leg_ys["fermion"] - fa_hw, leg_ys["fermion"], leg_ys["fermion"] + fa_hw],
        "grp": [0, 0, 0],
    }
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

# --- Subtitle annotation (reaction equation, placed prominently) ---
equation_df = pd.DataFrame(
    {"x": [0.50], "y": [0.96], "label": ["e\u207be\u207a \u2192 \u03b3 \u2192 \u03bc\u207b\u03bc\u207a"]}
)

# --- Build plot ---
plot = (
    ggplot()
    + theme_void()
    # Fermion lines
    + geom_segment(data=segments, mapping=aes(x="x", y="y", xend="xend", yend="yend"), size=2.5, color=BLUE)
    # Arrowheads as filled polygons
    + geom_polygon(data=arrow_polys, mapping=aes(x="x", y="y", group="grp"), fill=BLUE, color=BLUE, size=0.5)
    # Photon wavy line
    + geom_path(data=photon_df, mapping=aes(x="x", y="y", group="grp"), size=2.5, color=GOLD)
    # Vertices
    + geom_point(data=vertex_df, mapping=aes(x="x", y="y"), size=12, color=DARK, shape=16)
    # Particle labels
    + geom_text(data=labels_df, mapping=aes(x="x", y="y", label="label"), size=24, color=DARK, fontface="italic")
    # Time arrow
    + geom_segment(data=time_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), size=1.0, color=GRAY)
    + geom_polygon(data=time_arrow, mapping=aes(x="x", y="y", group="grp"), fill=GRAY, color=GRAY, size=0.5)
    + geom_text(data=time_lbl, mapping=aes(x="x", y="y", label="label"), size=16, color=GRAY, fontface="italic")
    # --- Legend (top-left, compact) ---
    + geom_segment(data=leg_fermion, mapping=aes(x="x", y="y", xend="xend", yend="yend"), size=2.0, color=BLUE)
    + geom_polygon(data=leg_fermion_arrow, mapping=aes(x="x", y="y", group="grp"), fill=BLUE, color=BLUE, size=0.5)
    + geom_path(data=leg_photon, mapping=aes(x="x", y="y", group="grp"), size=2.0, color=GOLD)
    + geom_path(data=leg_gluon, mapping=aes(x="x", y="y", group="grp"), size=2.0, color=TEAL)
    + geom_segment(
        data=leg_boson, mapping=aes(x="x", y="y", xend="xend", yend="yend"), size=2.0, color=PURPLE, linetype="dashed"
    )
    + geom_text(data=leg_labels, mapping=aes(x="x", y="y", label="label"), size=14, color=DARK, hjust=0)
    # Reaction equation
    + geom_text(data=equation_df, mapping=aes(x="x", y="y", label="label"), size=20, color="#4A6B82")
    # Styling
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
