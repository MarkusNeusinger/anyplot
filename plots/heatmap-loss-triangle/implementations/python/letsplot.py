""" pyplots.ai
heatmap-loss-triangle: Actuarial Loss Development Triangle
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-09
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

# Create legend data: two rows representing region types for the explicit legend
df_legend = pd.DataFrame(
    {
        "x": [str(dev_periods[0]), str(dev_periods[0])],
        "y": [str(accident_years[0]), str(accident_years[0])],
        "region": ["■ Actual (white border)", "■ Projected (gold border)"],
        "clr": ["white", "#E8A838"],
    }
)

# Split text into light and dark for readability against varying backgrounds
df_light_text = df[df["text_color"] == "white"].copy()
df_dark_text = df[df["text_color"] != "white"].copy()

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
    # Cell value annotations (split by text color to avoid color scale conflict)
    + geom_text(aes(x="dev_period", y="accident_year", label="label"), data=df_light_text, color="white", size=12)
    + geom_text(aes(x="dev_period", y="accident_year", label="label"), data=df_dark_text, color="#1a1a1a", size=12)
    # Invisible points for explicit actual/projected legend
    + geom_point(aes(x="x", y="y", color="region"), data=df_legend, size=0, alpha=0)
    + scale_color_manual(
        values={"■ Actual (white border)": "white", "■ Projected (gold border)": "#E8A838"},
        name="Cell Region",
        guide=guide_legend(override_aes={"size": 8, "alpha": 1, "shape": 15}),
    )
    # Factor row background
    + geom_tile(aes(x="dev_period", y="accident_year"), data=df_factors, fill="#F0F4F8", color="#B0BEC5", size=0.8)
    # Factor labels
    + geom_text(
        aes(x="dev_period", y="accident_year", label="label"),
        data=df_factors,
        color="#1A4D7A",
        size=12,
        fontface="bold",
    )
    + scale_fill_gradient2(
        low="#E8F0FE",
        mid="#4A7FB5",
        high="#0D2240",
        midpoint=(df["cumulative"].max() + df["cumulative"].min()) / 2,
        name="Cumulative\nClaims ($)",
    )
    + scale_x_discrete(limits=[str(p) for p in dev_periods])
    + scale_y_discrete(limits=y_order)
    + labs(
        x="Development Period (Years)",
        y="Accident / Origin Year",
        title="heatmap-loss-triangle · letsplot · pyplots.ai",
        subtitle="Chain-Ladder Loss Triangle  ·  Actual (white border) vs Projected (gold border, 70% opacity)",
        caption="Bottom row: Age-to-Age Development Factors",
    )
    + coord_fixed(ratio=0.65)
    + theme_minimal()
    + flavor_darcula()
    + theme(
        plot_title=element_text(size=26, face="bold", color="#FFFFFF"),
        plot_subtitle=element_text(size=15, face="italic", color="#90A4AE"),
        plot_caption=element_text(size=13, color="#78909C"),
        axis_title=element_text(size=20, face="bold", color="#CFD8DC"),
        axis_text_x=element_text(size=17, face="bold", color="#B0BEC5"),
        axis_text_y=element_text(size=16, color="#B0BEC5"),
        legend_title=element_text(size=16, face="bold"),
        legend_text=element_text(size=14),
        legend_position="right",
        panel_grid=element_blank(),
        plot_margin=[40, 20, 30, 20],
    )
    + ggsize(1700, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
