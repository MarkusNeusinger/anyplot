"""pyplots.ai
lightcurve-transit: Astronomical Light Curve
Library: plotly 6.6.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-18
"""

import numpy as np
import plotly.graph_objects as go


# Data
np.random.seed(42)
n_points = 500
phase = np.sort(np.random.uniform(0.0, 1.0, n_points))

# Transit model parameters (quadratic limb darkening)
transit_center = 0.5
transit_duration = 0.06
transit_depth = 0.01
u1, u2 = 0.4, 0.2

# Compute model flux with limb-darkened transit shape
model_flux = np.ones_like(phase)
in_transit = np.abs(phase - transit_center) < transit_duration
z = np.abs(phase[in_transit] - transit_center) / transit_duration
mu = np.sqrt(1 - z**2)
limb_darkening = 1 - u1 * (1 - mu) - u2 * (1 - mu) ** 2
transit_profile = 1 - transit_depth * limb_darkening
model_flux[in_transit] = transit_profile

# Observed flux with noise
flux_err = np.random.uniform(0.0008, 0.0020, n_points)
flux = model_flux + np.random.normal(0, 1, n_points) * flux_err

# Sort model for smooth curve
phase_model_fine = np.linspace(0, 1, 2000)
model_fine = np.ones_like(phase_model_fine)
in_transit_fine = np.abs(phase_model_fine - transit_center) < transit_duration
z_fine = np.abs(phase_model_fine[in_transit_fine] - transit_center) / transit_duration
mu_fine = np.sqrt(1 - z_fine**2)
ld_fine = 1 - u1 * (1 - mu_fine) - u2 * (1 - mu_fine) ** 2
model_fine[in_transit_fine] = 1 - transit_depth * ld_fine

# Plot
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=phase,
        y=flux,
        mode="markers",
        name="Observations",
        marker={"size": 5, "color": "#306998", "opacity": 0.45, "line": {"width": 0.5, "color": "white"}},
        error_y={
            "type": "data",
            "array": flux_err,
            "visible": True,
            "color": "rgba(48, 105, 152, 0.20)",
            "thickness": 1.2,
            "width": 0,
        },
        hovertemplate="Phase: %{x:.4f}<br>Flux: %{y:.5f}<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=phase_model_fine,
        y=model_fine,
        mode="lines",
        name="Transit Model",
        line={"color": "#E67E22", "width": 3},
        hovertemplate="Phase: %{x:.4f}<br>Model: %{y:.5f}<extra></extra>",
    )
)

# Reference line at baseline flux
fig.add_hline(y=1.0, line_dash="dot", line_color="rgba(0,0,0,0.15)", line_width=1.5)

# Transit depth annotation
min_model = 1 - transit_depth
fig.add_annotation(
    x=transit_center + transit_duration + 0.025,
    y=(1.0 + min_model) / 2,
    text=f"Depth: {transit_depth * 100:.1f}%",
    showarrow=False,
    font={"size": 16, "color": "#555"},
    bgcolor="rgba(255,255,255,0.85)",
    borderpad=4,
)

# Bracket lines for transit depth
fig.add_shape(
    type="line",
    x0=transit_center + transit_duration + 0.015,
    x1=transit_center + transit_duration + 0.015,
    y0=1.0,
    y1=min_model,
    line={"color": "#888", "width": 1.2, "dash": "solid"},
)
fig.add_shape(
    type="line",
    x0=transit_center + transit_duration + 0.010,
    x1=transit_center + transit_duration + 0.020,
    y0=1.0,
    y1=1.0,
    line={"color": "#888", "width": 1.2},
)
fig.add_shape(
    type="line",
    x0=transit_center + transit_duration + 0.010,
    x1=transit_center + transit_duration + 0.020,
    y0=min_model,
    y1=min_model,
    line={"color": "#888", "width": 1.2},
)

# Style
fig.update_layout(
    title={
        "text": "Exoplanet Transit · lightcurve-transit · plotly · pyplots.ai",
        "font": {"size": 28},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Orbital Phase", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "showgrid": False,
        "showline": False,
        "zeroline": False,
        "range": [-0.02, 1.02],
    },
    yaxis={
        "title": {"text": "Relative Flux", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.08)",
        "gridwidth": 1,
        "showline": False,
        "zeroline": False,
    },
    template="plotly_white",
    legend={
        "font": {"size": 18},
        "x": 0.02,
        "y": 0.02,
        "xanchor": "left",
        "yanchor": "bottom",
        "bgcolor": "rgba(255,255,255,0.8)",
        "bordercolor": "rgba(0,0,0,0.1)",
        "borderwidth": 1,
    },
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin={"l": 80, "r": 40, "t": 80, "b": 80},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
