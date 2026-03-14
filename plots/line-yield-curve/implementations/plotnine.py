""" pyplots.ai
line-yield-curve: Yield Curve (Interest Rate Term Structure)
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-14
"""

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_text,
    geom_line,
    geom_point,
    geom_rect,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    theme,
    theme_minimal,
)


# Data
maturities = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
maturity_years = [1 / 12, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30]

yields_normal = [1.55, 1.72, 1.95, 2.15, 2.45, 2.68, 2.95, 3.12, 3.35, 3.65, 3.80]
yields_flat = [4.10, 4.15, 4.18, 4.20, 4.15, 4.12, 4.08, 4.05, 4.02, 3.98, 3.95]
yields_inverted = [5.45, 5.50, 5.48, 5.35, 5.05, 4.78, 4.42, 4.25, 4.10, 4.35, 4.40]

dates = ["2021-06-15 (Normal)", "2023-01-10 (Flat)", "2024-07-01 (Inverted)"]

df = pd.DataFrame(
    {
        "maturity_years": maturity_years * 3,
        "yield_pct": yields_normal + yields_flat + yields_inverted,
        "date": [dates[0]] * 11 + [dates[1]] * 11 + [dates[2]] * 11,
    }
)

# Inversion shading — highlight where short-term yields exceed long-term
inv_long_min = min(yields_inverted[6:])
inv_short_max = max(yields_inverted[:4])
shade_df = pd.DataFrame({"xmin": [0], "xmax": [31], "ymin": [inv_long_min], "ymax": [inv_short_max]})

label_df = pd.DataFrame({"x": [15], "y": [inv_short_max + 0.12], "label": ["Inversion zone"]})

# Use fewer tick marks to avoid label overlap at short maturities
tick_positions = [1 / 12, 1, 2, 5, 7, 10, 20, 30]
tick_labels = ["1M", "1Y", "2Y", "5Y", "7Y", "10Y", "20Y", "30Y"]

# Colors
colors = ["#306998", "#7B8FA1", "#C0392B"]

# Plot
plot = (
    ggplot(df, aes(x="maturity_years", y="yield_pct", color="date"))
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        data=shade_df,
        inherit_aes=False,
        fill="#C0392B",
        alpha=0.07,
        color=None,
    )
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=label_df,
        inherit_aes=False,
        size=11,
        color="#C0392B",
        alpha=0.6,
        fontstyle="italic",
    )
    + geom_line(size=1.8)
    + geom_point(size=3.5)
    + scale_x_continuous(breaks=tick_positions, labels=tick_labels, limits=(0, 31))
    + scale_color_manual(values=colors)
    + labs(
        x="Maturity",
        y="Yield (%)",
        title="U.S. Treasury Yield Curves · line-yield-curve · plotnine · pyplots.ai",
        color="Date",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=22, weight="bold"),
        legend_title=element_text(size=18),
        legend_text=element_text(size=15),
        legend_position=(0.22, 0.35),
        legend_background=element_blank(),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#DDDDDD", size=0.5, alpha=0.5),
        axis_line_x=element_line(color="#333333", size=0.5),
    )
)

# Save
plot.save("plot.png", dpi=300)
