""" pyplots.ai
lightcurve-transit: Astronomical Light Curve
Library: altair 6.0.0 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-18
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - simulated exoplanet transit light curve (phase-folded)
np.random.seed(42)

n_points = 500
phase = np.sort(np.random.uniform(0.0, 1.0, n_points))

# Transit parameters
transit_center = 0.5
transit_width = 0.025
transit_depth = 0.01
limb_u1, limb_u2 = 0.4, 0.2
sharpness = 120

# Smooth transit model: tanh ingress/egress with quadratic limb darkening
dist = np.abs(phase - transit_center)
box = 0.5 * (np.tanh(sharpness * (transit_width - dist)) + 1.0)
mu = np.clip(1.0 - (dist / transit_width) ** 2, 0, 1)
limb = 1.0 - limb_u1 * (1 - mu) - limb_u2 * (1 - mu) ** 2
model_flux = 1.0 - transit_depth * box * limb

# Observed flux with Gaussian noise
flux_err = np.random.uniform(0.0008, 0.0018, n_points)
flux = model_flux + np.random.normal(0, 1, n_points) * flux_err

df_obs = pd.DataFrame(
    {"phase": phase, "flux": flux, "flux_err": flux_err, "flux_upper": flux + flux_err, "flux_lower": flux - flux_err}
)

# Dense model curve for smooth overlay
phase_model = np.linspace(0.0, 1.0, 2000)
dist_m = np.abs(phase_model - transit_center)
box_m = 0.5 * (np.tanh(sharpness * (transit_width - dist_m)) + 1.0)
mu_m = np.clip(1.0 - (dist_m / transit_width) ** 2, 0, 1)
limb_m = 1.0 - limb_u1 * (1 - mu_m) - limb_u2 * (1 - mu_m) ** 2
model_dense = 1.0 - transit_depth * box_m * limb_m

df_model = pd.DataFrame({"phase": phase_model, "flux": model_dense})

# Combined legend data
df_legend = pd.DataFrame(
    {
        "phase": [phase[0], phase_model[0]],
        "flux": [flux[0], model_dense[0]],
        "series": ["Observed Data", "Transit Model"],
    }
)

# Color palette - colorblind-safe teal + amber
color_obs = "#2A6B7C"
color_model = "#D4820E"
legend_scale = alt.Scale(domain=["Observed Data", "Transit Model"], range=[color_obs, color_model])

# Scales and axes
y_scale = alt.Scale(domain=[0.986, 1.006])
y_axis = alt.Axis(
    labelFontSize=18, titleFontSize=22, grid=True, gridOpacity=0.15, gridDash=[4, 4], format=".3f", tickCount=6
)
x_axis = alt.Axis(labelFontSize=18, titleFontSize=22, grid=True, gridOpacity=0.1, gridDash=[4, 4], tickCount=10)

# Error bars
error_bars = (
    alt.Chart(df_obs)
    .mark_rule(strokeWidth=1, opacity=0.2, color=color_obs)
    .encode(
        x=alt.X("phase:Q", title="Orbital Phase", axis=x_axis),
        y=alt.Y("flux_lower:Q", scale=y_scale),
        y2="flux_upper:Q",
    )
)

# Data points
points = (
    alt.Chart(df_obs)
    .mark_circle(size=30, opacity=0.5, stroke="white", strokeWidth=0.3)
    .encode(
        x=alt.X("phase:Q", title="Orbital Phase", axis=x_axis),
        y=alt.Y("flux:Q", title="Relative Flux", scale=y_scale, axis=y_axis),
        color=alt.value(color_obs),
        tooltip=[
            alt.Tooltip("phase:Q", title="Phase", format=".4f"),
            alt.Tooltip("flux:Q", title="Flux", format=".5f"),
            alt.Tooltip("flux_err:Q", title="Error", format=".5f"),
        ],
    )
)

# Transit model curve
model_line = (
    alt.Chart(df_model)
    .mark_line(strokeWidth=2.5, opacity=0.9)
    .encode(x=alt.X("phase:Q"), y=alt.Y("flux:Q", scale=y_scale), color=alt.value(color_model))
)

# Legend via invisible scatter with both series
legend_points = (
    alt.Chart(df_legend)
    .mark_point(size=0, filled=True, opacity=0)
    .encode(
        x=alt.X("phase:Q"),
        y=alt.Y("flux:Q", scale=y_scale),
        color=alt.Color(
            "series:N",
            scale=legend_scale,
            legend=alt.Legend(
                title=None,
                orient="top-right",
                labelFontSize=16,
                symbolSize=160,
                padding=14,
                cornerRadius=4,
                fillColor="rgba(255,255,255,0.9)",
                strokeColor="rgba(0,0,0,0.1)",
            ),
        ),
    )
)

# Nearest-point selection for interactive hover
nearest = alt.selection_point(nearest=True, on="pointerover", fields=["phase"], empty=False)

selectors = alt.Chart(df_obs).mark_point(size=1, opacity=0).encode(x="phase:Q", y="flux:Q").add_params(nearest)

hover_rule = (
    alt.Chart(df_obs)
    .mark_rule(color="#888888", strokeWidth=1, strokeDash=[3, 3])
    .encode(x="phase:Q")
    .transform_filter(nearest)
)

hover_point = (
    alt.Chart(df_obs)
    .mark_circle(size=120, color=color_obs, stroke=color_obs, strokeWidth=2, opacity=1)
    .encode(x="phase:Q", y="flux:Q")
    .transform_filter(nearest)
)

# Layer and configure
chart = (
    alt.layer(error_bars, points, model_line, legend_points, selectors, hover_rule, hover_point)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "Exoplanet Transit · lightcurve-transit · altair · pyplots.ai",
            fontSize=28,
            fontWeight="bold",
            subtitle="Phase-folded Kepler photometry with limb-darkened transit model",
            subtitleFontSize=18,
            subtitleColor="#666666",
            subtitlePadding=6,
            anchor="start",
            offset=12,
        ),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22)
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
