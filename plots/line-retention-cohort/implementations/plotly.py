"""pyplots.ai
line-retention-cohort: User Retention Curve by Cohort
Library: plotly 6.6.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-16
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
colors = ["#306998", "#E6A817", "#2CA02C", "#D62728", "#9467BD"]
fill_opacities = [0.04, 0.05, 0.06, 0.08, 0.10]
fig = go.Figure()

for i, (cohort, retention) in enumerate(retention_data.items()):
    params = cohorts[cohort]
    line_width = 2 + i * 0.5
    opacity = 0.55 + i * 0.10

    # Fill area under curve for visual depth
    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=retention,
            mode="none",
            fill="tozeroy",
            fillcolor=f"rgba({int(colors[i][1:3], 16)},{int(colors[i][3:5], 16)},{int(colors[i][5:7], 16)},{fill_opacities[i]})",
            showlegend=False,
            hoverinfo="skip",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=retention,
            mode="lines+markers",
            name=f"{cohort} (n={params['size']:,})",
            line={"color": colors[i], "width": line_width},
            marker={"size": 8 + i, "color": colors[i]},
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
    annotation_font={"size": 14, "color": "#999999"},
)

# Annotation highlighting improving trend
last_week = weeks[-1]
oldest_val = retention_data["Jan 2025"][-1]
newest_val = retention_data["May 2025"][-1]
fig.add_annotation(
    x=last_week,
    y=(oldest_val + newest_val) / 2,
    text=f"+{newest_val - oldest_val:.0f}pp improvement",
    showarrow=True,
    arrowhead=2,
    arrowcolor="#2CA02C",
    ax=60,
    ay=0,
    font={"size": 15, "color": "#2CA02C", "weight": "bold"},
    bordercolor="#2CA02C",
    borderwidth=1,
    borderpad=4,
    bgcolor="rgba(44,160,44,0.08)",
)

# Style
fig.update_layout(
    title={"text": "line-retention-cohort · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Weeks Since Signup", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "dtick": 1,
        "showgrid": False,
        "showline": True,
        "linecolor": "#CCCCCC",
    },
    yaxis={
        "title": {"text": "Retained Users (%)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "range": [0, 105],
        "ticksuffix": "%",
        "dtick": 20,
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.08)",
        "gridwidth": 1,
        "showline": True,
        "linecolor": "#CCCCCC",
    },
    template="plotly_white",
    legend={"font": {"size": 16}, "borderwidth": 0, "yanchor": "top", "y": 0.95, "xanchor": "right", "x": 0.98},
    plot_bgcolor="white",
    width=1600,
    height=900,
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
)

# Save
fig.write_html("plot.html", include_plotlyjs="cdn")
fig.write_image("plot.png", width=1600, height=900, scale=3)
