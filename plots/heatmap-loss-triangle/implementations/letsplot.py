""" pyplots.ai
heatmap-loss-triangle: Actuarial Loss Development Triangle
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 79/100 | Created: 2026-03-09
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - Cumulative paid claims triangle (10 accident years x 10 development periods)
np.random.seed(42)
accident_years = list(range(2015, 2025))
dev_periods = list(range(1, 11))
n_years = len(accident_years)
n_periods = len(dev_periods)

# Generate realistic initial claims and development factors
initial_claims = np.random.uniform(8000, 15000, n_years)
age_to_age_factors = [2.50, 1.45, 1.22, 1.12, 1.07, 1.04, 1.025, 1.015, 1.008]

# Build the cumulative triangle
triangle = np.full((n_years, n_periods), np.nan)
for i in range(n_years):
    triangle[i, 0] = initial_claims[i]
    for j in range(1, n_periods):
        noise = np.random.normal(1.0, 0.02)
        triangle[i, j] = triangle[i, j - 1] * age_to_age_factors[j - 1] * noise

# Determine actual vs projected (upper-left triangle is actual)
rows = []
for i in range(n_years):
    for j in range(n_periods):
        is_projected = (i + j) >= n_years
        rows.append(
            {
                "accident_year": str(accident_years[i]),
                "dev_period": str(dev_periods[j]),
                "cumulative": triangle[i, j],
                "region": "Projected" if is_projected else "Actual",
            }
        )

df = pd.DataFrame(rows)
df["accident_year"] = df["accident_year"].astype(object)
df["dev_period"] = df["dev_period"].astype(object)

# Format labels with thousands separator
df["label"] = df["cumulative"].apply(lambda v: f"{v:,.0f}")

# Text color: white on dark cells, dark on light cells
max_val = df["cumulative"].max()
min_val = df["cumulative"].min()
df["text_color"] = df["cumulative"].apply(
    lambda v: "white" if (v - min_val) / (max_val - min_val) > 0.65 else "#1a1a1a"
)

# Plot
plot = (
    ggplot(df, aes(x="dev_period", y="accident_year"))
    + geom_tile(aes(fill="cumulative", alpha="region"), color="white", size=1.2)
    + geom_text(aes(label="label", color="text_color"), size=9)
    + scale_color_identity()
    + scale_fill_gradient(low="#E8F0FE", high="#1A3A6B", name="Cumulative\nClaims ($)")
    + scale_alpha_manual(values={"Actual": 1.0, "Projected": 0.6}, name="Region")
    + scale_x_discrete(limits=[str(p) for p in dev_periods])
    + scale_y_discrete(limits=[str(y) for y in accident_years[::-1]])
    + labs(x="Development Period (Years)", y="Accident Year", title="heatmap-loss-triangle · lets-plot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        panel_grid=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
