""" pyplots.ai
dashboard-metrics-tiles: Real-Time Dashboard Tiles
Library: plotly 6.5.2 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-19
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Data - 6 metric tiles for a 3x2 dashboard layout
np.random.seed(42)

metrics = [
    {
        "name": "CPU Usage",
        "value": 45,
        "unit": "%",
        "history": 30 + np.cumsum(np.random.randn(30) * 2),
        "change": -5.2,
        "status": "good",
        "higher_is_bad": True,
    },
    {
        "name": "Memory",
        "value": 72,
        "unit": "%",
        "history": 60 + np.cumsum(np.random.randn(30) * 1.5),
        "change": 8.3,
        "status": "warning",
        "higher_is_bad": True,
    },
    {
        "name": "Response Time",
        "value": 120,
        "unit": "ms",
        "history": 100 + np.cumsum(np.random.randn(30) * 5),
        "change": -15.4,
        "status": "good",
        "higher_is_bad": True,
    },
    {
        "name": "Requests/sec",
        "value": 1250,
        "unit": "",
        "history": 1000 + np.cumsum(np.random.randn(30) * 50),
        "change": 12.7,
        "status": "good",
        "higher_is_bad": False,
    },
    {
        "name": "Error Rate",
        "value": 2.3,
        "unit": "%",
        "history": 1 + np.abs(np.cumsum(np.random.randn(30) * 0.3)),
        "change": 45.0,
        "status": "critical",
        "higher_is_bad": True,
    },
    {
        "name": "Disk I/O",
        "value": 85,
        "unit": "MB/s",
        "history": 70 + np.cumsum(np.random.randn(30) * 3),
        "change": -2.1,
        "status": "good",
        "higher_is_bad": False,
    },
]

# Normalize history for sparklines
for m in metrics:
    hist = np.array(m["history"])
    m["history_norm"] = (hist - hist.min()) / (hist.max() - hist.min() + 1e-6)

# Colors
status_colors = {"good": "#22c55e", "warning": "#f59e0b", "critical": "#ef4444"}
tile_bg = "#f8fafc"
text_color = "#1e293b"

# Grid layout: 3 columns x 2 rows
n_cols, n_rows = 3, 2

# Create subplots - use domain type for indicators (no axes)
fig = make_subplots(
    rows=n_rows,
    cols=n_cols,
    horizontal_spacing=0.08,
    vertical_spacing=0.12,
    specs=[[{"type": "indicator"} for _ in range(n_cols)] for _ in range(n_rows)],
)

# Add indicator tiles
for idx, metric in enumerate(metrics):
    row = idx // n_cols + 1
    col = idx % n_cols + 1

    # Determine delta color - for "higher is bad" metrics, decreasing is green
    if metric["higher_is_bad"]:
        delta_increasing_color = "#ef4444"  # Red when increasing
        delta_decreasing_color = "#22c55e"  # Green when decreasing
    else:
        delta_increasing_color = "#22c55e"  # Green when increasing
        delta_decreasing_color = "#ef4444"  # Red when decreasing

    # Format value text
    value_suffix = metric["unit"]

    fig.add_trace(
        go.Indicator(
            mode="number+delta",
            value=metric["value"],
            number=dict(font=dict(size=48, color=status_colors[metric["status"]]), suffix=value_suffix),
            delta=dict(
                reference=metric["value"] / (1 + metric["change"] / 100),
                relative=True,
                valueformat=".1%",
                font=dict(size=20),
                increasing=dict(color=delta_increasing_color, symbol="▲"),
                decreasing=dict(color=delta_decreasing_color, symbol="▼"),
            ),
            title=dict(text=metric["name"], font=dict(size=24, color=text_color)),
        ),
        row=row,
        col=col,
    )

# Add sparklines as scatter traces in background
# First, update layout to add regular axes for sparklines
for idx, metric in enumerate(metrics):
    row = idx // n_cols + 1
    col = idx % n_cols + 1

    # Get the domain for this subplot
    if row == 1:
        y_domain = [0.55, 0.95]
    else:
        y_domain = [0.05, 0.45]

    if col == 1:
        x_domain = [0.0, 0.28]
    elif col == 2:
        x_domain = [0.36, 0.64]
    else:
        x_domain = [0.72, 1.0]

    # Add a new axis for the sparkline
    axis_num = idx + 2  # Start from axis 2
    x_axis = f"x{axis_num}"
    y_axis = f"y{axis_num}"

    # Sparkline trace
    x_spark = list(range(len(metric["history_norm"])))
    y_spark = metric["history_norm"].tolist()

    fig.add_trace(
        go.Scatter(
            x=x_spark,
            y=y_spark,
            mode="lines",
            line=dict(color=status_colors[metric["status"]], width=2),
            fill="tozeroy",
            fillcolor=f"rgba{tuple([int(status_colors[metric['status']][i:i+2], 16) for i in (1, 3, 5)] + [0.15])}",
            showlegend=False,
            hoverinfo="skip",
            xaxis=x_axis,
            yaxis=y_axis,
        )
    )

    # Configure the axis
    sparkline_height = 0.12
    fig.update_layout(
        **{
            f"xaxis{axis_num}": dict(
                domain=[x_domain[0] + 0.02, x_domain[1] - 0.02],
                range=[0, len(x_spark) - 1],
                showticklabels=False,
                showgrid=False,
                zeroline=False,
                showline=False,
                anchor=y_axis,
            ),
            f"yaxis{axis_num}": dict(
                domain=[y_domain[0] - 0.02, y_domain[0] + sparkline_height],
                range=[-0.1, 1.1],
                showticklabels=False,
                showgrid=False,
                zeroline=False,
                showline=False,
                anchor=x_axis,
            ),
        }
    )

# Add tile backgrounds
for idx in range(len(metrics)):
    row = idx // n_cols + 1
    col = idx % n_cols + 1

    if row == 1:
        y_domain = [0.52, 1.0]
    else:
        y_domain = [0.0, 0.48]

    if col == 1:
        x_domain = [0.0, 0.30]
    elif col == 2:
        x_domain = [0.35, 0.65]
    else:
        x_domain = [0.70, 1.0]

    fig.add_shape(
        type="rect",
        xref="paper",
        yref="paper",
        x0=x_domain[0],
        y0=y_domain[0],
        x1=x_domain[1],
        y1=y_domain[1],
        fillcolor=tile_bg,
        line=dict(color="#e2e8f0", width=2),
        layer="below",
    )

# Add title as annotation to ensure proper positioning
fig.add_annotation(
    text="dashboard-metrics-tiles · plotly · pyplots.ai",
    x=0.5,
    y=1.08,
    xref="paper",
    yref="paper",
    showarrow=False,
    font=dict(size=28, color=text_color, family="Arial"),
    xanchor="center",
    yanchor="top",
)

# Update layout
fig.update_layout(paper_bgcolor="white", margin=dict(l=40, r=40, t=100, b=40), showlegend=False)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
