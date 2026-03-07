"""pyplots.ai
bar-tornado-sensitivity: Tornado Diagram for Sensitivity Analysis
Library: plotly 6.6.0 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-07
"""

import numpy as np
import plotly.graph_objects as go


# Data - NPV sensitivity analysis for a capital investment project
parameters = [
    "Discount Rate",
    "Revenue Growth",
    "Initial Investment",
    "Operating Costs",
    "Tax Rate",
    "Terminal Value",
    "Working Capital",
    "Salvage Value",
]

base_npv = 12.5  # Base case NPV in $M

# Output NPV when each parameter is set to its low and high scenario
low_values = np.array([15.8, 9.1, 14.2, 14.8, 13.9, 10.4, 13.1, 12.0])
high_values = np.array([9.8, 16.3, 10.8, 10.5, 11.3, 14.8, 12.0, 13.1])

# Sort by total range (widest bar at top)
total_range = np.abs(high_values - low_values)
sort_idx = np.argsort(total_range)
parameters = [parameters[i] for i in sort_idx]
low_values = low_values[sort_idx]
high_values = high_values[sort_idx]
total_range = total_range[sort_idx]

# Calculate bar positions relative to base
low_deltas = low_values - base_npv
high_deltas = high_values - base_npv

# Color palette - gradient intensity by influence rank
n = len(parameters)
low_colors = [f"rgba(30, 80, 160, {0.35 + 0.65 * i / (n - 1):.2f})" for i in range(n)]
high_colors = [f"rgba(220, 120, 40, {0.35 + 0.65 * i / (n - 1):.2f})" for i in range(n)]

# Plot
fig = go.Figure()

fig.add_trace(
    go.Bar(
        y=parameters,
        x=low_deltas,
        base=base_npv,
        orientation="h",
        name="Low Scenario",
        marker={"color": low_colors, "line": {"width": 0}},
        text=[f"${v:.1f}M" for v in low_values],
        textposition="outside",
        textfont={"size": 16, "color": "#444"},
        cliponaxis=False,
        hovertemplate="%{y}<br>Low: %{text}<br>Change: %{x:+.1f}M<extra></extra>",
    )
)

fig.add_trace(
    go.Bar(
        y=parameters,
        x=high_deltas,
        base=base_npv,
        orientation="h",
        name="High Scenario",
        marker={"color": high_colors, "line": {"width": 0}},
        text=[f"${v:.1f}M" for v in high_values],
        textposition="outside",
        textfont={"size": 16, "color": "#444"},
        cliponaxis=False,
        hovertemplate="%{y}<br>High: %{text}<br>Change: %{x:+.1f}M<extra></extra>",
    )
)

# Base case reference line
fig.add_vline(x=base_npv, line={"color": "#666", "width": 1.5, "dash": "dot"})

# Base case annotation at the top
fig.add_annotation(
    x=base_npv,
    y=1.0,
    yref="paper",
    text=f"Base Case: <b>${base_npv}M</b>",
    showarrow=False,
    font={"size": 16, "color": "#555"},
    yshift=18,
    xanchor="center",
)

# Highlight the most influential parameter with a subtle bracket
top_range = total_range[-1]
fig.add_annotation(
    x=high_values[-1] + 0.3,
    y=parameters[-1],
    text=f"<b>▸ Largest Swing: ${top_range:.1f}M</b>",
    showarrow=False,
    xanchor="left",
    font={"size": 14, "color": "#c05020"},
    yshift=18,
)

# Style
fig.update_layout(
    title={
        "text": "bar-tornado-sensitivity · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#333", "family": "Arial Black, Arial"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.98,
    },
    xaxis={
        "title": {"text": "Net Present Value ($M)", "font": {"size": 22, "color": "#555"}, "standoff": 15},
        "tickfont": {"size": 18, "color": "#666"},
        "tickprefix": "$",
        "ticksuffix": "M",
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.05)",
        "gridwidth": 1,
        "zeroline": False,
        "side": "bottom",
    },
    yaxis={"tickfont": {"size": 18, "color": "#444"}, "showgrid": False, "automargin": True},
    template="plotly_white",
    barmode="overlay",
    bargap=0.25,
    legend={
        "font": {"size": 17, "color": "#555"},
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.08,
        "xanchor": "center",
        "x": 0.5,
        "bgcolor": "rgba(0,0,0,0)",
        "itemsizing": "constant",
    },
    margin={"l": 10, "r": 130, "t": 140, "b": 70},
    plot_bgcolor="rgba(250,250,252,1)",
    paper_bgcolor="white",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
