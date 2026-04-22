""" pyplots.ai
facet-grid: Faceted Grid Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
import seaborn as sns


# Data
np.random.seed(42)

# Create dataset with two categorical faceting variables
categories_row = ["Region A", "Region B", "Region C"]
categories_col = ["Q1", "Q2", "Q3", "Q4"]

data = []
for row_cat in categories_row:
    for col_cat in categories_col:
        n_points = 25
        # Vary the relationship by region and quarter
        base_slope = 0.6 + 0.2 * categories_row.index(row_cat)
        intercept = 10 + 5 * categories_col.index(col_cat)

        x = np.random.uniform(5, 30, n_points)
        noise = np.random.normal(0, 3, n_points)
        y = intercept + base_slope * x + noise

        for i in range(n_points):
            data.append(
                {"Marketing Spend ($k)": x[i], "Sales Revenue ($k)": y[i], "Region": row_cat, "Quarter": col_cat}
            )

df = pd.DataFrame(data)

# Plot
sns.set_context("talk", font_scale=1.3)
sns.set_style("whitegrid")

g = sns.FacetGrid(df, row="Region", col="Quarter", height=4.5, aspect=1.1, margin_titles=True)

g.map_dataframe(
    sns.scatterplot,
    x="Marketing Spend ($k)",
    y="Sales Revenue ($k)",
    color="#306998",
    s=150,
    alpha=0.7,
    edgecolor="white",
    linewidth=0.5,
)

# Styling
g.set_titles(row_template="{row_name}", col_template="{col_name}", size=20)
g.set_axis_labels("Marketing Spend ($k)", "Sales Revenue ($k)", fontsize=18)

for ax in g.axes.flat:
    ax.tick_params(axis="both", labelsize=14)
    ax.grid(True, alpha=0.3, linestyle="--")

g.figure.suptitle("facet-grid · seaborn · pyplots.ai", fontsize=26, fontweight="bold", y=1.02)

g.tight_layout()

# Save
g.savefig("plot.png", dpi=300, bbox_inches="tight")
