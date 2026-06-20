"""anyplot.ai
lightcurve-transit: Astronomical Light Curve
Library: plotly | Python 3.13
Quality: 92/100 | Created: 2026-03-18
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens (Imprint palette — see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint categorical palette
BRAND = "#009E73"  # position 1 — observations (first series, always)
MODEL_COLOR = "#C475FD"  # position 2 — transit model

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

# Fine model curve for smooth overlay
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
        marker={"size": 8, "color": BRAND, "opacity": 0.55, "line": {"width": 0.5, "color": PAGE_BG}},
        error_y={
            "type": "data",
            "array": flux_err,
            "visible": True,
            "color": "rgba(0,158,115,0.35)",
            "thickness": 1.5,
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
        line={"color": MODEL_COLOR, "width": 3},
        hovertemplate="Phase: %{x:.4f}<br>Model: %{y:.5f}<extra></extra>",
    )
)

# Transit window highlight
fig.add_vrect(
    x0=transit_center - transit_duration,
    x1=transit_center + transit_duration,
    fillcolor="rgba(196,117,253,0.06)",
    line_width=0,
    annotation_text="Transit Window",
    annotation_position="top",
    annotation_font={"size": 13, "color": INK_MUTED},
)

# Baseline reference line
fig.add_hline(y=1.0, line_dash="dot", line_color=GRID, line_width=1.5)

# Transit depth annotation
min_model = 1 - transit_depth
fig.add_annotation(
    x=transit_center + transit_duration + 0.025,
    y=(1.0 + min_model) / 2,
    text=f"Depth: {transit_depth * 100:.1f}%",
    showarrow=False,
    font={"size": 16, "color": INK_SOFT},
    bgcolor=ELEVATED_BG,
    borderpad=4,
)

# Bracket lines for transit depth
bracket_x = transit_center + transit_duration + 0.015
fig.add_shape(type="line", x0=bracket_x, x1=bracket_x, y0=1.0, y1=min_model, line={"color": INK_SOFT, "width": 1.2})
fig.add_shape(
    type="line", x0=bracket_x - 0.005, x1=bracket_x + 0.005, y0=1.0, y1=1.0, line={"color": INK_SOFT, "width": 1.2}
)
fig.add_shape(
    type="line",
    x0=bracket_x - 0.005,
    x1=bracket_x + 0.005,
    y0=min_model,
    y1=min_model,
    line={"color": INK_SOFT, "width": 1.2},
)

# Ingress/egress contact markers
for label, xpos in [("T₁", transit_center - transit_duration), ("T₄", transit_center + transit_duration)]:
    fig.add_annotation(x=xpos, y=min_model - 0.0015, text=label, showarrow=False, font={"size": 14, "color": INK_MUTED})

# Title length 69 chars → ratio 67/69 ≈ 0.97 → rounds to 16px (at default floor)
title = "Exoplanet Transit · lightcurve-transit · python · plotly · anyplot.ai"

# Style
fig.update_layout(
    autosize=False,
    title={"text": title, "font": {"size": 16, "color": INK}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Orbital Phase", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": False,
        "showline": False,
        "zeroline": False,
        "range": [-0.02, 1.02],
        "linecolor": INK_SOFT,
        "spikemode": "across",
        "spikethickness": 1,
        "spikecolor": GRID,
        "spikedash": "dot",
    },
    yaxis={
        "title": {"text": "Relative Flux", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "showline": False,
        "zeroline": False,
        "linecolor": INK_SOFT,
        "spikemode": "across",
        "spikethickness": 1,
        "spikecolor": GRID,
        "spikedash": "dot",
    },
    hoverdistance=20,
    hovermode="closest",
    legend={
        "font": {"size": 10, "color": INK_SOFT},
        "x": 0.02,
        "y": 0.02,
        "xanchor": "left",
        "yanchor": "bottom",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
)

# Save — 3200×1800 landscape (width=800 × scale=4)
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn", config={"displayModeBar": True, "scrollZoom": True})
