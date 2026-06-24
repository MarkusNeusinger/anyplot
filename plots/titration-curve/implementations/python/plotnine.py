""" anyplot.ai
titration-curve: Acid-Base Titration Curve
Library: plotnine 0.15.7 | Python 3.13.14
Quality: 86/100 | Updated: 2026-06-24
"""

import os
import sys


# Prevent this file from shadowing the installed plotnine package
sys.path = [p for p in sys.path if p not in ("", ".") and not p.endswith("/python")]

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_area,
    geom_line,
    geom_point,
    geom_ribbon,
    geom_segment,
    geom_text,
    ggplot,
    guide_legend,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette positions used in this chart
COLOR_PH = "#009E73"  # position 1: brand green — pH curve (first series)
COLOR_DERIV = "#C475FD"  # position 2: lavender — derivative curve

# Data — 25 mL of 0.1 M HCl titrated with 0.1 M NaOH (vectorized analytical calculation)
volume_hcl = 25.0
conc_hcl = 0.1
conc_naoh = 0.1
moles_hcl = volume_hcl * conc_hcl / 1000

volume_ml = np.concatenate([np.linspace(0, 24, 80), np.linspace(24, 26, 40), np.linspace(26, 50, 80)])

moles_naoh = conc_naoh * volume_ml / 1000
total_volume_L = (volume_hcl + volume_ml) / 1000
excess_h = np.clip(moles_hcl - moles_naoh, 1e-14, None) / total_volume_L
excess_oh = np.clip(moles_naoh - moles_hcl, 1e-14, None) / total_volume_L
ph_acid = -np.log10(excess_h)
ph_base = 14.0 + np.log10(excess_oh)
ph = np.where(moles_naoh < moles_hcl - 1e-10, ph_acid, np.where(moles_naoh > moles_hcl + 1e-10, ph_base, 7.0))

# Derivative dpH/dV — scaled to pH axis range for overlay display
_, unique_idx = np.unique(volume_ml, return_index=True)
unique_idx = np.sort(unique_idx)
vol_unique = volume_ml[unique_idx]
ph_unique = ph[unique_idx]
dph_dv_unique = np.gradient(ph_unique, vol_unique)
dph_dv = np.interp(volume_ml, vol_unique, dph_dv_unique)
dph_dv = np.nan_to_num(dph_dv, nan=0.0, posinf=0.0, neginf=0.0)
dph_max = dph_dv.max()
dph_scaled = dph_dv / dph_max * 12

# Long-format DataFrame for grammar-of-graphics layering
df_ph = pd.DataFrame({"volume_ml": volume_ml, "value": ph, "series": "pH"})
df_deriv = pd.DataFrame({"volume_ml": volume_ml, "value": dph_scaled, "series": "dpH/dV (scaled)"})
df = pd.concat([df_ph, df_deriv], ignore_index=True)

df_area = pd.DataFrame({"volume_ml": volume_ml, "value": dph_scaled})

# Transition region ribbon (±3 mL around equivalence point)
eq_volume = 25.0
eq_ph = 7.0
mask = (volume_ml >= 22) & (volume_ml <= 28)
df_ribbon = pd.DataFrame(
    {"volume_ml": volume_ml[mask], "ymin": np.clip(ph[mask] - 1.2, 0, 14), "ymax": np.clip(ph[mask] + 1.2, 0, 14)}
)

# Equivalence point marker and annotation DataFrames
df_eq = pd.DataFrame({"volume_ml": [eq_volume], "value": [eq_ph], "y_start": [0.0]})
df_eq_label = pd.DataFrame(
    {
        "volume_ml": [eq_volume + 2.5],
        "value": [eq_ph + 1.8],
        "label": [f"Equivalence Point\n({eq_volume:.0f} mL, pH {eq_ph:.0f})"],
    }
)
df_peak_label = pd.DataFrame(
    {"volume_ml": [38.0], "value": [11.0], "label": [f"Peak dpH/dV = {dph_max:.1f}\nat {eq_volume:.0f} mL"]}
)

palette = {"pH": COLOR_PH, "dpH/dV (scaled)": COLOR_DERIV}
title = "titration-curve · python · plotnine · anyplot.ai"

# Plot
plot = (
    ggplot()
    # Transition region shading around equivalence point
    + geom_ribbon(aes(x="volume_ml", ymin="ymin", ymax="ymax"), data=df_ribbon, fill=COLOR_PH, alpha=0.15)
    # Derivative area fill — more visible than default
    + geom_area(aes(x="volume_ml", y="value"), data=df_area, fill=COLOR_DERIV, alpha=0.18)
    # Equivalence point vertical dashed reference line
    + geom_segment(
        aes(x="volume_ml", xend="volume_ml", y="y_start", yend="value"),
        data=df_eq,
        linetype="dashed",
        color=INK_MUTED,
        size=0.6,
    )
    # Main curves via color aesthetic mapping
    + geom_line(aes(x="volume_ml", y="value", color="series"), data=df, size=1.5)
    # Equivalence point diamond marker — Imprint matte red for semantic emphasis
    + geom_point(aes(x="volume_ml", y="value"), data=df_eq, color="#AE3030", size=4, shape="D", stroke=0.5)
    # Annotations (idiomatic plotnine geom_text, not matplotlib annotate)
    + geom_text(
        aes(x="volume_ml", y="value", label="label"), data=df_eq_label, size=3, ha="left", color=INK, fontstyle="italic"
    )
    + geom_text(
        aes(x="volume_ml", y="value", label="label"),
        data=df_peak_label,
        size=2.5,
        ha="left",
        color=COLOR_DERIV,
        fontweight="bold",
    )
    # Scales
    + scale_color_manual(values=palette, name=" ", guide=guide_legend(override_aes={"size": 3}))
    + scale_x_continuous(breaks=range(0, 55, 5), limits=(0, 50))
    + scale_y_continuous(breaks=range(0, 15, 2), limits=(0, 14))
    + labs(x="Volume of NaOH added (mL)", y="pH / dpH/dV (scaled)", title=title)
    # Theme — Imprint-compliant, theme-adaptive chrome
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_title=element_text(size=12, weight="bold", color=INK, margin={"b": 10}),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=8, color=INK),
        legend_position=(0.15, 0.85),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.3),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_blank(),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.15),
        axis_line_x=element_line(color=INK_SOFT, size=0.5),
        axis_line_y=element_line(color=INK_SOFT, size=0.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
