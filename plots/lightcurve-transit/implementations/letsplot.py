"""pyplots.ai
lightcurve-transit: Astronomical Light Curve
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-18
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_text,
    geom_errorbar,
    geom_line,
    geom_point,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_manual,
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


# Vectorized transit model with quadratic limb darkening
def compute_transit(phases):
    dist = np.abs(phases - transit_center)
    flux = np.ones_like(phases)
    # Full transit region
    in_transit = dist < half_dur - half_ingress
    r = dist[in_transit] / (half_dur - half_ingress)
    limb = 1 - 0.3 * (1 - np.sqrt(1 - r**2))
    flux[in_transit] = 1.0 - transit_depth * limb
    # Ingress/egress region
    in_ingress = (dist >= half_dur - half_ingress) & (dist < half_dur + half_ingress)
    frac = (half_dur + half_ingress - dist[in_ingress]) / (2 * half_ingress)
    flux[in_ingress] = 1.0 - transit_depth * frac
    return flux


model_flux = compute_transit(phase)

# Add noise to create observed flux
flux_err = np.random.uniform(0.001, 0.003, n_points)
flux = model_flux + np.random.normal(0, 1, n_points) * flux_err

# Smooth model curve
phase_model = np.linspace(0.0, 1.0, 1000)
model_smooth = compute_transit(phase_model)

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

df_model = pd.DataFrame({"phase": phase_model, "flux": model_smooth, "series": "Transit Model"})

# Plot
plot = (
    ggplot()
    + geom_errorbar(
        aes(x="phase", ymin="ymin", ymax="ymax"), data=df_obs, color="#8FAFC8", alpha=0.4, size=0.5, width=0.0
    )
    + geom_point(aes(x="phase", y="flux", color="series"), data=df_obs, size=4, alpha=0.7)
    + geom_line(aes(x="phase", y="flux", color="series"), data=df_model, size=2)
    + scale_color_manual(values={"Observations": "#306998", "Transit Model": "#E8442A"}, name="")
    + scale_x_continuous(name="Orbital Phase", breaks=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    + scale_y_continuous(name="Relative Flux")
    + labs(
        title="lightcurve-transit · letsplot · pyplots.ai",
        subtitle="Phase-folded exoplanet transit  ·  Depth: ~1%  ·  Quadratic limb darkening model",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        plot_subtitle=element_text(size=16, color="#666666"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_text=element_text(size=16),
        legend_position="top",
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.5),
        axis_ticks=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", scale=3, path=".")
ggsave(plot, "plot.html", path=".")
