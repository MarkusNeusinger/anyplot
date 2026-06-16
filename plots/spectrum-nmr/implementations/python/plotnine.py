""" anyplot.ai
spectrum-nmr: NMR Spectrum (Nuclear Magnetic Resonance)
Library: plotnine 0.15.5 | Python 3.13.13
Quality: 90/100 | Updated: 2026-06-03
"""

import os
import sys


# This file is named 'plotnine.py' — remove its directory from sys.path so the
# 'plotnine' library is found in site-packages instead of looping back here.
_d = os.path.dirname(os.path.abspath(__file__))
if _d in sys.path:
    sys.path.remove(_d)
del _d

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_area,
    geom_line,
    geom_point,
    geom_segment,
    geom_text,
    geom_vline,
    ggplot,
    labs,
    scale_x_reverse,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # Imprint palette position 1 — ALWAYS first series

# Title with length-aware fontsize
title = "\xb9H NMR of Ethanol · spectrum-nmr · python · plotnine · anyplot.ai"
n = len(title)
title_fontsize = max(8, round(12 * 67 / n)) if n > 67 else 12

# Data — synthetic 1H NMR spectrum of ethanol (CH3CH2OH)
np.random.seed(42)
chemical_shift = np.linspace(-0.5, 5.0, 6000)

w = 0.015  # default Lorentzian peak width
intensity = np.zeros_like(chemical_shift)

# TMS reference peak at 0 ppm (singlet)
w_tms = 0.012
intensity += 0.4 * w_tms**2 / ((chemical_shift - 0.0) ** 2 + w_tms**2)

# CH3 triplet near 1.18 ppm (ratio 1:2:1)
triplet_center = 1.18
j_coupling = 0.07
intensity += 0.7 * w**2 / ((chemical_shift - (triplet_center - j_coupling)) ** 2 + w**2)
intensity += 1.4 * w**2 / ((chemical_shift - triplet_center) ** 2 + w**2)
intensity += 0.7 * w**2 / ((chemical_shift - (triplet_center + j_coupling)) ** 2 + w**2)

# CH2 quartet near 3.69 ppm (ratio 1:3:3:1)
quartet_center = 3.69
intensity += 0.35 * w**2 / ((chemical_shift - (quartet_center - 1.5 * j_coupling)) ** 2 + w**2)
intensity += 1.05 * w**2 / ((chemical_shift - (quartet_center - 0.5 * j_coupling)) ** 2 + w**2)
intensity += 1.05 * w**2 / ((chemical_shift - (quartet_center + 0.5 * j_coupling)) ** 2 + w**2)
intensity += 0.35 * w**2 / ((chemical_shift - (quartet_center + 1.5 * j_coupling)) ** 2 + w**2)

# OH singlet near 2.61 ppm
intensity += 0.55 * w**2 / ((chemical_shift - 2.61) ** 2 + w**2)

# Slight baseline noise
intensity += np.random.normal(0, 0.003, len(chemical_shift))
intensity = np.maximum(intensity, 0)

df = pd.DataFrame({"chemical_shift": chemical_shift, "intensity": intensity})

# Peak annotation data
labels_df = pd.DataFrame(
    {
        "x": [triplet_center, quartet_center, 2.61, 0.0],
        "y": [1.52, 1.17, 0.67, 0.45],
        "peak_y": [1.40, 1.05, 0.55, 0.40],
        "label": ["CH₃ (triplet)\n1.18 ppm", "CH₂ (quartet)\n3.69 ppm", "OH (singlet)\n2.61 ppm", "TMS\n0.00"],
        "group": ["main", "main", "main", "ref"],
    }
)

main_labels = labels_df[labels_df["group"] == "main"]
ref_labels = labels_df[labels_df["group"] == "ref"]

vline_df = pd.DataFrame({"xintercept": [triplet_center, quartet_center, 2.61]})

# Plot
plot = (
    ggplot(df, aes(x="chemical_shift", y="intensity"))
    + geom_area(fill=BRAND, alpha=0.08)
    + geom_vline(
        data=vline_df,
        mapping=aes(xintercept="xintercept"),
        color=BRAND,
        alpha=0.12,
        size=0.5,
        linetype="dashed",
        inherit_aes=False,
    )
    + geom_line(color=BRAND, size=1.0)
    + geom_point(data=labels_df, mapping=aes(x="x", y="peak_y"), color=BRAND, size=2.5, shape="o", inherit_aes=False)
    + geom_segment(
        data=labels_df,
        mapping=aes(x="x", xend="x", y="peak_y", yend="y"),
        color=INK_SOFT,
        size=0.4,
        linetype="dotted",
        inherit_aes=False,
    )
    + geom_text(
        data=main_labels,
        mapping=aes(x="x", y="y", label="label"),
        size=3.5,
        color=INK,
        fontweight="bold",
        va="bottom",
        ha="center",
        inherit_aes=False,
    )
    + geom_text(
        data=ref_labels,
        mapping=aes(x="x", y="y", label="label"),
        size=3.0,
        color=INK_SOFT,
        va="bottom",
        ha="center",
        inherit_aes=False,
    )
    + annotate("text", x=4.6, y=0.03, label="baseline", size=2.5, color=INK_MUTED, fontstyle="italic")
    + scale_x_reverse(limits=(5.0, -0.5), breaks=[0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0])
    + scale_y_continuous(breaks=[], limits=(-0.05, 1.72))
    + coord_cartesian(expand=False)
    + labs(x="Chemical Shift (ppm)", y="Intensity", title=title)
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7, color=INK_SOFT),
        axis_title_x=element_text(size=10, color=INK, margin={"t": 8}),
        axis_title_y=element_text(size=10, color=INK_MUTED),
        axis_text_x=element_text(size=8, color=INK_SOFT),
        axis_text_y=element_blank(),
        axis_ticks_major_y=element_blank(),
        axis_line_x=element_line(color=INK_SOFT, size=0.6),
        axis_line_y=element_blank(),
        plot_title=element_text(size=title_fontsize, color=INK, margin={"b": 8}),
        panel_background=element_rect(fill=PAGE_BG, color="none"),
        plot_background=element_rect(fill=PAGE_BG, color="none"),
        panel_border=element_blank(),
        panel_grid_major_x=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        plot_margin=0.04,
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
