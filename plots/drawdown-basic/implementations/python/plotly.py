""" pyplots.ai
drawdown-basic: Drawdown Chart
Library: plotly 6.5.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data - Simulated stock price with realistic volatility
np.random.seed(42)
n_days = 500
dates = pd.date_range("2022-01-01", periods=n_days, freq="B")

# Generate realistic price path with trends and volatility
returns = np.random.normal(0.0003, 0.015, n_days)
returns[100:150] -= 0.008  # Simulate a market correction
returns[300:350] -= 0.012  # Simulate a larger drawdown period
price = 100 * np.cumprod(1 + returns)

# Calculate drawdown
running_max = np.maximum.accumulate(price)
drawdown = (price - running_max) / running_max * 100

# Find maximum drawdown
max_dd_idx = np.argmin(drawdown)
max_dd_value = drawdown[max_dd_idx]
max_dd_date = dates[max_dd_idx]

# Find recovery points (where drawdown returns to zero after being negative)
recovery_mask = (drawdown == 0) & (np.roll(drawdown, 1) < 0)
recovery_mask[0] = False
recovery_dates = dates[recovery_mask]

# Create figure with secondary y-axis
fig = go.Figure()

# Add drawdown fill area
fig.add_trace(
    go.Scatter(
        x=dates,
        y=drawdown,
        fill="tozeroy",
        fillcolor="rgba(220, 53, 69, 0.4)",
        line=dict(color="#dc3545", width=2),
        name="Drawdown",
        hovertemplate="Date: %{x|%Y-%m-%d}<br>Drawdown: %{y:.2f}%<extra></extra>",
    )
)

# Add zero baseline
fig.add_hline(y=0, line=dict(color="#333333", width=2, dash="solid"))

# Add maximum drawdown marker
fig.add_trace(
    go.Scatter(
        x=[max_dd_date],
        y=[max_dd_value],
        mode="markers+text",
        marker=dict(size=16, color="#dc3545", symbol="diamond"),
        text=[f"Max DD: {max_dd_value:.1f}%"],
        textposition="bottom center",
        textfont=dict(size=16, color="#dc3545"),
        name="Max Drawdown",
        showlegend=False,
        hovertemplate=f"Max Drawdown<br>Date: {max_dd_date.strftime('%Y-%m-%d')}<br>Drawdown: {max_dd_value:.2f}%<extra></extra>",
    )
)

# Add recovery point markers
if len(recovery_dates) > 0:
    fig.add_trace(
        go.Scatter(
            x=recovery_dates,
            y=[0] * len(recovery_dates),
            mode="markers",
            marker=dict(size=12, color="#28a745", symbol="triangle-up"),
            name="Recovery (New High)",
            hovertemplate="Recovery<br>Date: %{x|%Y-%m-%d}<extra></extra>",
        )
    )

# Calculate statistics for annotation
max_dd_duration = 0
current_duration = 0
for dd in drawdown:
    if dd < 0:
        current_duration += 1
        max_dd_duration = max(max_dd_duration, current_duration)
    else:
        current_duration = 0

stats_text = (
    f"<b>Drawdown Statistics</b><br>"
    f"Max Drawdown: {max_dd_value:.2f}%<br>"
    f"Max Duration: {max_dd_duration} days<br>"
    f"Recovery Points: {len(recovery_dates)}"
)

# Update layout
fig.update_layout(
    title=dict(
        text="drawdown-basic · plotly · pyplots.ai", font=dict(size=28, color="#333333"), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text="Date", font=dict(size=22)), tickfont=dict(size=18), showgrid=True, gridcolor="rgba(0,0,0,0.1)"
    ),
    yaxis=dict(
        title=dict(text="Drawdown (%)", font=dict(size=22)),
        tickfont=dict(size=18),
        ticksuffix="%",
        showgrid=True,
        gridcolor="rgba(0,0,0,0.1)",
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor="#333333",
    ),
    template="plotly_white",
    showlegend=True,
    legend=dict(font=dict(size=16), orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    margin=dict(l=80, r=200, t=100, b=80),
    annotations=[
        dict(
            text=stats_text,
            xref="paper",
            yref="paper",
            x=1.02,
            y=0.95,
            xanchor="left",
            yanchor="top",
            showarrow=False,
            font=dict(size=16),
            align="left",
            bordercolor="#333333",
            borderwidth=1,
            borderpad=10,
            bgcolor="rgba(255,255,255,0.9)",
        )
    ],
)

# Save as PNG
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs="cdn")
