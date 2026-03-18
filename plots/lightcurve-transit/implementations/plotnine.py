"""pyplots.ai
lightcurve-transit: Astronomical Light Curve
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-03-18
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_text,
    geom_line,
    geom_linerange,
    geom_point,
    ggplot,
    labs,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data
np.random.seed(42)
n_points = 400
phase = np.sort(np.random.uniform(0.0, 1.0, n_points))

transit_center = 0.5
transit_half_dur = 0.04
ingress_half = 0.01
transit_depth = 0.012
u1, u2 = 0.4, 0.1


transit_model = np.ones_like(phase)
for i, p in enumerate(phase):
    dist = abs(p - transit_center)
    if dist < transit_half_dur - ingress_half:
        r = dist / transit_half_dur
        mu = np.sqrt(max(1 - r**2, 0))
        limb = 1 - u1 * (1 - mu) - u2 * (1 - mu) ** 2
        transit_model[i] = 1.0 - transit_depth * limb
    elif dist < transit_half_dur + ingress_half:
        frac = (transit_half_dur + ingress_half - dist) / (2 * ingress_half)
        frac = 3 * frac**2 - 2 * frac**3
        r = dist / transit_half_dur
        mu = np.sqrt(max(1 - min(r, 1) ** 2, 0))
        limb = 1 - u1 * (1 - mu) - u2 * (1 - mu) ** 2
        transit_model[i] = 1.0 - transit_depth * limb * frac

flux_err = np.random.uniform(0.0008, 0.0025, n_points)
flux = transit_model + np.random.normal(0, 1, n_points) * flux_err

phase_fine = np.linspace(0.0, 1.0, 2000)
model_fine = np.ones(2000)
for i, p in enumerate(phase_fine):
    dist = abs(p - transit_center)
    if dist < transit_half_dur - ingress_half:
        r = dist / transit_half_dur
        mu = np.sqrt(max(1 - r**2, 0))
        limb = 1 - u1 * (1 - mu) - u2 * (1 - mu) ** 2
        model_fine[i] = 1.0 - transit_depth * limb
    elif dist < transit_half_dur + ingress_half:
        frac = (transit_half_dur + ingress_half - dist) / (2 * ingress_half)
        frac = 3 * frac**2 - 2 * frac**3
        r = dist / transit_half_dur
        mu = np.sqrt(max(1 - min(r, 1) ** 2, 0))
        limb = 1 - u1 * (1 - mu) - u2 * (1 - mu) ** 2
        model_fine[i] = 1.0 - transit_depth * limb * frac

df_obs = pd.DataFrame({"phase": phase, "flux": flux, "flux_err": flux_err})

df_model = pd.DataFrame({"phase": phase_fine, "flux": model_fine})

# Plot
plot = (
    ggplot()
    + geom_linerange(
        aes(x="phase", ymin="flux - flux_err", ymax="flux + flux_err"),
        data=df_obs,
        color="#92b4cc",
        alpha=0.4,
        size=0.3,
    )
    + geom_point(aes(x="phase", y="flux"), data=df_obs, color="#306998", alpha=0.6, size=1.5, stroke=0)
    + geom_line(aes(x="phase", y="flux"), data=df_model, color="#e8453c", size=1.6)
)

# Style
plot = (
    plot
    + labs(x="Orbital Phase", y="Relative Flux", title="lightcurve-transit · plotnine · pyplots.ai")
    + scale_y_continuous(labels=lambda lst: [f"{v:.3f}" for v in lst])
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#cccccc", alpha=0.3, size=0.5),
        plot_background=element_blank(),
        panel_background=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
