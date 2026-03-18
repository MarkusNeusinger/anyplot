"""pyplots.ai
lightcurve-transit: Astronomical Light Curve
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-18
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_line,
    geom_linerange,
    geom_point,
    geom_ribbon,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    scale_x_continuous,
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

# Vectorized transit computation (no function — KISS)
dist = np.abs(phase - transit_center)
full_transit = dist < transit_half_dur - ingress_half
ingress = (dist >= transit_half_dur - ingress_half) & (dist < transit_half_dur + ingress_half)
r = np.clip(dist / transit_half_dur, 0, 1)
mu = np.sqrt(np.maximum(1 - r**2, 0))
limb = 1 - u1 * (1 - mu) - u2 * (1 - mu) ** 2
transit_model = np.ones(n_points)
transit_model[full_transit] = 1.0 - transit_depth * limb[full_transit]
frac = (transit_half_dur + ingress_half - dist[ingress]) / (2 * ingress_half)
frac = 3 * frac**2 - 2 * frac**3
transit_model[ingress] = 1.0 - transit_depth * limb[ingress] * frac

flux_err = np.random.uniform(0.0008, 0.0025, n_points)
flux = transit_model + np.random.normal(0, 1, n_points) * flux_err

# Fine model curve
phase_fine = np.linspace(0.0, 1.0, 2000)
dist_f = np.abs(phase_fine - transit_center)
full_f = dist_f < transit_half_dur - ingress_half
ing_f = (dist_f >= transit_half_dur - ingress_half) & (dist_f < transit_half_dur + ingress_half)
r_f = np.clip(dist_f / transit_half_dur, 0, 1)
mu_f = np.sqrt(np.maximum(1 - r_f**2, 0))
limb_f = 1 - u1 * (1 - mu_f) - u2 * (1 - mu_f) ** 2
model_fine = np.ones(2000)
model_fine[full_f] = 1.0 - transit_depth * limb_f[full_f]
frac_f = (transit_half_dur + ingress_half - dist_f[ing_f]) / (2 * ingress_half)
frac_f = 3 * frac_f**2 - 2 * frac_f**3
model_fine[ing_f] = 1.0 - transit_depth * limb_f[ing_f] * frac_f

# Uncertainty ribbon only near transit (purposeful, not noise)
model_upper = model_fine + 0.0012
model_lower = model_fine - 0.0012
near_transit = np.abs(phase_fine - transit_center) < transit_half_dur + ingress_half + 0.02

df_obs = pd.DataFrame({"phase": phase, "flux": flux, "flux_err": flux_err, "series": "Observations"})
df_model = pd.DataFrame({"phase": phase_fine, "flux": model_fine, "series": "Transit Model"})
df_ribbon = pd.DataFrame(
    {"phase": phase_fine[near_transit], "upper": model_upper[near_transit], "lower": model_lower[near_transit]}
)

# Transit depth annotation
min_model = model_fine.min()
depth_pct = (1.0 - min_model) * 100

# Plot
plot = (
    ggplot()
    + geom_hline(yintercept=1.0, color="#999999", size=0.4, linetype="dotted", alpha=0.5)
    + geom_ribbon(aes(x="phase", ymin="lower", ymax="upper"), data=df_ribbon, fill="#c46210", alpha=0.12)
    + geom_linerange(
        aes(x="phase", ymin="flux - flux_err", ymax="flux + flux_err"),
        data=df_obs,
        color="#8fb8de",
        alpha=0.35,
        size=0.3,
    )
    + geom_point(aes(x="phase", y="flux", color="series"), data=df_obs, alpha=0.55, size=2, stroke=0)
    + geom_line(aes(x="phase", y="flux", color="series"), data=df_model, size=1.8)
    + scale_color_manual(values={"Observations": "#306998", "Transit Model": "#c46210"})
    + guides(color=guide_legend(title=None))
    + annotate(
        "text",
        x=0.62,
        y=min_model - 0.001,
        label=f"Depth: {depth_pct:.2f}%",
        size=14,
        color="#5a3e1b",
        fontstyle="italic",
    )
    + annotate(
        "segment", x=0.54, xend=0.54, y=1.0, yend=min_model, color="#5a3e1b", size=0.5, linetype="dashed", alpha=0.6
    )
    + annotate("text", x=0.08, y=1.0005, label="Baseline", size=10, color="#999999", fontstyle="italic")
)

# Style
plot = (
    plot
    + labs(x="Orbital Phase", y="Relative Flux", title="lightcurve-transit · plotnine · pyplots.ai")
    + scale_x_continuous(breaks=np.arange(0, 1.1, 0.1))
    + scale_y_continuous(labels=lambda lst: [f"{v:.3f}" for v in lst])
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", margin={"b": 15}),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_text=element_text(size=16),
        legend_title=element_blank(),
        legend_position=(0.85, 0.95),
        legend_background=element_blank(),
        legend_key=element_rect(fill="white", color="none"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#cccccc", alpha=0.25, size=0.4),
        plot_background=element_blank(),
        panel_background=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
