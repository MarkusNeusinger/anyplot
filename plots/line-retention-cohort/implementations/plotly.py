""" pyplots.ai
line-retention-cohort: User Retention Curve by Cohort
Library: plotly 6.6.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-16
"""

import numpy as np
import plotly.graph_objects as go


# Data
np.random.seed(42)

cohorts = {
    "Jan 2025": {"size": 1245, "decay": 0.18},
    "Feb 2025": {"size": 1102, "decay": 0.16},
    "Mar 2025": {"size": 1380, "decay": 0.14},
    "Apr 2025": {"size": 1510, "decay": 0.12},
    "May 2025": {"size": 1425, "decay": 0.10},
}

weeks = np.arange(0, 13)

retention_data = {}
for cohort, params in cohorts.items():
    base_retention = 100 * np.exp(-params["decay"] * weeks)
    noise = np.random.normal(0, 1.5, len(weeks))
    noise[0] = 0
    retention = np.clip(base_retention + noise, 0, 100)
    retention[0] = 100.0
    retention_data[cohort] = retention

# Plot
colors = ["#8DA0B5", "#7A9DBF", "#5B8DB8", "#3D7EAF", "#306998"]
fig = go.Figure()

for i, (cohort, retention) in enumerate(retention_data.items()):
    params = cohorts[cohort]
    line_width = 2 + i * 0.5
    opacity = 0.5 + i * 0.12

    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=retention,
            mode="lines+markers",
            name=f"{cohort} (n={params['size']:,})",
            line=dict(color=colors[i], width=line_width),
            marker=dict(size=8 + i, color=colors[i]),
            opacity=opacity,
        )
    )

# Reference line at 20% retention threshold
fig.add_hline(
    y=20,
    line_dash="dash",
    line_color="#999999",
    line_width=1.5,
    annotation_text="20% retention threshold",
    annotation_position="top left",
    annotation_font=dict(size=14, color="#999999"),
)

# Style
fig.update_layout(
    title=dict(text="line-retention-cohort · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Weeks Since Signup", font=dict(size=22)),
        tickfont=dict(size=18),
        dtick=1,
        showgrid=False,
        showline=True,
        linecolor="#CCCCCC",
    ),
    yaxis=dict(
        title=dict(text="Retained Users (%)", font=dict(size=22)),
        tickfont=dict(size=18),
        range=[0, 105],
        ticksuffix="%",
        dtick=20,
        showgrid=True,
        gridcolor="rgba(0,0,0,0.08)",
        gridwidth=1,
        showline=True,
        linecolor="#CCCCCC",
    ),
    template="plotly_white",
    legend=dict(font=dict(size=16), borderwidth=0, yanchor="top", y=0.95, xanchor="right", x=0.98),
    plot_bgcolor="white",
    width=1600,
    height=900,
    margin=dict(l=80, r=40, t=80, b=60),
)

# Save
fig.write_html("plot.html", include_plotlyjs="cdn")
fig.write_image("plot.png", width=1600, height=900, scale=3)
