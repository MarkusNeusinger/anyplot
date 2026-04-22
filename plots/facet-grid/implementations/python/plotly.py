""" pyplots.ai
facet-grid: Faceted Grid Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
import plotly.express as px


# Data - Create realistic dataset for faceted visualization
np.random.seed(42)

# Product performance data across regions and quarters
regions = ["North", "South", "East", "West"]
quarters = ["Q1", "Q2", "Q3", "Q4"]

data = []
for region in regions:
    for quarter in quarters:
        # Generate 15 data points per region-quarter combination
        n = 15
        # Base values vary by region and quarter
        base_sales = {"North": 80, "South": 60, "East": 70, "West": 75}
        quarter_effect = {"Q1": 0, "Q2": 10, "Q3": 5, "Q4": 15}

        marketing_spend = np.random.uniform(10, 50, n)
        sales = (
            base_sales[region]
            + quarter_effect[quarter]
            + marketing_spend * (0.8 + np.random.uniform(0, 0.4, n))
            + np.random.normal(0, 5, n)
        )

        for i in range(n):
            data.append(
                {
                    "Marketing Spend ($K)": marketing_spend[i],
                    "Sales ($K)": sales[i],
                    "Region": region,
                    "Quarter": quarter,
                }
            )

df = pd.DataFrame(data)

# Create faceted scatter plot
# Using single color since Region is already encoded by facet rows
fig = px.scatter(df, x="Marketing Spend ($K)", y="Sales ($K)", facet_row="Region", facet_col="Quarter")

# Update layout for large canvas
fig.update_layout(
    title=dict(text="facet-grid · plotly · pyplots.ai", font=dict(size=32), x=0.5, xanchor="center"),
    font=dict(size=16),
    template="plotly_white",
    showlegend=False,
    margin=dict(l=80, r=80, t=100, b=80),
)

# Update axes for all facets
fig.update_xaxes(title_font=dict(size=20), tickfont=dict(size=16), gridcolor="rgba(0,0,0,0.1)", gridwidth=1)

fig.update_yaxes(title_font=dict(size=20), tickfont=dict(size=16), gridcolor="rgba(0,0,0,0.1)", gridwidth=1)

# Update facet labels (annotations)
fig.for_each_annotation(lambda a: a.update(font=dict(size=18)))

# Update markers with consistent color for visibility
fig.update_traces(marker=dict(size=12, opacity=0.8, color="#306998", line=dict(width=1, color="white")))

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
