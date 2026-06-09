"""anyplot.ai
scatter-connected-temporal: Connected Scatter Plot with Temporal Path
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-06-09
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    arrow,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_color_gradient,
    scale_fill_gradient,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.12)" if THEME == "light" else "rgba(240,239,232,0.12)"

# Imprint sequential colormap: brand green (early) → blue (recent)
SEQ_LOW = "#009E73"  # Imprint position 1 — start of temporal path
SEQ_HIGH = "#4467A3"  # Imprint position 3 — end of temporal path

# Data — Phillips curve dynamics, unemployment vs inflation 1990–2023
np.random.seed(42)
years = np.arange(1990, 2024)
n = len(years)

unemployment = np.concatenate(
    [
        np.linspace(5.6, 4.0, 10) + np.random.randn(10) * 0.3,  # 1990s decline
        np.linspace(4.0, 6.3, 4) + np.random.randn(4) * 0.2,  # 2001 recession
        np.linspace(6.3, 4.4, 6) + np.random.randn(6) * 0.2,  # mid-2000s recovery
        np.linspace(4.4, 10.0, 3) + np.random.randn(3) * 0.3,  # 2008 crisis
        np.linspace(10.0, 3.5, 11) + np.random.randn(11) * 0.3,  # long recovery
    ]
)
inflation = np.concatenate(
    [
        np.linspace(5.4, 2.3, 10) + np.random.randn(10) * 0.4,  # 1990s disinflation
        np.linspace(2.3, 1.6, 4) + np.random.randn(4) * 0.3,  # low inflation
        np.linspace(1.6, 3.8, 6) + np.random.randn(6) * 0.3,  # rising
        np.linspace(3.8, -0.4, 3) + np.random.randn(3) * 0.4,  # deflation scare
        np.linspace(-0.4, 6.5, 11) + np.random.randn(11) * 0.5,  # recovery to post-covid
    ]
)

df = pd.DataFrame(
    {
        "unemployment": unemployment,
        "inflation": inflation,
        "year": years,
        "year_label": [str(y) for y in years],
        "time_idx": np.arange(n),
    }
)

# Annotate key economic turning points
key_years = {1990, 2000, 2007, 2009, 2020, 2023}
df_labels = df[df["year"].isin(key_years)].copy()

nudge_map = {
    1990: (0.35, 0.7),
    2000: (0.35, -0.7),
    2007: (0.35, -0.7),
    2009: (-0.55, 0.7),
    2020: (-0.35, 0.7),
    2023: (0.35, 0.7),
}

df_endpoints = df[df["year"].isin([1990, 2023])].copy()
df_labels["label_x"] = df_labels.apply(lambda r: r["unemployment"] + nudge_map.get(r["year"], (0, 0))[0], axis=1)
df_labels["label_y"] = df_labels.apply(lambda r: r["inflation"] + nudge_map.get(r["year"], (0, 0))[1], axis=1)

# Direction arrow at terminal segment of the path
last = df.iloc[-1]
prev = df.iloc[-2]
arrow_df = pd.DataFrame(
    {"x": [prev["unemployment"]], "y": [prev["inflation"]], "xend": [last["unemployment"]], "yend": [last["inflation"]]}
)

title = "scatter-connected-temporal · python · letsplot · anyplot.ai"

# Plot
plot = (
    ggplot(df, aes(x="unemployment", y="inflation"))
    + geom_path(aes(color="time_idx"), size=1.5, alpha=0.75, tooltips="none")
    + geom_segment(
        data=arrow_df,
        mapping=aes(x="x", y="y", xend="xend", yend="yend"),
        color=SEQ_HIGH,
        size=2.2,
        arrow=arrow(angle=25, length=10, type="closed"),
    )
    + geom_point(
        aes(fill="time_idx"),
        color=PAGE_BG,
        size=3.5,
        stroke=1.0,
        shape=21,
        alpha=0.9,
        tooltips=layer_tooltips()
        .line("Year|@year")
        .line("Unemployment|@{unemployment}{.1f}%")
        .line("Inflation|@{inflation}{.1f}%"),
    )
    + geom_point(
        data=df_endpoints,
        mapping=aes(x="unemployment", y="inflation", fill="time_idx"),
        color=INK,
        size=6.0,
        stroke=1.8,
        shape=21,
        alpha=1.0,
    )
    + geom_text(
        data=df_labels,
        mapping=aes(x="label_x", y="label_y", label="year_label"),
        size=5,
        color=INK,
        family="monospace",
        fontface="bold",
    )
    + scale_color_gradient(
        low=SEQ_LOW, high=SEQ_HIGH, name="Year", breaks=[0, (n - 1) / 2, n - 1], labels=["1990", "2006", "2023"]
    )
    + scale_fill_gradient(low=SEQ_LOW, high=SEQ_HIGH, guide="none")
    + scale_x_continuous(expand=[0.06, 0])
    + scale_y_continuous(expand=[0.08, 0])
    + labs(
        x="Unemployment Rate (%)",
        y="Inflation Rate (%)",
        title=title,
        subtitle="Phillips Curve: unemployment vs inflation, 1990–2023",
    )
    + ggsize(800, 450)
    + theme_minimal()
    + theme(
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_title=element_text(size=12, color=INK),
        plot_title=element_text(size=16, color=INK),
        plot_subtitle=element_text(size=10, color=INK_SOFT),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=12, color=INK),
        panel_grid_major=element_line(color=GRID, size=0.3),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        plot_margin=[20, 20, 10, 10],
    )
)

# Save — PNG at 3200×1800 (800×450 × scale=4), plus interactive HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
