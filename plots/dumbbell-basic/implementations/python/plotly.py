""" pyplots.ai
dumbbell-basic: Basic Dumbbell Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-23
"""

import plotly.graph_objects as go


# Data - Employee satisfaction scores before and after policy changes
categories = [
    "Engineering",
    "Sales",
    "Marketing",
    "Customer Support",
    "Finance",
    "Human Resources",
    "Operations",
    "Product",
]
before = [62, 71, 58, 45, 68, 52, 64, 73]  # Before policy changes
after = [78, 82, 75, 69, 74, 71, 79, 85]  # After policy changes

# Sort by difference (largest improvement at top of chart)
data = sorted(zip(categories, before, after, strict=True), key=lambda x: x[2] - x[1])
categories = [d[0] for d in data]
before = [d[1] for d in data]
after = [d[2] for d in data]

# Create figure
fig = go.Figure()

# Add connecting lines (one per category)
for i, cat in enumerate(categories):
    fig.add_trace(
        go.Scatter(
            x=[before[i], after[i]],
            y=[cat, cat],
            mode="lines",
            line={"color": "#999999", "width": 2},
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Add "Before" dots (Python Blue)
fig.add_trace(
    go.Scatter(
        x=before,
        y=categories,
        mode="markers",
        marker={"size": 18, "color": "#306998"},
        name="Before",
        hovertemplate="<b>%{y}</b><br>Before: %{x}<extra></extra>",
    )
)

# Add "After" dots (Python Yellow)
fig.add_trace(
    go.Scatter(
        x=after,
        y=categories,
        mode="markers",
        marker={"size": 18, "color": "#FFD43B"},
        name="After",
        hovertemplate="<b>%{y}</b><br>After: %{x}<extra></extra>",
    )
)

# Layout
fig.update_layout(
    title={
        "text": "Employee Satisfaction · dumbbell-basic · plotly · pyplots.ai",
        "font": {"size": 28},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Satisfaction Score", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "range": [35, 95],
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
    },
    yaxis={"title": {"text": "Department", "font": {"size": 22}}, "tickfont": {"size": 18}},
    template="plotly_white",
    legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "center", "x": 0.5, "font": {"size": 18}},
    margin={"l": 150, "r": 50, "t": 100, "b": 80},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
