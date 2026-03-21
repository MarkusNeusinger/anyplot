""" pyplots.ai
titration-curve: Acid-Base Titration Curve
Library: plotly 6.6.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-21
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Data — 25 mL of 0.1 M HCl titrated with 0.1 M NaOH
c_acid = 0.1
v_acid = 25.0
c_base = 0.1
volume_ml = np.concatenate([np.linspace(0.0, 24.0, 80), np.linspace(24.0, 26.0, 30), np.linspace(26.0, 50.0, 50)])
volume_ml = np.unique(volume_ml)

ph = np.zeros_like(volume_ml)
for i, v in enumerate(volume_ml):
    total_vol = (v_acid + v) / 1000.0
    moles_acid = c_acid * v_acid / 1000.0
    moles_base = c_base * v / 1000.0
    diff = moles_acid - moles_base

    if diff > 1e-10:
        h_conc = diff / total_vol
        ph[i] = -np.log10(h_conc)
    elif diff < -1e-10:
        oh_conc = -diff / total_vol
        poh = -np.log10(oh_conc)
        ph[i] = 14.0 - poh
    else:
        ph[i] = 7.0

ph = np.clip(ph, 0, 14)

# Derivative (dpH/dV) using central differences
dph_dv = np.gradient(ph, volume_ml)

# Equivalence point — theoretical value for strong acid/strong base
eq_volume = 25.0
eq_ph = 7.0

# Buffer region — where pH changes slowly (flat part of the curve)
# For strong acid/base: the region before the steep transition where excess acid buffers
buffer_start = 5.0
buffer_end = 20.0
buffer_mask_pre = (volume_ml >= buffer_start) & (volume_ml <= buffer_end)

# Plot — dual y-axis
fig = make_subplots(specs=[[{"secondary_y": True}]])

# Buffer region shading via filled area
buffer_vols = volume_ml[buffer_mask_pre]
buffer_phs = ph[buffer_mask_pre]
if len(buffer_vols) > 0:
    fig.add_trace(
        go.Scatter(
            x=np.concatenate([buffer_vols, buffer_vols[::-1]]),
            y=np.concatenate([buffer_phs, np.full(len(buffer_phs), 0.0)]),
            fill="toself",
            fillcolor="rgba(48, 105, 152, 0.12)",
            line={"width": 0},
            name="Buffer Region",
            showlegend=True,
            hoverinfo="skip",
        ),
        secondary_y=False,
    )
    # Buffer region label centered in shaded area
    fig.add_annotation(
        x=(buffer_start + buffer_end) / 2,
        y=2.8,
        text="Buffer Region",
        showarrow=False,
        font={"size": 16, "color": "rgba(48, 105, 152, 0.8)", "family": "Arial"},
    )

# Main pH curve
fig.add_trace(
    go.Scatter(
        x=volume_ml,
        y=ph,
        mode="lines",
        name="pH",
        line={"color": "#306998", "width": 3.5},
        hovertemplate="Volume: %{x:.1f} mL<br>pH: %{y:.2f}<extra></extra>",
    ),
    secondary_y=False,
)

# Derivative curve
fig.add_trace(
    go.Scatter(
        x=volume_ml,
        y=dph_dv,
        mode="lines",
        name="dpH/dV",
        line={"color": "#E8873A", "width": 2.5, "dash": "dot"},
        hovertemplate="Volume: %{x:.1f} mL<br>dpH/dV: %{y:.2f}<extra></extra>",
    ),
    secondary_y=True,
)

# Equivalence point vertical line
fig.add_vline(x=eq_volume, line_dash="dash", line_color="rgba(120, 120, 120, 0.5)", line_width=1.5)

# Equivalence point marker
fig.add_trace(
    go.Scatter(
        x=[eq_volume],
        y=[eq_ph],
        mode="markers",
        name="Equivalence Point",
        marker={"size": 14, "color": "#D64545", "symbol": "diamond", "line": {"width": 2, "color": "white"}},
        showlegend=False,
        hovertemplate="Equivalence Point<br>%{x:.1f} mL, pH %{y:.1f}<extra></extra>",
    ),
    secondary_y=False,
)

# Equivalence point annotation — offset to avoid overlap with derivative spike
fig.add_annotation(
    x=eq_volume,
    y=eq_ph,
    text=f"Equivalence Point<br>{eq_volume:.1f} mL, pH {eq_ph:.1f}",
    showarrow=True,
    arrowhead=2,
    arrowsize=1,
    arrowwidth=1.5,
    arrowcolor="#666666",
    ax=90,
    ay=-70,
    font={"size": 16, "color": "#333333", "family": "Arial"},
    bgcolor="rgba(255, 255, 255, 0.85)",
    bordercolor="rgba(100, 100, 100, 0.3)",
    borderwidth=1,
    borderpad=6,
)

# Style
fig.update_layout(
    title={
        "text": "HCl + NaOH Titration · titration-curve · plotly · pyplots.ai",
        "font": {"size": 28, "family": "Arial", "color": "#2a2a2a"},
        "x": 0.5,
        "xanchor": "center",
    },
    template="plotly_white",
    legend={
        "font": {"size": 18, "family": "Arial"},
        "x": 0.02,
        "y": 0.98,
        "bgcolor": "rgba(255, 255, 255, 0.9)",
        "bordercolor": "rgba(200, 200, 200, 0.5)",
        "borderwidth": 1,
    },
    margin={"l": 80, "r": 90, "t": 100, "b": 80},
    plot_bgcolor="rgba(250, 250, 252, 1)",
    hovermode="x unified",
)

fig.update_xaxes(
    title={"text": "Volume of NaOH added (mL)", "font": {"size": 22, "family": "Arial"}},
    tickfont={"size": 18, "family": "Arial"},
    showgrid=False,
    showline=True,
    linewidth=1,
    linecolor="#CCCCCC",
    zeroline=False,
    ticks="outside",
    tickwidth=1,
    tickcolor="#CCCCCC",
    ticklen=5,
)

fig.update_yaxes(
    title={"text": "pH", "font": {"size": 22, "family": "Arial"}},
    tickfont={"size": 18, "family": "Arial"},
    range=[0, 14],
    showgrid=True,
    gridwidth=1,
    gridcolor="rgba(0, 0, 0, 0.06)",
    showline=True,
    linewidth=1,
    linecolor="#CCCCCC",
    zeroline=False,
    ticks="outside",
    tickwidth=1,
    tickcolor="#CCCCCC",
    ticklen=5,
    dtick=2,
    secondary_y=False,
)

fig.update_yaxes(
    title={"text": "dpH/dV (mL⁻¹)", "font": {"size": 22, "family": "Arial"}},
    tickfont={"size": 18, "family": "Arial"},
    showgrid=False,
    showline=True,
    linewidth=1,
    linecolor="#CCCCCC",
    zeroline=False,
    ticks="outside",
    tickwidth=1,
    tickcolor="#CCCCCC",
    ticklen=5,
    secondary_y=True,
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
