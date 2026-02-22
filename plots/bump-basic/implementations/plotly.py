"""pyplots.ai
bump-basic: Basic Bump Chart
Library: plotly 6.5.2 | Python 3.14.3
Quality: /100 | Updated: 2026-02-22
"""

import plotly.graph_objects as go


# Data - Formula 1 driver standings over a season
drivers = ["Verstappen", "Hamilton", "Norris", "Leclerc", "Piastri", "Sainz"]
races = ["Bahrain", "Jeddah", "Melbourne", "Suzuka", "Miami", "Imola", "Monaco", "Silverstone"]

rankings = {
    "Verstappen": [1, 1, 1, 1, 1, 2, 3, 2],
    "Hamilton": [4, 3, 4, 3, 3, 3, 1, 1],
    "Norris": [5, 5, 3, 4, 2, 1, 2, 3],
    "Leclerc": [2, 2, 2, 2, 4, 4, 4, 4],
    "Piastri": [3, 4, 5, 5, 5, 5, 5, 5],
    "Sainz": [6, 6, 6, 6, 6, 6, 6, 6],
}

# Colors - Python Blue first, then colorblind-safe palette
colors = {
    "Verstappen": "#306998",
    "Hamilton": "#e74c3c",
    "Norris": "#2ecc71",
    "Leclerc": "#f39c12",
    "Piastri": "#9b59b6",
    "Sainz": "#7f8c8d",
}

# Create figure
fig = go.Figure()

for driver in drivers:
    ranks = rankings[driver]
    color = colors[driver]
    fig.add_trace(
        go.Scatter(
            x=races,
            y=ranks,
            mode="lines+markers",
            name=driver,
            line={"width": 4, "color": color},
            marker={"size": 14, "color": color, "line": {"width": 2, "color": "white"}},
            showlegend=False,
        )
    )
    # End-of-line label
    fig.add_annotation(
        x=races[-1], y=ranks[-1], text=f"  {driver}", showarrow=False, xanchor="left", font={"size": 16, "color": color}
    )

# Layout with inverted Y-axis (rank 1 at top)
fig.update_layout(
    title={"text": "bump-basic · plotly · pyplots.ai", "font": {"size": 28}},
    xaxis={"title": {"text": "Race", "font": {"size": 22}}, "tickfont": {"size": 18}},
    yaxis={
        "title": {"text": "Championship Position", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "autorange": "reversed",
        "tickmode": "linear",
        "tick0": 1,
        "dtick": 1,
        "gridcolor": "rgba(0,0,0,0.08)",
        "showgrid": True,
    },
    xaxis_showgrid=False,
    template="plotly_white",
    margin={"r": 120},
)

# Save as PNG (4800x2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html")
