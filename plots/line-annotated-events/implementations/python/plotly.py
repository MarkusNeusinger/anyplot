""" pyplots.ai
line-annotated-events: Annotated Line Plot with Event Markers
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data - Simulated stock price data with events
np.random.seed(42)

# Generate daily stock prices over a year
dates = pd.date_range("2024-01-01", periods=252, freq="B")  # Business days
returns = np.random.normal(0.0005, 0.015, len(dates))
prices = 100 * np.exp(np.cumsum(returns))

# Define significant events (earnings announcements, product launches)
events = [
    {"date": pd.Timestamp("2024-01-25"), "label": "Q4 Earnings"},
    {"date": pd.Timestamp("2024-03-15"), "label": "Product Launch"},
    {"date": pd.Timestamp("2024-04-24"), "label": "Q1 Earnings"},
    {"date": pd.Timestamp("2024-06-10"), "label": "Expansion Announced"},
    {"date": pd.Timestamp("2024-07-25"), "label": "Q2 Earnings"},
    {"date": pd.Timestamp("2024-09-20"), "label": "Partnership Deal"},
    {"date": pd.Timestamp("2024-10-24"), "label": "Q3 Earnings"},
]

# Create figure
fig = go.Figure()

# Add main price line
fig.add_trace(
    go.Scatter(
        x=dates,
        y=prices,
        mode="lines",
        name="Stock Price",
        line={"color": "#306998", "width": 4},
        hovertemplate="Date: %{x|%Y-%m-%d}<br>Price: $%{y:.2f}<extra></extra>",
    )
)

# Add vertical lines and markers for events with alternating heights
y_range = prices.max() - prices.min()
heights = [0.92, 0.82, 0.92, 0.82, 0.92, 0.82, 0.92]  # Alternating heights

for i, event in enumerate(events):
    event_date = event["date"]
    event_label = event["label"]
    y_position = prices.min() + y_range * heights[i]

    # Find the closest price at event date
    closest_idx = np.abs(dates - event_date).argmin()
    price_at_event = prices[closest_idx]

    # Add vertical dashed line
    fig.add_shape(
        type="line",
        x0=event_date,
        x1=event_date,
        y0=prices.min() - y_range * 0.02,
        y1=y_position - y_range * 0.02,
        line={"color": "#FFD43B", "width": 3, "dash": "dash"},
    )

    # Add marker at the event date on the price line
    fig.add_trace(
        go.Scatter(
            x=[event_date],
            y=[price_at_event],
            mode="markers",
            marker={"size": 18, "color": "#FFD43B", "symbol": "diamond", "line": {"color": "#306998", "width": 2}},
            showlegend=False,
            hovertemplate=f"{event_label}<br>Date: %{{x|%Y-%m-%d}}<br>Price: $%{{y:.2f}}<extra></extra>",
        )
    )

    # Add annotation label
    fig.add_annotation(
        x=event_date,
        y=y_position,
        text=event_label,
        showarrow=False,
        font={"size": 20, "color": "#333333"},
        bgcolor="rgba(255, 212, 59, 0.9)",
        bordercolor="#FFD43B",
        borderwidth=2,
        borderpad=8,
    )

# Update layout
fig.update_layout(
    title={"text": "line-annotated-events · plotly · pyplots.ai", "font": {"size": 40}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Date", "font": {"size": 36}},
        "tickfont": {"size": 28},
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
    },
    yaxis={
        "title": {"text": "Stock Price (USD)", "font": {"size": 36}},
        "tickfont": {"size": 28},
        "tickprefix": "$",
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
    },
    template="plotly_white",
    showlegend=True,
    legend={
        "x": 0.02,
        "y": 0.98,
        "font": {"size": 24},
        "bgcolor": "rgba(255,255,255,0.9)",
        "bordercolor": "rgba(0,0,0,0.2)",
        "borderwidth": 1,
    },
    margin={"l": 120, "r": 50, "t": 120, "b": 100},
    plot_bgcolor="white",
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs=True)
