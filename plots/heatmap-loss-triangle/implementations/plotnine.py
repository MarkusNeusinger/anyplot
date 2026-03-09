"""pyplots.ai
heatmap-loss-triangle: Actuarial Loss Development Triangle
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-03-09
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
    scale_color_identity,
    scale_fill_gradient2,
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

# Base initial claims for each accident year (realistic range)
base_claims = np.array([3200, 3450, 3100, 3600, 3800, 3500, 3900, 4100, 3700, 4200])

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
        # Upper-left triangle is actual, lower-right is projected
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

# Midpoint for color scale
amount_mid = (df["cumulative_amount"].min() + df["cumulative_amount"].max()) / 2

# Text color: white on dark tiles, dark on light tiles
df["text_color"] = df["cumulative_amount"].apply(lambda v: "white" if v > amount_mid * 1.3 else "#1a1a1a")

# Separate actual and projected for different alpha
df_actual = df[~df["is_projected"]].copy()
df_projected = df[df["is_projected"]].copy()

# Plot
plot = (
    ggplot()
    # Actual cells (full opacity)
    + geom_tile(
        data=df_actual,
        mapping=aes(x="development_period", y="accident_year", fill="cumulative_amount"),
        color="white",
        size=1.2,
        alpha=1.0,
    )
    # Projected cells (reduced opacity)
    + geom_tile(
        data=df_projected,
        mapping=aes(x="development_period", y="accident_year", fill="cumulative_amount"),
        color="white",
        size=1.2,
        alpha=0.55,
    )
    # Cell annotations
    + geom_text(
        data=df, mapping=aes(x="development_period", y="accident_year", label="label", color="text_color"), size=7
    )
    + scale_fill_gradient2(low="#e8f4f8", mid="#306998", high="#1a1a2e", midpoint=amount_mid, name="Cumulative\nAmount")
    + scale_color_identity()
    + scale_x_continuous(breaks=development_periods, labels=[str(d) for d in development_periods])
    + scale_y_reverse(breaks=accident_years, labels=[str(y) for y in accident_years])
    + labs(
        x="Development Period (Years)",
        y="Accident Year",
        title="heatmap-loss-triangle · plotnine · pyplots.ai",
        subtitle="Cumulative Paid Claims — Actual (solid) vs Projected (faded)",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 10),
        plot_title=element_text(size=22, ha="center", weight="bold"),
        plot_subtitle=element_text(size=16, ha="center", color="#555555"),
        axis_title=element_text(size=18),
        axis_text_x=element_text(size=14),
        axis_text_y=element_text(size=14),
        legend_title=element_text(size=14),
        legend_text=element_text(size=12),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill="white", color="white"),
        panel_background=element_rect(fill="white", color="white"),
    )
)

# Save
plot.save("plot.png", dpi=300, width=16, height=10)
