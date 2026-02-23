""" pyplots.ai
band-basic: Basic Band Plot
Library: plotly 6.5.2 | Python 3.14
Quality: 90/100 | Updated: 2026-02-23
"""

import numpy as np
import plotly.graph_objects as go


# Data
np.random.seed(42)
hours = np.linspace(0, 48, 100)
# Sensor temperature reading with slight oscillation
temperature = 20 + 0.15 * hours + 1.5 * np.sin(hours * 0.3)
# Measurement uncertainty grows over time (sensor drift)
uncertainty = 0.4 + 0.02 * hours
temp_lower = temperature - 1.96 * uncertainty
temp_upper = temperature + 1.96 * uncertainty

# Plot
fig = go.Figure()

# Band (fill between lower and upper bounds)
fig.add_trace(
    go.Scatter(
        x=np.concatenate([hours, hours[::-1]]),
        y=np.concatenate([temp_upper, temp_lower[::-1]]),
        fill="toself",
        fillcolor="rgba(48, 105, 152, 0.25)",
        line={"width": 0},
        hoverinfo="skip",
        showlegend=True,
        name="95% Confidence Interval",
    )
)

# Central trend line with custom hover showing confidence bounds
fig.add_trace(
    go.Scatter(
        x=hours,
        y=temperature,
        mode="lines",
        line={"color": "#306998", "width": 3},
        name="Measured Temperature",
        customdata=np.stack([temp_lower, temp_upper], axis=-1),
        hovertemplate=(
            "<b>Hour:</b> %{x:.1f} h<br>"
            "<b>Temp:</b> %{y:.1f} °C<br>"
            "<b>CI:</b> [%{customdata[0]:.1f}, %{customdata[1]:.1f}] °C"
            "<extra></extra>"
        ),
    )
)

# Layout
fig.update_layout(
    title={"text": "band-basic · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Elapsed Time (hours)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "gridcolor": "rgba(128, 128, 128, 0.2)",
        "gridwidth": 1,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Temperature (°C)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "gridcolor": "rgba(128, 128, 128, 0.2)",
        "gridwidth": 1,
        "zeroline": False,
    },
    legend={"font": {"size": 16}, "yanchor": "top", "y": 0.99, "xanchor": "left", "x": 0.01, "borderwidth": 0},
    template="plotly_white",
    margin={"l": 80, "r": 40, "t": 80, "b": 80},
    hoverlabel={"font": {"size": 14}},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
