""" anyplot.ai
line-yield-curve: Yield Curve (Interest Rate Term Structure)
Library: plotnine 0.15.5 | Python 3.13.13
Quality: 91/100 | Updated: 2026-06-10
"""

import os

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


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — first series always #009E73; matte red for recession/inversion signal
PALETTE_NORMAL = "#009E73"  # brand green — growth / upward-sloping
PALETTE_FLAT = "#C475FD"  # lavender — neutral / transitional
PALETTE_INVERTED = "#AE3030"  # matte red — recession indicator / inverted

# Data
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

# Ordered categorical for legend ordering (plotnine: pd.Categorical + scale interaction)
df["curve"] = pd.Categorical(df["curve"], categories=curve_labels, ordered=True)

# Inversion zone bounds
inv_short_max = max(yields_inverted[:4])  # 5.50
inv_long_min = min(yields_inverted[4:])  # 4.10

# Tick positions — well-spaced to avoid label cramping
tick_positions = [1, 2, 5, 7, 10, 20, 30]
tick_labels = ["1Y", "2Y", "5Y", "7Y", "10Y", "20Y", "30Y"]

# Title with length-scaled fontsize (see prompts/plot-generator.md)
title = "U.S. Treasury Yield Curves · line-yield-curve · python · plotnine · anyplot.ai"
n = len(title)
title_fontsize = max(8, round(12 * 67 / n)) if n > 67 else 12

# Plot
plot = (
    ggplot(df, aes(x="maturity_years", y="yield_pct", color="curve"))
    # Inversion zone shading — more prominent than previous (alpha=0.10 vs 0.06)
    + annotate(
        "rect",
        xmin=-0.5,
        xmax=10.5,
        ymin=inv_long_min - 0.08,
        ymax=inv_short_max + 0.08,
        fill=PALETTE_INVERTED,
        alpha=0.10,
    )
    + annotate(
        "text",
        x=0.5,
        y=inv_short_max + 0.22,
        label="Inversion zone (short-term > long-term)",
        size=9,
        color=PALETTE_INVERTED,
        alpha=0.85,
        fontstyle="italic",
        ha="left",
    )
    # geom layers sized for 3200×1800 canvas
    + geom_line(size=2.0, alpha=0.85)
    + geom_point(size=3.5, alpha=0.9)
    + scale_x_continuous(breaks=tick_positions, labels=tick_labels, limits=(0, 31), expand=(0.02, 0))
    + scale_y_continuous(
        breaks=[1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5], labels=lambda b: [f"{v:.1f}%" for v in b]
    )
    + scale_color_manual(values=[PALETTE_NORMAL, PALETTE_FLAT, PALETTE_INVERTED])
    # coord_cartesian for view clipping without data removal (plotnine pattern)
    + coord_cartesian(ylim=(1.3, 5.9))
    # guide_legend for fine-grained legend control
    + guides(color=guide_legend(title="Curve Date", override_aes={"size": 3, "alpha": 1}))
    + labs(x="Maturity", y="Yield (%)", title=title)
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(family="sans-serif", color=INK),
        axis_title=element_text(size=10, color=INK, margin={"t": 8, "r": 8}),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=title_fontsize, weight="bold", color=INK, margin={"b": 10}),
        legend_title=element_text(size=9, weight="bold", color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_position=(0.25, 0.30),
        legend_background=element_rect(fill=ELEVATED_BG, alpha=0.9, color=INK_SOFT),
        legend_key=element_rect(fill="none", color="none"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.15),
        axis_line_x=element_line(color=INK_SOFT, size=0.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
