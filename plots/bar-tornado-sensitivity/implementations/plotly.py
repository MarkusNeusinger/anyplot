"""pyplots.ai
bar-tornado-sensitivity: Tornado Diagram for Sensitivity Analysis
Library: plotly | Python 3.13
Quality: pending | Created: 2026-03-07
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

# Calculate bar positions relative to base
low_deltas = low_values - base_npv
high_deltas = high_values - base_npv

# Plot
fig = go.Figure()

fig.add_trace(
    go.Bar(
        y=parameters,
        x=low_deltas,
        base=base_npv,
        orientation="h",
        name="Low Scenario",
        marker={"color": "#306998"},
        text=[f"${v:.1f}M" for v in low_values],
        textposition="outside",
        textfont={"size": 16},
        cliponaxis=False,
    )
)

fig.add_trace(
    go.Bar(
        y=parameters,
        x=high_deltas,
        base=base_npv,
        orientation="h",
        name="High Scenario",
        marker={"color": "#E8833A"},
        text=[f"${v:.1f}M" for v in high_values],
        textposition="outside",
        textfont={"size": 16},
        cliponaxis=False,
    )
)

# Base case reference line
fig.add_vline(
    x=base_npv,
    line={"color": "#333333", "width": 2, "dash": "dash"},
    annotation={"text": f"Base Case: ${base_npv}M", "font": {"size": 18, "color": "#333333"}, "yshift": 10},
)

# Style
fig.update_layout(
    title={"text": "bar-tornado-sensitivity · plotly · pyplots.ai", "font": {"size": 28}},
    xaxis={
        "title": {"text": "Net Present Value ($M)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "tickprefix": "$",
        "ticksuffix": "M",
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.08)",
        "zeroline": False,
    },
    yaxis={"tickfont": {"size": 18}, "showgrid": False},
    template="plotly_white",
    barmode="overlay",
    bargap=0.3,
    legend={"font": {"size": 18}, "orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "center", "x": 0.5},
    margin={"l": 20, "r": 80, "t": 100, "b": 60},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
