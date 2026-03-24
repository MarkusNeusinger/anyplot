""" pyplots.ai
spirometry-flow-volume: Spirometry Flow-Volume Loop
Library: plotly 6.6.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-18
"""

import numpy as np
import plotly.graph_objects as go


# Data - Spirometry flow-volume loop for a patient with mild obstruction
np.random.seed(42)

# Measured values
fvc = 4.2  # Forced Vital Capacity (L)
pef = 8.5  # Peak Expiratory Flow (L/s)
fev1 = 3.1  # FEV1 (L)

# Predicted normal values
fvc_pred = 4.8
pef_pred = 10.2

# Expiratory limb: sharp rise to PEF then roughly linear decline
n_points = 150
volume_exp = np.linspace(0, fvc, n_points)
t_exp = volume_exp / fvc
flow_exp = pef * (1 - t_exp) ** 0.35 * (1 - np.exp(-30 * t_exp))
flow_exp = np.maximum(flow_exp, 0)

# Inspiratory limb: symmetric U-shape below zero line
volume_insp = np.linspace(fvc, 0, n_points)
t_insp = np.linspace(0, 1, n_points)
pif = -5.5  # Peak Inspiratory Flow
flow_insp = pif * np.sin(np.pi * t_insp)

# Predicted normal expiratory limb
volume_pred_exp = np.linspace(0, fvc_pred, n_points)
t_pred_exp = volume_pred_exp / fvc_pred
flow_pred_exp = pef_pred * (1 - t_pred_exp) ** 0.3 * (1 - np.exp(-35 * t_pred_exp))
flow_pred_exp = np.maximum(flow_pred_exp, 0)

# Predicted normal inspiratory limb
volume_pred_insp = np.linspace(fvc_pred, 0, n_points)
t_pred_insp = np.linspace(0, 1, n_points)
pif_pred = -6.5
flow_pred_insp = pif_pred * np.sin(np.pi * t_pred_insp)

# Combine into closed loops
volume_measured = np.concatenate([volume_exp, volume_insp])
flow_measured = np.concatenate([flow_exp, flow_insp])

volume_predicted = np.concatenate([volume_pred_exp, volume_pred_insp])
flow_predicted = np.concatenate([flow_pred_exp, flow_pred_insp])

# Find PEF point on measured curve
pef_idx = np.argmax(flow_exp)
pef_volume = volume_exp[pef_idx]

# FEV1 volume marker (volume at 1 second ~ first ~74% of FVC for this patient)
fev1_volume = fev1  # approximate volume where FEV1 is reached

# Plot
fig = go.Figure()

# Shaded area between predicted and measured expiratory curves to highlight deficit
# Use a common volume range for the fill
vol_common = np.linspace(0, min(fvc, fvc_pred), 120)
flow_pred_interp = np.interp(vol_common, volume_pred_exp, flow_pred_exp)
flow_meas_interp = np.interp(vol_common, volume_exp, flow_exp)

fig.add_trace(
    go.Scatter(
        x=np.concatenate([vol_common, vol_common[::-1]]),
        y=np.concatenate([flow_pred_interp, flow_meas_interp[::-1]]),
        fill="toself",
        fillcolor="rgba(231, 76, 60, 0.08)",
        line={"width": 0},
        name="Flow Deficit",
        showlegend=True,
        hoverinfo="skip",
        legendrank=3,
    )
)

# Predicted normal loop (dashed, behind measured)
fig.add_trace(
    go.Scatter(
        x=volume_predicted,
        y=flow_predicted,
        mode="lines",
        line={"color": "#90A4AE", "width": 2.5, "dash": "dot"},
        name="Predicted Normal",
        hovertemplate="<b>Predicted</b><br>Volume: %{x:.2f} L<br>Flow: %{y:.2f} L/s<extra></extra>",
        legendrank=2,
    )
)

# Measured loop (solid, with gradient-like effect using color)
fig.add_trace(
    go.Scatter(
        x=volume_measured,
        y=flow_measured,
        mode="lines",
        line={"color": "#1B4F72", "width": 4, "shape": "spline"},
        name="Measured",
        hovertemplate="<b>Measured</b><br>Volume: %{x:.2f} L<br>Flow: %{y:.2f} L/s<extra></extra>",
        legendrank=1,
    )
)

# PEF marker with custom symbol
fig.add_trace(
    go.Scatter(
        x=[pef_volume],
        y=[pef],
        mode="markers",
        marker={"size": 18, "color": "#E74C3C", "symbol": "diamond", "line": {"width": 2.5, "color": "white"}},
        name="PEF",
        showlegend=False,
        hovertemplate="<b>Peak Expiratory Flow</b><br>%{y:.1f} L/s at %{x:.2f} L<extra></extra>",
    )
)

# PEF annotation with arrow
fig.add_annotation(
    x=pef_volume,
    y=pef,
    text=f"<b>PEF = {pef:.1f} L/s</b>",
    showarrow=True,
    arrowhead=0,
    arrowwidth=2,
    arrowcolor="#C0392B",
    ax=60,
    ay=-40,
    font={"size": 17, "color": "#C0392B", "family": "Arial"},
    bgcolor="rgba(255,255,255,0.85)",
    bordercolor="#C0392B",
    borderwidth=1.5,
    borderpad=6,
)

# FEV1 vertical reference line
fig.add_shape(
    type="line",
    x0=fev1_volume,
    x1=fev1_volume,
    y0=-1,
    y1=np.interp(fev1_volume, volume_exp, flow_exp),
    line={"color": "rgba(27, 79, 114, 0.35)", "width": 1.5, "dash": "dashdot"},
)

fig.add_annotation(
    x=fev1_volume,
    y=-1.2,
    text=f"FEV₁ = {fev1:.1f} L",
    showarrow=False,
    font={"size": 15, "color": "#1B4F72", "family": "Arial"},
    bgcolor="rgba(255,255,255,0.8)",
    borderpad=4,
)

# Clinical values annotation box with styled header
clinical_text = (
    f'<span style="color:#1B4F72"><b>Spirometry Results</b></span><br>'
    f'<span style="color:#555">━━━━━━━━━━━━━━━━━━━</span><br>'
    f"FEV₁: <b>{fev1:.1f} L</b><br>"
    f"FVC: <b>{fvc:.1f} L</b><br>"
    f"FEV₁/FVC: <b>{fev1 / fvc:.0%}</b><br>"
    f"PEF: <b>{pef:.1f} L/s</b>"
)
fig.add_annotation(
    x=0.98,
    y=0.95,
    xref="paper",
    yref="paper",
    text=clinical_text,
    showarrow=False,
    font={"size": 17, "family": "Arial"},
    align="left",
    bordercolor="#1B4F72",
    borderwidth=2,
    borderpad=14,
    bgcolor="rgba(248, 249, 250, 0.95)",
    xanchor="right",
    yanchor="top",
)

# Zero flow reference line
fig.add_hline(y=0, line={"color": "rgba(0,0,0,0.2)", "width": 1, "dash": "solid"})

# Layout with refined styling
fig.update_layout(
    title={
        "text": "spirometry-flow-volume · plotly · pyplots.ai",
        "font": {"size": 28, "family": "Arial", "color": "#2C3E50"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.96,
    },
    xaxis={
        "title": {"text": "Volume (L)", "font": {"size": 22, "family": "Arial", "color": "#2C3E50"}, "standoff": 15},
        "tickfont": {"size": 18, "family": "Arial", "color": "#555"},
        "showgrid": False,
        "zeroline": False,
        "range": [-0.3, max(fvc, fvc_pred) + 0.6],
        "linecolor": "#BDC3C7",
        "linewidth": 1.5,
        "mirror": False,
        "ticks": "outside",
        "ticklen": 6,
        "tickcolor": "#BDC3C7",
        "dtick": 1,
    },
    yaxis={
        "title": {"text": "Flow (L/s)", "font": {"size": 22, "family": "Arial", "color": "#2C3E50"}, "standoff": 15},
        "tickfont": {"size": 18, "family": "Arial", "color": "#555"},
        "showgrid": True,
        "gridcolor": "rgba(189, 195, 199, 0.3)",
        "griddash": "dot",
        "gridwidth": 1,
        "zeroline": False,
        "linecolor": "#BDC3C7",
        "linewidth": 1.5,
        "mirror": False,
        "ticks": "outside",
        "ticklen": 6,
        "tickcolor": "#BDC3C7",
        "dtick": 2,
    },
    template="plotly_white",
    legend={
        "font": {"size": 16, "family": "Arial"},
        "x": 0.02,
        "y": 0.02,
        "xanchor": "left",
        "yanchor": "bottom",
        "bgcolor": "rgba(248, 249, 250, 0.9)",
        "bordercolor": "#BDC3C7",
        "borderwidth": 1,
        "itemsizing": "constant",
        "tracegroupgap": 4,
    },
    margin={"l": 100, "r": 80, "t": 100, "b": 100},
    plot_bgcolor="white",
    paper_bgcolor="white",
    hoverlabel={
        "bgcolor": "white",
        "bordercolor": "#1B4F72",
        "font": {"size": 15, "family": "Arial", "color": "#2C3E50"},
    },
    hovermode="closest",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
