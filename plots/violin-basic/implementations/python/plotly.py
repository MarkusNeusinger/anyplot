""" pyplots.ai
violin-basic: Basic Violin Plot
Library: plotly 6.5.2 | Python 3.14.3
Quality: 90/100 | Updated: 2026-02-21
"""

import numpy as np
import plotly.graph_objects as go


# Data - 4 categories with distinct distribution shapes
np.random.seed(42)
data = {
    "Engineering": np.concatenate([np.random.normal(92000, 8000, 120), np.random.normal(75000, 5000, 80)]),
    "Marketing": np.random.normal(72000, 10000, 180),
    "Sales": np.random.normal(78000, 18000, 220),
    "Support": np.random.normal(55000, 8000, 190),
}

# Colors - 4 distinct, colorblind-safe colors starting with Python Blue
# Engineering highlighted with higher opacity to emphasize bimodal distribution
colors = ["#306998", "#E8873D", "#C44E52", "#6AAB73"]
opacities = [0.85, 0.6, 0.6, 0.6]

# Create figure
fig = go.Figure()

for i, (cat, values) in enumerate(data.items()):
    fig.add_trace(
        go.Violin(
            y=values,
            name=cat,
            line={"color": colors[i], "width": 2},
            fillcolor=colors[i],
            opacity=opacities[i],
            points=False,
            box={"visible": True, "width": 0.2, "fillcolor": "white", "line": {"color": "#333333", "width": 2}},
            meanline={"visible": True, "color": "#333333", "width": 2},
            hoveron="violins+kde",
            hoverinfo="y+name",
            scalemode="width",
        )
    )

# Annotation highlighting the bimodal Engineering distribution
fig.add_annotation(
    x="Engineering",
    y=100000,
    text="Bimodal: two salary<br>clusters at ~75k & ~92k",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.2,
    arrowwidth=2,
    arrowcolor="#306998",
    ax=120,
    ay=-50,
    font={"size": 15, "color": "#306998"},
    bordercolor="#306998",
    borderwidth=1.5,
    borderpad=6,
    bgcolor="rgba(255,255,255,0.85)",
)

# Layout
fig.update_layout(
    title={"text": "violin-basic \u00b7 plotly \u00b7 pyplots.ai", "font": {"size": 28}, "x": 0.5, "xanchor": "center"},
    xaxis={"title": {"text": "Department", "font": {"size": 22}}, "tickfont": {"size": 18}},
    yaxis={
        "title": {"text": "Annual Salary ($)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "tickformat": ",.0f",
        "tickprefix": "$",
        "gridcolor": "rgba(0,0,0,0.08)",
        "gridwidth": 1,
        "zeroline": False,
    },
    template="plotly_white",
    showlegend=False,
    margin={"l": 110, "r": 60, "t": 100, "b": 80},
    plot_bgcolor="rgba(0,0,0,0)",
)

# Update violin traces for visibility
fig.update_traces(width=0.7, spanmode="soft")

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
