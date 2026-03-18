""" pyplots.ai
lightcurve-transit: Astronomical Light Curve
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-18
"""

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

# Data - simulated exoplanet transit (phase-folded)
np.random.seed(42)
n_points = 400
phase = np.sort(np.random.uniform(0.0, 1.0, n_points))

# Transit parameters
transit_center = 0.5
transit_duration = 0.08
transit_depth = 0.01
ingress_duration = 0.015
half_dur = transit_duration / 2
half_ingress = ingress_duration / 2

# Vectorized transit model with quadratic limb darkening (observations)
dist_obs = np.abs(phase - transit_center)
model_flux = np.ones_like(phase)
in_transit = dist_obs < half_dur - half_ingress
r_obs = dist_obs[in_transit] / (half_dur - half_ingress)
model_flux[in_transit] = 1.0 - transit_depth * (1 - 0.3 * (1 - np.sqrt(1 - r_obs**2)))
in_ingress = (dist_obs >= half_dur - half_ingress) & (dist_obs < half_dur + half_ingress)
model_flux[in_ingress] = 1.0 - transit_depth * (half_dur + half_ingress - dist_obs[in_ingress]) / (2 * half_ingress)

# Add noise to create observed flux
flux_err = np.random.uniform(0.001, 0.003, n_points)
flux = model_flux + np.random.normal(0, 1, n_points) * flux_err

# Smooth model curve with uncertainty band
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

# Model uncertainty envelope (±0.0015 flux, realistic systematic uncertainty)
model_upper = model_smooth + 0.0015
model_lower = model_smooth - 0.0015

# DataFrames
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

# Plot with lets-plot distinctive features: geom_ribbon, layer_tooltips
plot = (
    ggplot()
    + geom_ribbon(
        aes(x="phase", ymin="lower", ymax="upper", fill="band"),
        data=df_model,
        alpha=0.15,
        color="#C44E52",
        size=0.0,
        tooltips=layer_tooltips()
        .line("Model flux|@flux")
        .line("Phase|@phase")
        .format("@flux", ".5f")
        .format("@phase", ".3f"),
    )
    + geom_errorbar(
        aes(x="phase", ymin="ymin", ymax="ymax"), data=df_obs, color="#A8C4D8", alpha=0.35, size=0.4, width=0.0
    )
    + geom_point(
        aes(x="phase", y="flux", color="series"),
        data=df_obs,
        size=3.5,
        alpha=0.45,
        tooltips=layer_tooltips()
        .line("Flux|@flux")
        .line("Phase|@phase")
        .line("Error|@flux_err")
        .format("@flux", ".5f")
        .format("@phase", ".3f")
        .format("@flux_err", ".4f"),
    )
    + geom_line(aes(x="phase", y="flux", color="series"), data=df_model, size=2, tooltips="none")
    + scale_color_manual(values={"Observations": "#306998", "Transit Model": "#C44E52"}, name="")
    + scale_fill_manual(values={"Model ±1.5σ": "#C44E52"}, name="")
    + scale_x_continuous(name="Orbital Phase", breaks=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    + scale_y_continuous(name="Relative Flux")
    + labs(
        title="lightcurve-transit · letsplot · pyplots.ai",
        subtitle="Phase-folded exoplanet transit  ·  Depth: ~1%  ·  Quadratic limb darkening model",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold", color="#2D2D2D"),
        plot_subtitle=element_text(size=16, color="#777777"),
        axis_title=element_text(size=20, color="#444444"),
        axis_text=element_text(size=16, color="#555555"),
        legend_text=element_text(size=16),
        legend_position="top",
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#ECECEC", size=0.4),
        axis_ticks=element_blank(),
        plot_background=element_rect(fill="#FAFAFA", color="#FAFAFA"),
        panel_background=element_rect(fill="#FAFAFA", color="#FAFAFA"),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", scale=3, path=".")
ggsave(plot, "plot.html", path=".")
