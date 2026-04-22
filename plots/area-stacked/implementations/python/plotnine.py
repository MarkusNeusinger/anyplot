""" pyplots.ai
area-stacked: Stacked Area Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_text,
    geom_area,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_date,
    theme,
    theme_minimal,
)


# Data: Website traffic sources over 24 months
np.random.seed(42)

dates = pd.date_range(start="2023-01-01", periods=24, freq="MS")

# Generate realistic traffic data with trends
base_direct = 15000 + np.cumsum(np.random.randn(24) * 500)
base_organic = 25000 + np.cumsum(np.random.randn(24) * 800) + np.arange(24) * 300
base_referral = 10000 + np.cumsum(np.random.randn(24) * 400)
base_social = 8000 + np.cumsum(np.random.randn(24) * 600) + np.arange(24) * 200

# Ensure all values are positive
direct = np.maximum(base_direct, 5000)
organic = np.maximum(base_organic, 10000)
referral = np.maximum(base_referral, 3000)
social = np.maximum(base_social, 2000)

# Create long-format DataFrame for stacking
df = pd.DataFrame(
    {
        "Date": np.tile(dates, 4),
        "Visitors": np.concatenate([direct, organic, referral, social]),
        "Source": (["Direct"] * 24 + ["Organic Search"] * 24 + ["Referral"] * 24 + ["Social Media"] * 24),
    }
)

# Order categories by average size (largest at bottom for easier reading)
source_order = ["Organic Search", "Direct", "Referral", "Social Media"]
df["Source"] = pd.Categorical(df["Source"], categories=source_order, ordered=True)

# Colors: Python Blue first, then complementary colorblind-safe colors
colors = ["#306998", "#FFD43B", "#4DAF4A", "#E41A1C"]

# Create stacked area chart
plot = (
    ggplot(df, aes(x="Date", y="Visitors", fill="Source"))
    + geom_area(alpha=0.85, position="stack")
    + scale_fill_manual(values=colors)
    + scale_x_date(date_labels="%b %Y", date_breaks="3 months")
    + labs(title="area-stacked · plotnine · pyplots.ai", x="Month", y="Monthly Visitors", fill="Traffic Source")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        axis_text_x=element_text(angle=45, hjust=1),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
        panel_grid_major=element_line(color="#CCCCCC", size=0.5, alpha=0.3),
        panel_grid_minor=element_line(color="#EEEEEE", size=0.25, alpha=0.2),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
