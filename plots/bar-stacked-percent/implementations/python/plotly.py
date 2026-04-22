""" pyplots.ai
bar-stacked-percent: 100% Stacked Bar Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-25
"""

import pandas as pd
import plotly.graph_objects as go


# Data: Energy mix by country (percentage breakdown)
categories = ["Germany", "France", "UK", "Spain", "Italy", "Poland"]
components = ["Renewables", "Nuclear", "Natural Gas", "Coal", "Other"]

# Raw values (TWh) - will be normalized to 100%
data = {
    "Germany": [250, 65, 90, 105, 30],
    "France": [120, 340, 45, 10, 25],
    "UK": [145, 50, 130, 5, 20],
    "Spain": [175, 55, 85, 15, 20],
    "Italy": [115, 0, 145, 25, 15],
    "Poland": [45, 0, 25, 130, 15],
}

# Convert to percentages
df = pd.DataFrame(data, index=components)
df_percent = df.div(df.sum(axis=0), axis=1) * 100

# Colors: Python Blue first, then colorblind-safe palette
colors = ["#306998", "#FFD43B", "#45B39D", "#E74C3C", "#9B59B6"]

# Create figure
fig = go.Figure()

for i, component in enumerate(components):
    fig.add_trace(
        go.Bar(
            name=component,
            x=categories,
            y=df_percent.loc[component].values,
            marker_color=colors[i],
            text=[f"{v:.1f}%" for v in df_percent.loc[component].values],
            textposition="inside",
            textfont=dict(size=16, color="white"),
            insidetextanchor="middle",
        )
    )

# Layout for 4800x2700 px
fig.update_layout(
    barmode="stack",
    title=dict(text="bar-stacked-percent · plotly · pyplots.ai", font=dict(size=32), x=0.5, xanchor="center"),
    xaxis=dict(title=dict(text="Country", font=dict(size=24)), tickfont=dict(size=20)),
    yaxis=dict(
        title=dict(text="Energy Share (%)", font=dict(size=24)), tickfont=dict(size=20), range=[0, 100], ticksuffix="%"
    ),
    legend=dict(
        font=dict(size=18), orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, traceorder="normal"
    ),
    template="plotly_white",
    margin=dict(l=80, r=40, t=120, b=80),
    bargap=0.2,
)

# Save as PNG (4800x2700)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs="cdn")
