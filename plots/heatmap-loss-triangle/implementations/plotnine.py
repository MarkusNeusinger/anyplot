""" pyplots.ai
heatmap-loss-triangle: Actuarial Loss Development Triangle
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-09
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_text,
    geom_tile,
    ggplot,
    labs,
    scale_alpha_manual,
    scale_color_identity,
    scale_fill_gradientn,
    scale_x_continuous,
    scale_y_reverse,
    theme,
    theme_minimal,
)


# Data: Cumulative paid claims triangle (10 accident years x 10 development periods)
np.random.seed(42)

accident_years = list(range(2015, 2025))
development_periods = list(range(1, 11))
n_years = len(accident_years)
n_periods = len(development_periods)

# Base initial claims for each accident year
# 2019 is an anomalous year with higher initial claims (e.g., catastrophe year)
base_claims = np.array([3200, 3450, 3100, 3600, 5200, 3500, 3900, 4100, 3700, 4200])

# Age-to-age development factors (decreasing toward 1.0 as claims mature)
dev_factors = np.array([2.50, 1.60, 1.30, 1.15, 1.08, 1.05, 1.03, 1.02, 1.01])

# Build cumulative amounts
cumulative = np.zeros((n_years, n_periods))
for i in range(n_years):
    cumulative[i, 0] = base_claims[i] + np.random.normal(0, 100)
    for j in range(1, n_periods):
        noise = 1 + np.random.normal(0, 0.02)
        cumulative[i, j] = cumulative[i, j - 1] * dev_factors[j - 1] * noise

# Round to integers for display
cumulative = np.round(cumulative, 0).astype(int)

# Build long-format DataFrame
rows = []
for i, ay in enumerate(accident_years):
    for j, dp in enumerate(development_periods):
        is_projected = (i + j) >= n_years
        rows.append(
            {
                "accident_year": ay,
                "development_period": dp,
                "cumulative_amount": cumulative[i, j],
                "is_projected": is_projected,
            }
        )

df = pd.DataFrame(rows)

# Format amounts with thousands separator for annotations
df["label"] = df["cumulative_amount"].apply(lambda v: f"{v:,}")

# Region label for legend
df["region"] = df["is_projected"].map({False: "Actual", True: "Projected"})

# Text color: white on dark tiles, dark on light tiles
amount_75 = df["cumulative_amount"].quantile(0.45)
df["text_color"] = df["cumulative_amount"].apply(lambda v: "white" if v > amount_75 else "#1b2838")

# Development factors as a data-driven geom_text layer
dev_factor_y = max(accident_years) + 1.3
df_dev = pd.DataFrame(
    {
        "development_period": [j + 1.5 for j in range(len(dev_factors))],
        "accident_year": dev_factor_y,
        "label": [f"{f:.2f}" for f in dev_factors],
        "cumulative_amount": 0.0,
        "region": "Actual",
    }
)

# Perceptually uniform blue palette with better mid-range differentiation
palette_colors = ["#e8f4f8", "#a8d4e6", "#5ba3c9", "#306998", "#1b3a5c", "#0d1b2a"]

# Plot
plot = (
    ggplot(df, aes(x="development_period", y="accident_year"))
    + geom_tile(aes(fill="cumulative_amount", alpha="region"), color="white", size=1.2)
    + geom_text(aes(label="label", color="text_color"), size=7.5)
    # Dev factors as data-driven layer
    + geom_text(
        aes(x="development_period", y="accident_year", label="label"),
        data=df_dev,
        size=8,
        color="#306998",
        fontweight="bold",
        inherit_aes=False,
    )
    # Perceptually uniform gradient
    + scale_fill_gradientn(colors=palette_colors, name="Cumulative\nAmount")
    + scale_alpha_manual(values={"Actual": 1.0, "Projected": 0.35}, name="Region")
    + scale_color_identity()
    + scale_x_continuous(breaks=development_periods, labels=[str(d) for d in development_periods], expand=(0, 0.5))
    + scale_y_reverse(
        breaks=accident_years + [dev_factor_y],
        labels=[str(y) for y in accident_years] + ["Dev Factor"],
        expand=(0, 0.3, 0, 1.2),
    )
    + labs(
        x="Development Period (Years)",
        y="Accident Year",
        title="heatmap-loss-triangle · plotnine · pyplots.ai",
        subtitle="Cumulative Paid Claims — Actual vs Projected  ·  Development Factors shown below",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center", weight="bold"),
        plot_subtitle=element_text(size=16, ha="center", color="#555555"),
        plot_margin=0.02,
        axis_title=element_text(size=20),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=16),
        legend_title=element_text(size=14, weight="bold"),
        legend_text=element_text(size=12),
        legend_position="right",
        legend_box_margin=0,
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill="white", color="white"),
        panel_background=element_rect(fill="white", color="white"),
    )
)

# Save
plot.save("plot.png", dpi=300, width=16, height=9)
