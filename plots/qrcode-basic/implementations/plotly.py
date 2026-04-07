"""pyplots.ai
qrcode-basic: Basic QR Code Generator
Library: plotly 6.6.0 | Python 3.14.3
"""

import numpy as np
import plotly.graph_objects as go
import qrcode


# Data - Generate QR code for pyplots.ai
content = "https://pyplots.ai"

qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=1, border=4)
qr.add_data(content)
qr.make(fit=True)

qr_matrix = np.array(qr.get_matrix(), dtype=int)
n_modules = qr_matrix.shape[0]

# Plot - Render as heatmap with custom colorscale
fig = go.Figure(
    data=go.Heatmap(
        z=qr_matrix,
        colorscale=[[0, "#FFFFFF"], [1, "#1a1a2e"]],
        showscale=False,
        xgap=0.3,
        ygap=0.3,
        hovertemplate="Module: (%{x}, %{y})<br>Value: %{z}<extra></extra>",
    )
)

# Style - tighter layout for better canvas utilization
fig.update_layout(
    title={
        "text": "qrcode-basic · plotly · pyplots.ai",
        "font": {"size": 64, "color": "#306998", "family": "Arial Black, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
    },
    xaxis={
        "showticklabels": False,
        "showgrid": False,
        "zeroline": False,
        "scaleanchor": "y",
        "scaleratio": 1,
        "constrain": "domain",
        "showline": False,
        "range": [-0.5, n_modules - 0.5],
    },
    yaxis={
        "showticklabels": False,
        "showgrid": False,
        "zeroline": False,
        "autorange": "reversed",
        "constrain": "domain",
        "showline": False,
        "range": [-0.5, n_modules - 0.5],
    },
    template="plotly_white",
    margin={"l": 60, "r": 60, "t": 220, "b": 260},
    paper_bgcolor="#f8f9fa",
    plot_bgcolor="white",
)

# Decorative border around the QR code area
fig.add_shape(
    type="rect",
    xref="paper",
    yref="paper",
    x0=-0.01,
    y0=-0.01,
    x1=1.01,
    y1=1.01,
    line={"color": "#306998", "width": 1, "dash": "solid"},
    fillcolor="rgba(0,0,0,0)",
    opacity=0.3,
)

# Subtle divider line between QR code and annotations
fig.add_shape(
    type="line",
    xref="paper",
    yref="paper",
    x0=0.3,
    y0=-0.01,
    x1=0.7,
    y1=-0.01,
    line={"color": "#306998", "width": 1.5, "dash": "dot"},
)

# Content URL annotation - prominent, below plot area
fig.add_annotation(
    text=f"<b>{content}</b>",
    xref="paper",
    yref="paper",
    x=0.5,
    y=-0.025,
    showarrow=False,
    font={"size": 48, "color": "#306998", "family": "Arial, sans-serif"},
    xanchor="center",
    yanchor="top",
)

# Error correction and version info
fig.add_annotation(
    text=f"Error Correction: M (15%)  ·  Version {qr.version}  ·  {n_modules}×{n_modules} modules",
    xref="paper",
    yref="paper",
    x=0.5,
    y=-0.055,
    showarrow=False,
    font={"size": 38, "color": "#888888", "family": "Arial, sans-serif"},
    xanchor="center",
    yanchor="top",
)

# Save
fig.write_image("plot.png", width=3600, height=3600, scale=1)
fig.write_html("plot.html", include_plotlyjs="cdn")
