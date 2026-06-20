""" anyplot.ai
lightcurve-transit: Astronomical Light Curve
Library: letsplot 4.10.1 | Python 3.13.14
Quality: 93/100 | Updated: 2026-06-20
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_errorbar,
    geom_line,
    geom_point,
    geom_ribbon,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_color_manual,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")

# Imprint palette — first series always #009E73
IMPRINT_GREEN = "#009E73"
IMPRINT_LAVENDER = "#C475FD"

# Theme-adaptive chrome tokens
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
# Grid: rgba(INK, 0.15) composited on PAGE_BG
GRID_COLOR = "#D8D7D0" if THEME == "light" else "#3A3A36"

# Data: simulated phase-folded exoplanet transit
np.random.seed(42)
n_points = 400
phase = np.sort(np.random.uniform(0.0, 1.0, n_points))

transit_center = 0.5
transit_duration = 0.08
transit_depth = 0.01
ingress_duration = 0.015
half_dur = transit_duration / 2
half_ingress = ingress_duration / 2

# Limb-darkened transit model (observations)
dist_obs = np.abs(phase - transit_center)
model_flux = np.ones_like(phase)
in_transit = dist_obs < half_dur - half_ingress
r_obs = dist_obs[in_transit] / (half_dur - half_ingress)
model_flux[in_transit] = 1.0 - transit_depth * (1 - 0.3 * (1 - np.sqrt(1 - r_obs**2)))
in_ingress = (dist_obs >= half_dur - half_ingress) & (dist_obs < half_dur + half_ingress)
model_flux[in_ingress] = 1.0 - transit_depth * (half_dur + half_ingress - dist_obs[in_ingress]) / (2 * half_ingress)

flux_err = np.random.uniform(0.001, 0.003, n_points)
flux = model_flux + np.random.normal(0, 1, n_points) * flux_err

# Smooth model curve with uncertainty envelope
phase_model = np.linspace(0.0, 1.0, 1000)
dist_model = np.abs(phase_model - transit_center)
model_smooth = np.ones_like(phase_model)
in_transit_m = dist_model < half_dur - half_ingress
r_model = dist_model[in_transit_m] / (half_dur - half_ingress)
model_smooth[in_transit_m] = 1.0 - transit_depth * (1 - 0.3 * (1 - np.sqrt(1 - r_model**2)))
in_ingress_m = (dist_model >= half_dur - half_ingress) & (dist_model < half_dur + half_ingress)
model_smooth[in_ingress_m] = 1.0 - transit_depth * (half_dur + half_ingress - dist_model[in_ingress_m]) / (
    2 * half_ingress
)

model_upper = model_smooth + 0.0015
model_lower = model_smooth - 0.0015

df_obs = pd.DataFrame(
    {
        "phase": phase,
        "flux": flux,
        "flux_err": flux_err,
        "ymin": flux - flux_err,
        "ymax": flux + flux_err,
        "series": "Observations",
    }
)

df_model = pd.DataFrame(
    {
        "phase": phase_model,
        "flux": model_smooth,
        "upper": model_upper,
        "lower": model_lower,
        "series": "Transit Model",
        "band": "Model ±1.5σ",
    }
)

# Annotation: mark the transit minimum
transit_min = model_smooth[np.argmin(np.abs(phase_model - transit_center))]
df_annot = pd.DataFrame({"phase": [transit_center], "flux": [transit_min - 0.0018], "label": ["Transit Minimum"]})

plot = (
    ggplot()
    + geom_ribbon(
        aes(x="phase", ymin="lower", ymax="upper", fill="band"),
        data=df_model,
        alpha=0.18,
        color=IMPRINT_LAVENDER,
        size=0.0,
        tooltips=layer_tooltips()
        .line("Model flux|@flux")
        .line("Phase|@phase")
        .format("@flux", ".5f")
        .format("@phase", ".3f"),
    )
    + geom_errorbar(
        aes(x="phase", ymin="ymin", ymax="ymax"), data=df_obs, color=INK_MUTED, alpha=0.5, size=0.4, width=0.0
    )
    + geom_point(
        aes(x="phase", y="flux", color="series"),
        data=df_obs,
        size=2.5,
        alpha=0.5,
        tooltips=layer_tooltips()
        .line("Flux|@flux")
        .line("Phase|@phase")
        .line("Error|@flux_err")
        .format("@flux", ".5f")
        .format("@phase", ".3f")
        .format("@flux_err", ".4f"),
    )
    + geom_line(aes(x="phase", y="flux", color="series"), data=df_model, size=1.5, tooltips="none")
    + geom_text(aes(x="phase", y="flux", label="label"), data=df_annot, color=INK_SOFT, size=3, hjust=0.5, vjust=0.5)
    + scale_color_manual(values={"Observations": IMPRINT_GREEN, "Transit Model": IMPRINT_LAVENDER}, name="")
    + scale_fill_manual(values={"Model ±1.5σ": IMPRINT_LAVENDER}, name="")
    + scale_x_continuous(name="Orbital Phase", breaks=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    + scale_y_continuous(name="Relative Flux")
    + labs(
        title="lightcurve-transit · python · letsplot · anyplot.ai",
        subtitle="Phase-folded exoplanet transit  ·  Depth: ~1%  ·  Quadratic limb darkening model",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=16, face="bold", color=INK),
        plot_subtitle=element_text(size=10, color=INK_SOFT),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="top",
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=GRID_COLOR, size=0.4),
        axis_ticks=element_blank(),
        axis_line_x=element_line(color=INK_SOFT),
        axis_line_y=element_line(color=INK_SOFT),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
    )
    + ggsize(800, 450)
)

ggsave(plot, f"plot-{THEME}.png", scale=4, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
