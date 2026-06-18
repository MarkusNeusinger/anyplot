# ruff: noqa: F403, F405
"""anyplot.ai
root-locus-basic: Root Locus Plot for Control Systems
Library: letsplot 4.10.1 | Python 3.13
Quality: 90/100 | Updated: 2026-06-18
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *
from lets_plot import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — 4 branches, position 1 always first
BRANCH_COLORS = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]
# Alternating linetypes disambiguate overlapping real-axis segments
BRANCH_LINETYPES = ["solid", "dashed", "solid", "dashed"]

# Data — G(s) = (s + 3) / [s(s + 1)(s + 2)(s + 4)]
# Open-loop poles: 0, -1, -2, -4 | Open-loop zero: -3
den_coeffs = np.polymul(np.polymul([1, 0], [1, 1]), np.polymul([1, 2], [1, 4]))
open_loop_poles = np.array([0.0, -1.0, -2.0, -4.0])
open_loop_zeros = np.array([-3.0])

k_values = np.concatenate(
    [np.linspace(0, 0.5, 200), np.linspace(0.5, 5, 400), np.linspace(5, 30, 400), np.linspace(30, 120, 400)]
)

all_real, all_imag, all_gain, all_branch = [], [], [], []
for k in k_values:
    char_poly = np.polyadd(den_coeffs, k * np.array([0, 0, 0, 1, 3]))
    roots = np.sort_complex(np.roots(char_poly))
    for b, root in enumerate(roots):
        all_real.append(root.real)
        all_imag.append(root.imag)
        all_gain.append(k)
        all_branch.append(f"Branch {b + 1}")

df = pd.DataFrame({"real": all_real, "imaginary": all_imag, "gain": all_gain, "branch": all_branch})

# Open-loop poles and zeros for markers
poles_df = pd.DataFrame({"real": open_loop_poles, "imaginary": [0.0] * len(open_loop_poles)})
zeros_df = pd.DataFrame({"real": open_loop_zeros, "imaginary": [0.0] * len(open_loop_zeros)})

# Imaginary axis crossings (stability boundary)
crossing_mask = (np.abs(df["real"]) < 0.08) & (np.abs(df["imaginary"]) > 0.3)
crossings = df[crossing_mask].copy()
if len(crossings) > 0:
    crossings = crossings.sort_values("imaginary")
    crossing_pts = pd.concat(
        [crossings[crossings["imaginary"] > 0].head(1), crossings[crossings["imaginary"] < 0].head(1)]
    )
else:
    crossing_pts = pd.DataFrame(columns=df.columns)

# Direction arrows at representative gain values
arrow_gains = [5, 15, 50]
arrow_rows = []
for ag in arrow_gains:
    idx = np.argmin(np.abs(k_values - ag))
    subset = df[(df["gain"] >= k_values[max(0, idx - 1)]) & (df["gain"] <= k_values[min(len(k_values) - 1, idx + 1)])]
    for _, row in subset.drop_duplicates(subset="branch").iterrows():
        k_next = k_values[min(len(k_values) - 1, idx + 5)]
        next_pts = df[(np.abs(df["gain"] - k_next) < 1.0) & (df["branch"] == row["branch"])]
        if len(next_pts) > 0:
            npt = next_pts.iloc[0]
            dx, dy = npt["real"] - row["real"], npt["imaginary"] - row["imaginary"]
            mag = np.sqrt(dx**2 + dy**2)
            if mag > 0.01:
                scale = 0.25 / mag
                arrow_rows.append(
                    {
                        "x": row["real"],
                        "y": row["imaginary"],
                        "xend": row["real"] + dx * scale,
                        "yend": row["imaginary"] + dy * scale,
                    }
                )
arrows_df = pd.DataFrame(arrow_rows) if arrow_rows else pd.DataFrame(columns=["x", "y", "xend", "yend"])

# Damping ratio lines (constant ζ)
zeta_values = [0.2, 0.4, 0.6, 0.8]
r_max = 5.0
zeta_lines = []
for zeta in zeta_values:
    theta = np.arccos(zeta)
    zeta_lines += [
        {"x": 0, "y": 0, "xend": -r_max * np.cos(theta), "yend": r_max * np.sin(theta)},
        {"x": 0, "y": 0, "xend": -r_max * np.cos(theta), "yend": -r_max * np.sin(theta)},
    ]
zeta_df = pd.DataFrame(zeta_lines)

# Zeta labels — staggered radii for clear separation
r_factors = [0.32, 0.50, 0.66, 0.82]
zeta_label_df = pd.DataFrame(
    [
        {
            "x": -r_max * r_factors[i] * np.cos(np.arccos(z)),
            "y": r_max * r_factors[i] * np.sin(np.arccos(z)),
            "label": f"ζ={z}",
        }
        for i, z in enumerate(zeta_values)
    ]
)

# Natural frequency arcs (left half-plane)
wn_values = [1, 2, 3, 4]
wn_rows = []
for wn in wn_values:
    theta = np.linspace(np.pi / 2, 3 * np.pi / 2, 100)
    wn_rows.extend([{"real": wn * np.cos(t), "imaginary": wn * np.sin(t), "wn": f"ωn={wn}"} for t in theta])
wn_df = pd.DataFrame(wn_rows)

# Critical gain label — uses geom_label for legible background box
critical_gain = f"K ≈ {crossing_pts['gain'].iloc[0]:.1f}" if len(crossing_pts) > 0 else ""
critical_y = crossing_pts["imaginary"].max() if len(crossing_pts) > 0 else 2.0
crossing_label_df = pd.DataFrame({"x": [0.20], "y": [critical_y], "label": [critical_gain]})

title = "root-locus-basic · python · letsplot · anyplot.ai"

# Plot
plot = (
    ggplot()
    # Stable region — brand green tint, theme-adaptive alpha
    + geom_rect(
        aes(xmin="xmin", ymin="ymin", xmax="xmax", ymax="ymax"),
        data=pd.DataFrame({"xmin": [-5.5], "xmax": [0.0], "ymin": [-4.5], "ymax": [4.5]}),
        fill="#009E73",
        alpha=0.07 if THEME == "light" else 0.13,
        inherit_aes=False,
        tooltips="none",
    )
    # Natural frequency arcs
    + geom_path(
        aes(x="real", y="imaginary", group="wn"),
        data=wn_df,
        color=INK_MUTED,
        size=0.4,
        linetype="dashed",
        alpha=0.5,
        tooltips="none",
    )
    # Damping ratio lines
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"),
        data=zeta_df,
        color=INK_MUTED,
        size=0.4,
        linetype="dashed",
        alpha=0.5,
        tooltips="none",
    )
    # Zeta labels
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=zeta_label_df,
        size=3,
        color=INK_MUTED,
        inherit_aes=False,
        family="monospace",
    )
    # Stability boundary (imaginary axis) and real axis
    + geom_vline(xintercept=0, color=INK_SOFT, size=0.7)
    + geom_hline(yintercept=0, color=INK_MUTED, size=0.4)
    # Axis direction labels
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=pd.DataFrame({"x": [0.12], "y": [3.7], "label": ["jω"]}),
        size=4,
        color=INK_MUTED,
        inherit_aes=False,
        hjust=0,
        family="serif",
    )
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=pd.DataFrame({"x": [1.1], "y": [-0.22], "label": ["σ"]}),
        size=4,
        color=INK_MUTED,
        inherit_aes=False,
        hjust=0,
        family="serif",
    )
    # Region labels — Imprint semantic colors
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=pd.DataFrame({"x": [-4.3], "y": [2.9], "label": ["STABLE"]}),
        size=4.5,
        color="#009E73",
        alpha=0.50,
        inherit_aes=False,
        family="monospace",
        fontface="bold",
    )
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=pd.DataFrame({"x": [0.55], "y": [2.9], "label": ["UNSTABLE"]}),
        size=3.5,
        color="#AE3030",
        alpha=0.45,
        inherit_aes=False,
        family="monospace",
        fontface="bold",
    )
    # Root locus branches — color + linetype for branch disambiguation
    + geom_path(
        aes(x="real", y="imaginary", color="branch", linetype="branch"),
        data=df,
        size=1.6,
        alpha=0.9,
        tooltips=layer_tooltips()
        .format("gain", ".2f")
        .format("real", ".3f")
        .format("imaginary", ".3f")
        .line("Branch: @branch")
        .line("Gain K: @gain")
        .line("Re: @real")
        .line("Im: @imaginary"),
    )
    + scale_color_manual(values=BRANCH_COLORS, name="Locus Branch")
    + scale_linetype_manual(values=BRANCH_LINETYPES, name="Locus Branch")
    # Direction arrows
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"),
        data=arrows_df,
        color=INK_SOFT,
        size=1.0,
        arrow=arrow(length=12, ends="last", type="open"),
        inherit_aes=False,
        tooltips="none",
    )
    # Open-loop poles (× markers)
    + geom_point(
        aes(x="real", y="imaginary"),
        data=poles_df,
        shape=4,
        size=7,
        color=INK,
        stroke=2.5,
        inherit_aes=False,
        tooltips=layer_tooltips().line("Open-loop pole").line("s = @real"),
    )
    # Open-loop zeros (○ markers)
    + geom_point(
        aes(x="real", y="imaginary"),
        data=zeros_df,
        shape=1,
        size=7,
        color=INK,
        stroke=2.5,
        inherit_aes=False,
        tooltips=layer_tooltips().line("Open-loop zero").line("s = @real"),
    )
    # Imaginary axis crossings
    + geom_point(
        aes(x="real", y="imaginary"),
        data=crossing_pts,
        shape=18,
        size=7,
        color="#AE3030",
        inherit_aes=False,
        tooltips=layer_tooltips().line("Stability crossing").line("K ≈ @gain").line("Im: @imaginary"),
    )
    # Critical gain — geom_label for background-boxed annotation
    + geom_label(
        aes(x="x", y="y", label="label"),
        data=crossing_label_df,
        size=3.5,
        color="#AE3030",
        fill=ELEVATED_BG,
        inherit_aes=False,
        hjust=0,
        family="monospace",
        fontface="bold",
    )
    + labs(
        x="Real Axis (σ)",
        y="Imaginary Axis (jω)",
        title=title,
        caption="G(s) = (s + 3) / [s(s + 1)(s + 2)(s + 4)]  ·  × = poles  ·  ○ = zeros",
    )
    + coord_fixed(ratio=1, xlim=[-5.0, 1.5], ylim=[-4.0, 4.0])
    + ggsize(800, 450)
    + theme_minimal()
    + theme(
        axis_text=element_text(size=10, color=INK_SOFT, family="monospace"),
        axis_title=element_text(size=12, color=INK, face="bold"),
        plot_title=element_text(size=16, color=INK, face="bold"),
        plot_caption=element_text(size=9, color=INK_MUTED, face="italic"),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=11, color=INK, face="bold"),
        legend_position="right",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        axis_ticks=element_line(color=INK_MUTED, size=0.3),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_margin=[35, 45, 25, 25],
    )
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
