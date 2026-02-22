"""pyplots.ai
bump-basic: Basic Bump Chart
Library: plotly 6.5.2 | Python 3.14.3
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

# Colorblind-safe palette — Python Blue first, teal replaces green to avoid red-green issue
colors = {
    "Verstappen": "#306998",
    "Hamilton": "#e74c3c",
    "Norris": "#17becf",
    "Leclerc": "#f39c12",
    "Piastri": "#9b59b6",
    "Sainz": "#95a5a6",
}

# Visual hierarchy — emphasize dynamic storylines, mute static ones
rank_changes = {d: max(r) - min(r) for d, r in rankings.items()}
line_widths = {d: 5 if rank_changes[d] >= 3 else 3 if rank_changes[d] >= 2 else 2 for d in drivers}
marker_sizes = {d: 16 if rank_changes[d] >= 3 else 12 if rank_changes[d] >= 2 else 10 for d in drivers}
opacities = {d: 1.0 if rank_changes[d] >= 3 else 0.8 if rank_changes[d] >= 2 else 0.45 for d in drivers}

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
            line={"width": line_widths[driver], "color": color},
            marker={"size": marker_sizes[driver], "color": color, "line": {"width": 2, "color": "white"}},
            opacity=opacities[driver],
            showlegend=False,
            hovertemplate="<b>%{text}</b><br>%{x}: P%{y}<extra></extra>",
            text=[driver] * len(races),
        )
    )
    # End-of-line label
    fig.add_annotation(
        x=races[-1],
        y=ranks[-1],
        text=f"  <b>{driver}</b>" if rank_changes[driver] >= 3 else f"  {driver}",
        showarrow=False,
        xanchor="left",
        font={"size": 16, "color": color},
        opacity=opacities[driver],
    )

# Layout with inverted Y-axis (rank 1 at top)
fig.update_layout(
    title={"text": "bump-basic · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.02, "xanchor": "left"},
    xaxis={"title": {"text": "Race", "font": {"size": 22}}, "tickfont": {"size": 18}, "showgrid": False},
    yaxis={
        "title": {"text": "Championship Position", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "autorange": "reversed",
        "tickmode": "linear",
        "tick0": 1,
        "dtick": 1,
        "gridcolor": "rgba(0,0,0,0.06)",
        "gridwidth": 1,
        "showgrid": True,
        "zeroline": False,
    },
    template="plotly_white",
    margin={"r": 130, "t": 80, "l": 80, "b": 70},
    plot_bgcolor="rgba(0,0,0,0)",
    hoverlabel={"font_size": 16},
)

# Save as PNG (4800x2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html")
