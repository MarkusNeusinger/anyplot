""" pyplots.ai
spirometry-flow-volume: Spirometry Flow-Volume Loop
Library: plotly 6.6.0 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-18
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
# Model: rapid rise then linear-ish decay
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

# Plot
fig = go.Figure()

# Predicted normal loop (dashed, behind measured)
fig.add_trace(
    go.Scatter(
        x=volume_predicted,
        y=flow_predicted,
        mode="lines",
        line={"color": "#B0BEC5", "width": 3, "dash": "dash"},
        name="Predicted Normal",
        hovertemplate="Volume: %{x:.2f} L<br>Flow: %{y:.2f} L/s<extra>Predicted</extra>",
    )
)

# Measured loop (solid)
fig.add_trace(
    go.Scatter(
        x=volume_measured,
        y=flow_measured,
        mode="lines",
        line={"color": "#306998", "width": 4},
        name="Measured",
        hovertemplate="Volume: %{x:.2f} L<br>Flow: %{y:.2f} L/s<extra>Measured</extra>",
    )
)

# PEF marker
fig.add_trace(
    go.Scatter(
        x=[pef_volume],
        y=[pef],
        mode="markers+text",
        marker={"size": 16, "color": "#E74C3C", "line": {"width": 2, "color": "white"}},
        text=[f"PEF = {pef:.1f} L/s"],
        textposition="top right",
        textfont={"size": 18, "color": "#E74C3C"},
        name="PEF",
        showlegend=False,
        hovertemplate="PEF: %{y:.1f} L/s<br>Volume: %{x:.2f} L<extra></extra>",
    )
)

# Clinical values annotation box
clinical_text = (
    f"<b>Clinical Values</b><br>"
    f"FEV1: {fev1:.1f} L<br>"
    f"FVC: {fvc:.1f} L<br>"
    f"FEV1/FVC: {fev1 / fvc:.0%}<br>"
    f"PEF: {pef:.1f} L/s"
)
fig.add_annotation(
    x=0.98,
    y=0.98,
    xref="paper",
    yref="paper",
    text=clinical_text,
    showarrow=False,
    font={"size": 18},
    align="left",
    bordercolor="#306998",
    borderwidth=2,
    borderpad=12,
    bgcolor="rgba(255,255,255,0.9)",
    xanchor="right",
    yanchor="top",
)

# Zero flow reference line
fig.add_hline(y=0, line={"color": "rgba(0,0,0,0.3)", "width": 1.5})

# Layout
fig.update_layout(
    title={"text": "spirometry-flow-volume · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Volume (L)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "gridcolor": "rgba(0,0,0,0.08)",
        "showgrid": True,
        "zeroline": False,
        "range": [-0.2, max(fvc, fvc_pred) + 0.5],
    },
    yaxis={
        "title": {"text": "Flow (L/s)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "gridcolor": "rgba(0,0,0,0.08)",
        "showgrid": True,
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
    margin={"l": 100, "r": 80, "t": 100, "b": 100},
    plot_bgcolor="white",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
