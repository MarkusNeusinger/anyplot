""" pyplots.ai
mosaic-categorical: Mosaic Plot for Categorical Association Analysis
Library: plotly 6.5.1 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data: Titanic-style survival data by class
np.random.seed(42)

data = {
    "Class": ["First", "First", "Second", "Second", "Third", "Third"],
    "Survival": ["Survived", "Did Not Survive", "Survived", "Did Not Survive", "Survived", "Did Not Survive"],
    "Count": [203, 122, 118, 167, 178, 528],
}
df = pd.DataFrame(data)

# Pivot to create contingency table
contingency = df.pivot(index="Survival", columns="Class", values="Count")
contingency = contingency[["First", "Second", "Third"]]  # Ensure order

# Reorder so "Did Not Survive" is at bottom, "Survived" at top
survival_order = ["Did Not Survive", "Survived"]
contingency = contingency.reindex(survival_order)

# Calculate proportions for mosaic plot
class_totals = contingency.sum(axis=0)
total = class_totals.sum()
class_widths = class_totals / total

survival_categories = contingency.index.tolist()
class_categories = contingency.columns.tolist()

# Colors for survival status (colorblind-safe)
colors = {
    "Survived": "#306998",  # Python Blue
    "Did Not Survive": "#FFD43B",  # Python Yellow
}

# Gap between rectangles
gap = 0.015

# Build shapes and annotations
shapes = []
annotations = []

x_start = 0
for _class_idx, class_name in enumerate(class_categories):
    width = class_widths[class_name] - gap
    class_total = contingency[class_name].sum()

    y_start = 0
    for _surv_idx, survival in enumerate(survival_categories):
        count = contingency.loc[survival, class_name]
        height = count / class_total

        # Create rectangle shape
        shapes.append(
            {
                "type": "rect",
                "x0": x_start,
                "y0": y_start,
                "x1": x_start + width,
                "y1": y_start + height,
                "fillcolor": colors[survival],
                "line": {"color": "white", "width": 2},
                "layer": "below",
            }
        )

        # Add count annotation in center of rectangle
        if height > 0.08:  # Only add label if rectangle is tall enough
            annotations.append(
                {
                    "x": x_start + width / 2,
                    "y": y_start + height / 2,
                    "text": f"<b>{count}</b>",
                    "showarrow": False,
                    "font": {"size": 20, "color": "white" if survival == "Survived" else "#333333"},
                    "xanchor": "center",
                    "yanchor": "middle",
                }
            )

        y_start += height

    # Add class label at bottom
    annotations.append(
        {
            "x": x_start + width / 2,
            "y": -0.08,
            "text": f"<b>{class_name}</b>",
            "showarrow": False,
            "font": {"size": 22, "color": "#333333"},
            "xanchor": "center",
            "yanchor": "top",
        }
    )

    x_start += width + gap

# Create figure with shapes
fig = go.Figure()

# Add invisible scatter for legend
fig.add_trace(
    go.Scatter(
        x=[None],
        y=[None],
        mode="markers",
        marker={"size": 20, "color": colors["Survived"]},
        name="Survived",
        showlegend=True,
    )
)
fig.add_trace(
    go.Scatter(
        x=[None],
        y=[None],
        mode="markers",
        marker={"size": 20, "color": colors["Did Not Survive"]},
        name="Did Not Survive",
        showlegend=True,
    )
)

fig.update_layout(
    title={
        "text": "mosaic-categorical · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#333333"},
        "x": 0.5,
        "xanchor": "center",
    },
    shapes=shapes,
    annotations=annotations,
    xaxis={
        "title": {"text": "Passenger Class", "font": {"size": 22}},
        "showgrid": False,
        "zeroline": False,
        "showticklabels": False,
        "range": [-0.15, 1.02],
    },
    yaxis={
        "title": {"text": "Proportion", "font": {"size": 22}},
        "showgrid": False,
        "zeroline": False,
        "tickfont": {"size": 18},
        "range": [-0.12, 1.02],
    },
    legend={
        "font": {"size": 18},
        "x": 1.02,
        "y": 0.5,
        "xanchor": "left",
        "yanchor": "middle",
        "bgcolor": "rgba(255,255,255,0.8)",
        "bordercolor": "#cccccc",
        "borderwidth": 1,
    },
    template="plotly_white",
    plot_bgcolor="white",
    margin={"l": 120, "r": 180, "t": 100, "b": 100},
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
