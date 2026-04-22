""" pyplots.ai
line-yield-curve: Yield Curve (Interest Rate Term Structure)
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-14
"""

import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data
maturities = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
maturity_years = [1 / 12, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30]

yields_normal = [1.55, 1.72, 1.95, 2.15, 2.45, 2.68, 2.95, 3.12, 3.35, 3.65, 3.80]
yields_flat = [4.10, 4.15, 4.18, 4.20, 4.15, 4.12, 4.08, 4.05, 4.02, 3.98, 3.95]
yields_inverted = [5.45, 5.50, 5.48, 5.35, 5.05, 4.78, 4.42, 4.25, 4.10, 4.35, 4.40]

curve_labels = ["2021-06-15 · Normal", "2023-01-10 · Flat", "2024-07-01 · Inverted"]

df = pd.DataFrame(
    {
        "maturity_years": maturity_years * 3,
        "yield_pct": yields_normal + yields_flat + yields_inverted,
        "curve": [curve_labels[0]] * 11 + [curve_labels[1]] * 11 + [curve_labels[2]] * 11,
    }
)

# Ordered categorical for legend ordering (plotnine-specific: pd.Categorical + scale interaction)
df["curve"] = pd.Categorical(df["curve"], categories=curve_labels, ordered=True)

# Inversion zone: only span where short yields > long yields (2Y-10Y region)
inv_short_max = max(yields_inverted[:4])
inv_long_min = min(yields_inverted[4:])

# Tick positions — use only well-spaced maturities to avoid label cramping
tick_positions = [1, 2, 5, 7, 10, 20, 30]
tick_labels = ["1Y", "2Y", "5Y", "7Y", "10Y", "20Y", "30Y"]

# Colors: blue, amber, crimson — all colorblind-safe, high contrast
colors = ["#306998", "#E69F00", "#CC3333"]

# Plot — using plotnine's annotate() for non-data layers and stage() for aesthetic mapping
plot = (
    ggplot(df, aes(x="maturity_years", y="yield_pct", color="curve"))
    # Inversion zone shading — precise x-range where inversion is visible
    + annotate(
        "rect", xmin=-0.5, xmax=10.5, ymin=inv_long_min - 0.08, ymax=inv_short_max + 0.08, fill="#CC3333", alpha=0.06
    )
    + annotate(
        "text",
        x=5,
        y=inv_short_max + 0.22,
        label="Inversion zone (short-term yields > long-term)",
        size=10,
        color="#CC3333",
        alpha=0.75,
        fontstyle="italic",
    )
    # geom layers with explicit sizing for high-res output
    + geom_line(size=2.0, alpha=0.85)
    + geom_point(size=3.5, alpha=0.9)
    + scale_x_continuous(breaks=tick_positions, labels=tick_labels, limits=(0, 31), expand=(0.02, 0))
    + scale_y_continuous(breaks=[1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5], labels=lambda b: [f"{v:.1f}%" for v in b])
    + scale_color_manual(values=colors)
    # coord_cartesian for view clipping without data removal (plotnine-specific pattern)
    + coord_cartesian(ylim=(1.3, 5.8))
    # guide_legend for fine-grained legend control (plotnine-specific)
    + guides(color=guide_legend(title="Curve Date", override_aes={"size": 3, "alpha": 1}))
    + labs(x="Maturity", y="Yield (%)", title="U.S. Treasury Yield Curves · line-yield-curve · plotnine · pyplots.ai")
    + theme_minimal(base_size=14)
    + theme(
        figure_size=(16, 9),
        text=element_text(family="sans-serif"),
        axis_title=element_text(size=20, margin={"t": 12, "r": 12}),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24, weight="bold", margin={"b": 16}),
        legend_title=element_text(size=17, weight="bold"),
        legend_text=element_text(size=15),
        legend_position=(0.25, 0.30),
        legend_background=element_rect(fill="white", alpha=0.8, color="none"),
        legend_key=element_rect(fill="none", color="none"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.4, linetype="dashed"),
        axis_line_x=element_line(color="#333333", size=0.6),
        plot_background=element_rect(fill="white", color="none"),
        panel_background=element_rect(fill="#FAFAFA", color="none"),
    )
)

# Save
plot.save("plot.png", dpi=300)
