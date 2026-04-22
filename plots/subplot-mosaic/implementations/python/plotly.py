""" pyplots.ai
subplot-mosaic: Mosaic Subplot Layout with Varying Sizes
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Data
np.random.seed(42)

# Time series data for the wide overview chart (A - spans top row)
dates = pd.date_range("2024-01-01", periods=120, freq="D")
revenue = 50000 + np.cumsum(np.random.randn(120) * 1000) + np.arange(120) * 200
revenue = np.maximum(revenue, 30000)

# Monthly breakdown for bar chart (B - top right)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
monthly_sales = [42000, 48000, 51000, 46000, 58000, 62000]

# Scatter data for distribution view (C - middle left)
product_x = np.random.randn(80) * 15 + 50
product_y = product_x * 0.7 + np.random.randn(80) * 10 + 20

# Category comparison (D - middle right)
categories = ["Electronics", "Clothing", "Food", "Books", "Sports"]
cat_values = [35, 28, 22, 15, 18]

# Metric panel data (E, F, G - bottom row)
metric_1_history = np.random.rand(30) * 20 + 80
metric_2_history = np.random.rand(30) * 15 + 60
metric_3_history = np.random.rand(30) * 25 + 45

# Create mosaic layout: "AAB;CCD;EFG"
# Row 1: A spans 2 cols, B takes 1 col
# Row 2: C spans 2 cols, D takes 1 col
# Row 3: E, F, G each take 1 col

fig = make_subplots(
    rows=3,
    cols=3,
    specs=[[{"colspan": 2}, None, {}], [{"colspan": 2}, None, {}], [{}, {}, {}]],
    row_heights=[0.4, 0.35, 0.25],
    column_widths=[0.33, 0.33, 0.34],
    subplot_titles=[
        "Revenue Trend (Overview)",
        "Monthly Sales",
        "Product Performance",
        "Category Distribution",
        "Efficiency",
        "Quality Score",
        "Response Time",
    ],
    vertical_spacing=0.1,
    horizontal_spacing=0.08,
)

# A: Revenue trend line (top spanning)
fig.add_trace(
    go.Scatter(
        x=dates,
        y=revenue,
        mode="lines",
        line={"color": "#306998", "width": 3},
        fill="tozeroy",
        fillcolor="rgba(48, 105, 152, 0.2)",
        name="Revenue",
    ),
    row=1,
    col=1,
)

# B: Monthly sales bar (top right)
fig.add_trace(go.Bar(x=months, y=monthly_sales, marker_color="#FFD43B", name="Monthly"), row=1, col=3)

# C: Product scatter (middle spanning)
fig.add_trace(
    go.Scatter(
        x=product_x, y=product_y, mode="markers", marker={"size": 12, "color": "#306998", "opacity": 0.7}, name="Products"
    ),
    row=2,
    col=1,
)

# D: Category horizontal bar (middle right)
fig.add_trace(
    go.Bar(
        y=categories,
        x=cat_values,
        orientation="h",
        marker_color=["#306998", "#FFD43B", "#4B8BBE", "#646464", "#8B4513"],
        name="Categories",
    ),
    row=2,
    col=3,
)

# E: Efficiency metric (bottom left)
fig.add_trace(
    go.Scatter(
        x=list(range(30)),
        y=metric_1_history,
        mode="lines",
        line={"color": "#306998", "width": 2},
        fill="tozeroy",
        fillcolor="rgba(48, 105, 152, 0.3)",
        name="Efficiency",
    ),
    row=3,
    col=1,
)

# F: Quality score metric (bottom middle)
fig.add_trace(
    go.Scatter(
        x=list(range(30)),
        y=metric_2_history,
        mode="lines",
        line={"color": "#FFD43B", "width": 2},
        fill="tozeroy",
        fillcolor="rgba(255, 212, 59, 0.3)",
        name="Quality",
    ),
    row=3,
    col=2,
)

# G: Response time metric (bottom right)
fig.add_trace(
    go.Scatter(
        x=list(range(30)),
        y=metric_3_history,
        mode="lines",
        line={"color": "#4B8BBE", "width": 2},
        fill="tozeroy",
        fillcolor="rgba(75, 139, 190, 0.3)",
        name="Response",
    ),
    row=3,
    col=3,
)

# Update layout for large canvas
fig.update_layout(
    title={"text": "subplot-mosaic · plotly · pyplots.ai", "font": {"size": 32}, "x": 0.5, "xanchor": "center"},
    template="plotly_white",
    showlegend=False,
    margin={"l": 80, "r": 60, "t": 120, "b": 60},
)

# Update all axes for visibility
fig.update_xaxes(tickfont={"size": 14}, title_font={"size": 16})
fig.update_yaxes(tickfont={"size": 14}, title_font={"size": 16})

# Specific axis labels
fig.update_xaxes(title_text="Date", row=1, col=1)
fig.update_yaxes(title_text="Revenue ($)", row=1, col=1)
fig.update_xaxes(title_text="Month", row=1, col=3)
fig.update_yaxes(title_text="Sales ($)", row=1, col=3)
fig.update_xaxes(title_text="Feature X", row=2, col=1)
fig.update_yaxes(title_text="Feature Y", row=2, col=1)
fig.update_xaxes(title_text="Units Sold", row=2, col=3)
fig.update_xaxes(title_text="Days", row=3, col=1)
fig.update_yaxes(title_text="%", row=3, col=1)
fig.update_xaxes(title_text="Days", row=3, col=2)
fig.update_yaxes(title_text="Score", row=3, col=2)
fig.update_xaxes(title_text="Days", row=3, col=3)
fig.update_yaxes(title_text="ms", row=3, col=3)

# Update subplot titles font size
fig.update_annotations(font_size=18)

# Save as PNG
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
