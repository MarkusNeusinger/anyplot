""" pyplots.ai
subplot-grid: Subplot Grid Layout
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Data - Financial dashboard example
np.random.seed(42)

# Generate 60 days of stock data
days = 60
dates = pd.date_range("2024-01-01", periods=days, freq="D")

# Stock price with realistic walk
returns = np.random.normal(0.001, 0.02, days)
price = 100 * np.cumprod(1 + returns)

# Volume data (correlated with absolute price movement)
base_volume = 1000000
volume = base_volume + np.abs(returns) * 50000000 + np.random.normal(0, 200000, days)
volume = np.clip(volume, 500000, 3000000)

# Daily returns for histogram
daily_returns = np.diff(price) / price[:-1] * 100

# Moving averages
ma_20 = pd.Series(price).rolling(20).mean().values

# Create 2x2 subplot grid
fig = make_subplots(
    rows=2,
    cols=2,
    subplot_titles=("Stock Price & Moving Average", "Trading Volume", "Daily Returns Distribution", "Price vs Volume"),
    horizontal_spacing=0.1,
    vertical_spacing=0.12,
    specs=[[{"type": "scatter"}, {"type": "bar"}], [{"type": "histogram"}, {"type": "scatter"}]],
)

# Colors
python_blue = "#306998"
python_yellow = "#FFD43B"
accent_green = "#2E7D32"
accent_red = "#C62828"

# Subplot 1: Line chart - Stock price with moving average
fig.add_trace(
    go.Scatter(x=dates, y=price, mode="lines", name="Price", line={"color": python_blue, "width": 3}), row=1, col=1
)
fig.add_trace(
    go.Scatter(
        x=dates, y=ma_20, mode="lines", name="20-day MA", line={"color": python_yellow, "width": 2, "dash": "dash"}
    ),
    row=1,
    col=1,
)

# Subplot 2: Bar chart - Volume
volume_colors = [accent_green if r >= 0 else accent_red for r in returns]
fig.add_trace(go.Bar(x=dates, y=volume, name="Volume", marker={"color": volume_colors, "opacity": 0.7}), row=1, col=2)

# Subplot 3: Histogram - Daily returns distribution
fig.add_trace(
    go.Histogram(
        x=daily_returns,
        nbinsx=20,
        name="Returns",
        marker={"color": python_blue, "opacity": 0.7, "line": {"color": "white", "width": 1}},
    ),
    row=2,
    col=1,
)

# Subplot 4: Scatter - Price vs Volume relationship
fig.add_trace(
    go.Scatter(
        x=volume,
        y=price,
        mode="markers",
        name="Price-Volume",
        marker={"color": python_blue, "size": 10, "opacity": 0.6, "line": {"color": "white", "width": 1}},
    ),
    row=2,
    col=2,
)

# Update layout
fig.update_layout(
    title={"text": "subplot-grid \u00b7 plotly \u00b7 pyplots.ai", "font": {"size": 32}, "x": 0.5, "xanchor": "center"},
    showlegend=True,
    legend={"font": {"size": 16}, "x": 1.02, "y": 1, "xanchor": "left", "yanchor": "top"},
    template="plotly_white",
    margin={"l": 80, "r": 150, "t": 120, "b": 80},
)

# Update all axes fonts
fig.update_xaxes(tickfont={"size": 14}, title_font={"size": 18})
fig.update_yaxes(tickfont={"size": 14}, title_font={"size": 18})

# Specific axis labels
fig.update_xaxes(title_text="Date", row=1, col=1)
fig.update_yaxes(title_text="Price ($)", row=1, col=1)
fig.update_xaxes(title_text="Date", row=1, col=2)
fig.update_yaxes(title_text="Volume", row=1, col=2)
fig.update_xaxes(title_text="Daily Return (%)", row=2, col=1)
fig.update_yaxes(title_text="Frequency", row=2, col=1)
fig.update_xaxes(title_text="Volume", row=2, col=2)
fig.update_yaxes(title_text="Price ($)", row=2, col=2)

# Update subplot titles font size
for annotation in fig["layout"]["annotations"]:
    annotation["font"] = {"size": 20}

# Save as PNG (4800x2700 via scale=3)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html", include_plotlyjs=True)
