""" pyplots.ai
pyramid-basic: Basic Pyramid Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import plotly.graph_objects as go


# Data - Population pyramid by age group (in thousands)
age_groups = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]
male_population = [4200, 4800, 5500, 5200, 4900, 4100, 3200, 2100, 900]
female_population = [4000, 4600, 5300, 5400, 5100, 4400, 3600, 2700, 1400]

# Create figure
fig = go.Figure()

# Left bars (male) - negative values to extend left
fig.add_trace(
    go.Bar(
        y=age_groups,
        x=[-v for v in male_population],
        orientation="h",
        name="Male",
        marker_color="#306998",
        hovertemplate="Male<br>Age: %{y}<br>Population: %{customdata:,}<extra></extra>",
        customdata=male_population,
    )
)

# Right bars (female) - positive values to extend right
fig.add_trace(
    go.Bar(
        y=age_groups,
        x=female_population,
        orientation="h",
        name="Female",
        marker_color="#FFD43B",
        hovertemplate="Female<br>Age: %{y}<br>Population: %{customdata:,}<extra></extra>",
        customdata=female_population,
    )
)

# Layout
max_val = max(max(male_population), max(female_population))
tick_vals = [-5000, -2500, 0, 2500, 5000]
tick_text = ["5,000", "2,500", "0", "2,500", "5,000"]

fig.update_layout(
    title={
        "text": "Population Distribution · pyramid-basic · plotly · pyplots.ai",
        "font": {"size": 36},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Population (thousands)", "font": {"size": 28}},
        "tickfont": {"size": 22},
        "tickvals": tick_vals,
        "ticktext": tick_text,
        "range": [-max_val * 1.15, max_val * 1.15],
        "gridcolor": "rgba(128, 128, 128, 0.3)",
        "gridwidth": 1,
        "zeroline": True,
        "zerolinecolor": "rgba(128, 128, 128, 0.5)",
        "zerolinewidth": 2,
    },
    yaxis={
        "title": {"text": "Age Group", "font": {"size": 28}},
        "tickfont": {"size": 22},
        "categoryorder": "array",
        "categoryarray": age_groups,
    },
    barmode="overlay",
    bargap=0.15,
    template="plotly_white",
    legend={"font": {"size": 24}, "orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "center", "x": 0.5},
    margin={"l": 120, "r": 80, "t": 150, "b": 100},
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
