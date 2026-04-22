""" pyplots.ai
box-basic: Basic Box Plot
Library: plotly 6.5.2 | Python 3.14
Quality: 94/100 | Created: 2025-12-23
"""

import numpy as np
import plotly.graph_objects as go


# Data - salary distributions across departments
np.random.seed(42)
categories = ["Engineering", "Marketing", "Sales", "HR", "Finance"]
colors = ["#306998", "#E07B42", "#D4526E", "#8B6DAF", "#2D9B6E"]

data = {
    "Engineering": np.random.normal(95000, 15000, 100),
    "Marketing": np.random.normal(75000, 12000, 80),
    "Sales": np.random.normal(70000, 20000, 120),
    "HR": np.random.normal(65000, 10000, 60),
    "Finance": np.random.normal(85000, 14000, 90),
}

# Clip to realistic salary range
data = {k: np.clip(v, 25000, None) for k, v in data.items()}

# Compute medians for annotations
medians = {k: float(np.median(v)) for k, v in data.items()}
highest_dept = max(medians, key=medians.get)
lowest_dept = min(medians, key=medians.get)

# Plot
fig = go.Figure()

for i, (category, values) in enumerate(data.items()):
    fig.add_trace(
        go.Box(
            y=values,
            name=category,
            marker_color=colors[i],
            fillcolor=colors[i],
            opacity=0.85,
            boxpoints="outliers",
            marker={"size": 12, "opacity": 0.8, "line": {"width": 1, "color": "#444"}},
            line={"width": 2.5, "color": colors[i]},
            whiskerwidth=0.6,
            hovertemplate="<b>%{x}</b><br>Salary: $%{y:,.0f}<br><extra></extra>",
        )
    )

# Annotation: highlight highest-paid department median
fig.add_annotation(
    x=highest_dept,
    y=medians[highest_dept],
    text=f"Highest median<br><b>${medians[highest_dept]:,.0f}</b>",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.2,
    arrowwidth=2,
    arrowcolor="#306998",
    ax=60,
    ay=-50,
    font={"size": 17, "color": "#306998", "family": "Arial"},
    bordercolor="#306998",
    borderwidth=1.5,
    borderpad=6,
    bgcolor="rgba(255,255,255,0.9)",
)

# Annotation: highlight lowest-paid department median
fig.add_annotation(
    x=lowest_dept,
    y=medians[lowest_dept],
    text=f"Lowest median<br><b>${medians[lowest_dept]:,.0f}</b>",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.2,
    arrowwidth=2,
    arrowcolor="#D4526E",
    ax=-60,
    ay=50,
    font={"size": 17, "color": "#D4526E", "family": "Arial"},
    bordercolor="#D4526E",
    borderwidth=1.5,
    borderpad=6,
    bgcolor="rgba(255,255,255,0.9)",
)

# Annotation: salary gap insight
gap = medians[highest_dept] - medians[lowest_dept]
fig.add_annotation(
    x=0.98,
    y=0.98,
    xref="paper",
    yref="paper",
    text=f"Median salary gap: <b>${gap:,.0f}</b>",
    showarrow=False,
    font={"size": 18, "color": "#555", "family": "Arial"},
    bordercolor="#ccc",
    borderwidth=1,
    borderpad=8,
    bgcolor="rgba(245,245,245,0.95)",
    xanchor="right",
    yanchor="top",
)

# Layout
fig.update_layout(
    title={
        "text": "box-basic · plotly · pyplots.ai",
        "font": {"size": 32, "family": "Arial Black, Arial", "color": "#2a2a2a"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.96,
    },
    xaxis={
        "title": {"text": "Department", "font": {"size": 24, "color": "#444", "family": "Arial"}, "standoff": 15},
        "tickfont": {"size": 20, "color": "#333", "family": "Arial"},
        "showline": True,
        "linewidth": 1.5,
        "linecolor": "#bbb",
    },
    yaxis={
        "title": {
            "text": "Annual Salary ($)",
            "font": {"size": 24, "color": "#444", "family": "Arial"},
            "standoff": 10,
        },
        "tickfont": {"size": 20, "color": "#333", "family": "Arial"},
        "tickformat": "$,.0f",
        "gridcolor": "rgba(0,0,0,0.06)",
        "gridwidth": 1,
        "zeroline": False,
        "showline": True,
        "linewidth": 1.5,
        "linecolor": "#bbb",
        "range": [20000, 155000],
        "dtick": 20000,
    },
    template="plotly_white",
    showlegend=False,
    margin={"l": 120, "r": 60, "t": 90, "b": 80},
    plot_bgcolor="rgba(250,250,252,1)",
    paper_bgcolor="white",
    font={"family": "Arial"},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
