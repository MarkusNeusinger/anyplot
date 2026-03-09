""" pyplots.ai
heatmap-loss-triangle: Actuarial Loss Development Triangle
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-09
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

# Age-to-age development factors (realistic chain-ladder factors)
age_to_age_factors = [2.50, 1.45, 1.22, 1.12, 1.07, 1.04, 1.025, 1.015, 1.008]

# Generate realistic initial claims and build cumulative triangle
initial_claims = np.random.uniform(8000, 15000, n_years)
triangle = np.full((n_years, n_periods), np.nan)
for i in range(n_years):
    triangle[i, 0] = initial_claims[i]
    for j in range(1, n_periods):
        noise = max(np.random.normal(1.0, 0.02), 1.0 / age_to_age_factors[j - 1])
        triangle[i, j] = triangle[i, j - 1] * age_to_age_factors[j - 1] * noise

# Build main heatmap dataframe
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

# Format labels with thousands separator
df["label"] = df["cumulative"].apply(lambda v: f"{v:,.0f}")

# Text color: white on dark cells, dark on light cells
max_val = df["cumulative"].max()
min_val = df["cumulative"].min()
df["text_color"] = df["cumulative"].apply(
    lambda v: "white" if (v - min_val) / (max_val - min_val) > 0.65 else "#1a1a1a"
)

# Build development factors row dataframe
factor_rows = []
for j in range(len(age_to_age_factors)):
    factor_rows.append(
        {"accident_year": "Factor", "dev_period": str(dev_periods[j]), "label": f"{age_to_age_factors[j]:.3f}"}
    )
# Last column has no forward factor
factor_rows.append({"accident_year": "Factor", "dev_period": str(dev_periods[-1]), "label": "—"})
df_factors = pd.DataFrame(factor_rows)

# Y-axis ordering: Factor at bottom, 2024 above it, 2015 at top (ggplot y goes bottom-to-top)
y_order = ["Factor"] + [str(y) for y in reversed(accident_years)]

# Separate actual and projected for distinct styling
df_actual = df[df["region"] == "Actual"].copy()
df_projected = df[df["region"] == "Projected"].copy()

# Plot with separate layers for actual vs projected (distinct border colors)
plot = (
    ggplot()
    # Actual cells: solid white border
    + geom_tile(aes(x="dev_period", y="accident_year", fill="cumulative"), data=df_actual, color="white", size=1.2)
    # Projected cells: dashed-style border (orange-tinted) with lower alpha
    + geom_tile(
        aes(x="dev_period", y="accident_year", fill="cumulative"),
        data=df_projected,
        color="#E8A838",
        size=1.4,
        alpha=0.7,
    )
    # Cell value annotations
    + geom_text(aes(x="dev_period", y="accident_year", label="label", color="text_color"), data=df, size=9)
    # Factor row background
    + geom_tile(aes(x="dev_period", y="accident_year"), data=df_factors, fill="#F0F4F8", color="#B0BEC5", size=0.8)
    # Factor labels
    + geom_text(
        aes(x="dev_period", y="accident_year", label="label"),
        data=df_factors,
        color="#2C5F8A",
        size=10,
        fontface="bold",
    )
    + scale_color_identity()
    + scale_fill_gradient(low="#E8F0FE", high="#1A3A6B", name="Cumulative\nClaims ($)")
    + scale_x_discrete(limits=[str(p) for p in dev_periods])
    + scale_y_discrete(limits=y_order)
    + labs(
        x="Development Period (Years)",
        y="Accident / Origin Year",
        title="heatmap-loss-triangle · lets-plot · pyplots.ai",
        subtitle="Chain-Ladder Loss Triangle  ·  Actual (white border) vs Projected (gold border, 70% opacity)",
        caption="Bottom row: Age-to-Age Development Factors",
    )
    + coord_fixed(ratio=0.85)
    + theme_minimal()
    + flavor_darcula()
    + theme(
        plot_title=element_text(size=24, face="bold", color="white"),
        plot_subtitle=element_text(size=16, color="#B0BEC5"),
        plot_caption=element_text(size=14, color="#B0BEC5"),
        axis_title=element_text(size=20, color="#E0E0E0"),
        axis_text=element_text(size=16, color="#C0C0C0"),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        panel_grid=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
