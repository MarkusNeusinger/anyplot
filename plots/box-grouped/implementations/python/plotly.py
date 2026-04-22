""" pyplots.ai
box-grouped: Grouped Box Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import numpy as np
import plotly.graph_objects as go


# Data - Employee performance scores by department and experience level
np.random.seed(42)

categories = ["Sales", "Engineering", "Marketing", "Support"]
subcategories = ["Junior", "Mid-Level", "Senior"]

# Color palette following style guide
colors = ["#306998", "#FFD43B", "#4ECDC4"]

# Generate realistic performance data with varying distributions
data = {
    "Sales": {
        "Junior": np.random.normal(65, 12, 50),
        "Mid-Level": np.random.normal(75, 10, 50),
        "Senior": np.random.normal(85, 8, 50),
    },
    "Engineering": {
        "Junior": np.random.normal(60, 15, 50),
        "Mid-Level": np.random.normal(78, 9, 50),
        "Senior": np.random.normal(88, 6, 50),
    },
    "Marketing": {
        "Junior": np.random.normal(62, 14, 50),
        "Mid-Level": np.random.normal(72, 11, 50),
        "Senior": np.random.normal(82, 9, 50),
    },
    "Support": {
        "Junior": np.random.normal(58, 13, 50),
        "Mid-Level": np.random.normal(70, 10, 50),
        "Senior": np.random.normal(80, 7, 50),
    },
}

# Add some outliers for feature coverage
data["Sales"]["Junior"] = np.append(data["Sales"]["Junior"], [30, 95])
data["Engineering"]["Senior"] = np.append(data["Engineering"]["Senior"], [55, 100])
data["Marketing"]["Mid-Level"] = np.append(data["Marketing"]["Mid-Level"], [35, 98])

# Create figure
fig = go.Figure()

# Add box traces for each subcategory
for i, subcat in enumerate(subcategories):
    x_vals = []
    y_vals = []
    for cat in categories:
        values = data[cat][subcat]
        x_vals.extend([cat] * len(values))
        y_vals.extend(values)

    fig.add_trace(
        go.Box(
            x=x_vals,
            y=y_vals,
            name=subcat,
            marker_color=colors[i],
            boxmean=False,
            line={"width": 2},
            marker={"size": 8, "opacity": 0.7},
            boxpoints="outliers",
        )
    )

# Update layout for 4800x2700 resolution
fig.update_layout(
    title={"text": "box-grouped · plotly · pyplots.ai", "font": {"size": 32}, "x": 0.5, "xanchor": "center"},
    xaxis={"title": {"text": "Department", "font": {"size": 24}}, "tickfont": {"size": 20}},
    yaxis={
        "title": {"text": "Performance Score", "font": {"size": 24}},
        "tickfont": {"size": 20},
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
    },
    legend={
        "title": {"text": "Experience Level", "font": {"size": 20}},
        "font": {"size": 18},
        "x": 1.02,
        "y": 1,
        "xanchor": "left",
        "yanchor": "top",
    },
    boxmode="group",
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin={"l": 100, "r": 200, "t": 100, "b": 100},
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
