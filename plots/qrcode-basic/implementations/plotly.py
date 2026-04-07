"""pyplots.ai
qrcode-basic: Basic QR Code Generator
Library: plotly 6.6.0 | Python 3.14.3
Quality: /100 | Updated: 2026-04-07
"""

import numpy as np
import plotly.graph_objects as go
import qrcode


# Data - Generate QR code for pyplots.ai
content = "https://pyplots.ai"

qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=1, border=4)
qr.add_data(content)
qr.make(fit=True)

# Convert QR matrix to numpy array (True=black module, False=white)
qr_matrix = np.array(qr.get_matrix(), dtype=int)

# Plot - Render as heatmap (1=black, 0=white)
fig = go.Figure(
    data=go.Heatmap(z=qr_matrix, colorscale=[[0, "#FFFFFF"], [1, "#000000"]], showscale=False, xgap=0, ygap=0)
)

# Style
fig.update_layout(
    title={
        "text": "qrcode-basic · plotly · pyplots.ai",
        "font": {"size": 32, "color": "#306998"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={"showticklabels": False, "showgrid": False, "zeroline": False, "scaleanchor": "y", "scaleratio": 1},
    yaxis={"showticklabels": False, "showgrid": False, "zeroline": False, "autorange": "reversed"},
    template="plotly_white",
    margin={"l": 80, "r": 80, "t": 160, "b": 240},
    paper_bgcolor="white",
    plot_bgcolor="white",
)

fig.add_annotation(
    text=f"Content: {content}",
    xref="paper",
    yref="paper",
    x=0.5,
    y=-0.04,
    showarrow=False,
    font={"size": 32, "color": "#666666"},
    xanchor="center",
    yanchor="top",
)
fig.add_annotation(
    text="Error Correction: M (15%)",
    xref="paper",
    yref="paper",
    x=0.5,
    y=-0.09,
    showarrow=False,
    font={"size": 28, "color": "#888888"},
    xanchor="center",
    yanchor="top",
)

# Save
fig.write_image("plot.png", width=3600, height=3600, scale=1)
fig.write_html("plot.html")
