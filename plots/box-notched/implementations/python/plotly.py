""" pyplots.ai
box-notched: Notched Box Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-25
"""

import numpy as np
import plotly.graph_objects as go


# Data - Employee salary distributions across departments
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "HR", "Finance"]
salary_data = {
    "Engineering": np.random.normal(95000, 15000, 80),
    "Marketing": np.random.normal(72000, 12000, 65),
    "Sales": np.random.normal(68000, 18000, 90),  # Higher variance
    "HR": np.random.normal(65000, 10000, 50),
    "Finance": np.random.normal(85000, 14000, 70),
}

# Add some outliers
salary_data["Engineering"] = np.append(salary_data["Engineering"], [145000, 150000, 42000])
salary_data["Sales"] = np.append(salary_data["Sales"], [135000, 28000, 25000])
salary_data["Finance"] = np.append(salary_data["Finance"], [140000, 45000])

# Colors for each department (Python Blue first, then accessible colors)
colors = ["#306998", "#FFD43B", "#2CA02C", "#9467BD", "#E377C2"]

# Create figure
fig = go.Figure()

for i, (dept, values) in enumerate(salary_data.items()):
    fig.add_trace(
        go.Box(
            y=values,
            name=dept,
            boxpoints="outliers",
            notched=True,
            marker={"color": colors[i], "size": 10, "opacity": 0.7},
            line={"width": 2},
            fillcolor=colors[i],
            opacity=0.7,
        )
    )

# Layout for 4800x2700 px
fig.update_layout(
    title={"text": "box-notched · plotly · pyplots.ai", "font": {"size": 32}, "x": 0.5, "xanchor": "center"},
    xaxis={"title": {"text": "Department", "font": {"size": 24}}, "tickfont": {"size": 20}},
    yaxis={
        "title": {"text": "Annual Salary (USD)", "font": {"size": 24}},
        "tickfont": {"size": 20},
        "tickformat": "$,.0f",
        "gridcolor": "rgba(128, 128, 128, 0.3)",
        "gridwidth": 1,
    },
    template="plotly_white",
    showlegend=False,
    margin={"l": 100, "r": 60, "t": 100, "b": 80},
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
