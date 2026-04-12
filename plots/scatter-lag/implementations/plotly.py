""" pyplots.ai
scatter-lag: Lag Plot for Time Series Autocorrelation Diagnosis
Library: plotly 6.7.0 | Python 3.14.3
Quality: 89/100 | Created: 2026-04-12
"""

import numpy as np
import plotly.graph_objects as go


# Data - synthetic AR(1) temperature process with strong autocorrelation
np.random.seed(42)
n_points = 500
phi = 0.85
noise = np.random.normal(0, 1, n_points)
temperature = np.zeros(n_points)
temperature[0] = 20.0
for i in range(1, n_points):
    temperature[i] = phi * temperature[i - 1] + (1 - phi) * 20.0 + noise[i]

lag = 1
y_t = temperature[:-lag]
y_t_lag = temperature[lag:]
time_index = np.arange(len(y_t))

# Correlation coefficient
correlation = np.corrcoef(y_t, y_t_lag)[0, 1]

# Regression line through the data
slope, intercept = np.polyfit(y_t, y_t_lag, 1)
x_fit = np.array([y_t.min(), y_t.max()])
y_fit = slope * x_fit + intercept

# Plot
fig = go.Figure()

# Scatter points with Plasma for stronger visual contrast
fig.add_trace(
    go.Scatter(
        x=y_t,
        y=y_t_lag,
        mode="markers",
        marker={
            "size": 7,
            "color": time_index,
            "colorscale": "Plasma",
            "colorbar": {
                "title": {"text": "Time Index", "font": {"size": 18, "color": "#444444"}},
                "tickfont": {"size": 16, "color": "#666666"},
                "thickness": 18,
                "len": 0.65,
                "outlinewidth": 0,
                "y": 0.5,
            },
            "opacity": 0.55,
            "line": {"width": 0.3, "color": "rgba(255,255,255,0.6)"},
        },
        hovertemplate=(
            "<b>Time %{customdata}</b><br>Temp at t: %{x:.1f} °C<br>Temp at t+1: %{y:.1f} °C<extra></extra>"
        ),
        customdata=time_index,
    )
)

# Diagonal reference line (y = x)
data_min = min(y_t.min(), y_t_lag.min())
data_max = max(y_t.max(), y_t_lag.max())
padding = (data_max - data_min) * 0.05
line_min = data_min - padding
line_max = data_max + padding

fig.add_trace(
    go.Scatter(
        x=[line_min, line_max],
        y=[line_min, line_max],
        mode="lines",
        line={"color": "rgba(0,0,0,0.15)", "width": 1.5, "dash": "dot"},
        showlegend=False,
        hoverinfo="skip",
        name="y = x",
    )
)

# Regression trend line
fig.add_trace(
    go.Scatter(
        x=x_fit,
        y=y_fit,
        mode="lines",
        line={"color": "#306998", "width": 2.5},
        showlegend=False,
        hoverinfo="skip",
        name="trend",
    )
)

# Layout with custom background and removed axis borders
fig.update_layout(
    title={
        "text": "scatter-lag · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#333333"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.96,
    },
    xaxis={
        "title": {"text": "Temperature (°C) at time t", "font": {"size": 22, "color": "#444444"}},
        "tickfont": {"size": 18, "color": "#666666"},
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.06)",
        "gridwidth": 1,
        "zeroline": False,
        "showline": False,
        "ticks": "",
    },
    yaxis={
        "title": {"text": f"Temperature (°C) at time t+{lag}", "font": {"size": 22, "color": "#444444"}},
        "tickfont": {"size": 18, "color": "#666666"},
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.06)",
        "gridwidth": 1,
        "zeroline": False,
        "showline": False,
        "ticks": "",
    },
    template="plotly_white",
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#F8F9FA",
    showlegend=False,
    margin={"l": 90, "r": 130, "t": 100, "b": 90},
)

# Subtitle annotation for context
fig.add_annotation(
    text="AR(1) process  |  lag = 1  |  500 observations",
    xref="paper",
    yref="paper",
    x=0.5,
    y=1.06,
    showarrow=False,
    font={"size": 16, "color": "#999999"},
    xanchor="center",
)

# Correlation annotation - prominent and well-styled
fig.add_annotation(
    text=f"<b>r = {correlation:.3f}</b>",
    xref="paper",
    yref="paper",
    x=0.03,
    y=0.97,
    showarrow=False,
    font={"size": 24, "color": "#306998"},
    bgcolor="rgba(255,255,255,0.9)",
    bordercolor="rgba(48,105,152,0.3)",
    borderwidth=1.5,
    borderpad=10,
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
