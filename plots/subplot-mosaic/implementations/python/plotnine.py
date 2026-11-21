"""anyplot.ai
subplot-mosaic: Mosaic Subplot Layout with Varying Sizes
Library: plotnine 0.15.9 | Python 3.14
Quality: 95/100 | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_col,
    geom_line,
    geom_point,
    geom_text,
    geom_tile,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_gradient,
    scale_fill_manual,
    scale_x_continuous,
    scale_x_discrete,
    scale_y_discrete,
    theme,
    theme_minimal,
    theme_set,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

theme_set(theme_minimal())

# Columns: set these to your table's column names
PANEL = "Panel"  # role: extra
X = "x"  # role: x
Y = "y"  # role: y
GROUP = "Group"  # role: z
X_LABEL = "x label"  # role: extra
Y_LABEL = "y label"  # role: extra

# Data: one tidy table, one row per mark; the first panel is the primary view and drawn largest
rng = np.random.default_rng(42)
days = np.arange(60)
products = ["Alpha", "Beta", "Gamma"]
trend = pd.concat(
    [
        pd.DataFrame(
            {
                PANEL: "Sales Trend",
                X: days,
                Y: 100 + i * 15 + np.cumsum(rng.normal(0, 3, len(days))),
                GROUP: name,
                X_LABEL: "Day",
                Y_LABEL: "Sales (units)",
            }
        )
        for i, name in enumerate(products)
    ]
)

quarters = ["Q1", "Q2", "Q3", "Q4"]
quarterly = pd.DataFrame(
    {
        PANEL: "Quarterly Revenue",
        X: quarters,
        Y: [48, 35, 42, 55],
        GROUP: quarters,
        X_LABEL: "Quarter",
        Y_LABEL: "Revenue (k$)",
    }
)

units = rng.uniform(50, 400, 80)
margin = pd.DataFrame(
    {
        PANEL: "Margin Analysis",
        X: units,
        Y: 15 + rng.normal(0, 8, 80) + 0.03 * units,
        GROUP: "",
        X_LABEL: "Units sold",
        Y_LABEL: "Margin (%)",
    }
)

regions = ["North", "South", "East", "West"]
metrics = ["Sales", "Profit", "Growth"]
heat = pd.DataFrame(
    {
        PANEL: "Regional Heat",
        X: regions * len(metrics),
        Y: rng.uniform(0, 100, len(regions) * len(metrics)),
        GROUP: np.repeat(metrics, len(regions)),
        X_LABEL: "Region",
        Y_LABEL: "",
    }
)

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
perf = pd.DataFrame(
    {PANEL: "Performance", X: months, Y: [82, 78, 91, 88, 95, 92], GROUP: "", X_LABEL: "Month", Y_LABEL: "Score"}
)

df = pd.concat([trend, quarterly, margin, heat, perf], ignore_index=True)

# Plot: reads only df and the constants above
parts = [sub.drop(columns=PANEL) for _, sub in df.groupby(PANEL, sort=False)]
names = df[PANEL].unique().tolist()
p_trend, p_quarter, p_margin, p_heat, p_perf = parts


def axis_labels(sub, title):
    return labs(x=sub[X_LABEL].iloc[0], y=sub[Y_LABEL].iloc[0], title=title)


anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_blank(),
    axis_title=element_text(size=9, color=INK),
    axis_text=element_text(size=7.5, color=INK_SOFT),
    plot_title=element_text(size=10, color=INK, face="bold"),
    legend_background=element_rect(fill=PAGE_BG, color="none"),
    legend_text=element_text(size=7.5, color=INK_SOFT),
    legend_title=element_text(size=8.5, color=INK),
)

# Panel A: primary view, line plot with direct end labels instead of a legend
trend_num = p_trend.astype({X: float})
panel_a = (
    ggplot(trend_num, aes(x=X, y=Y, color=GROUP))
    + geom_line(size=1.0, show_legend=False)
    + geom_point(size=1.5, alpha=0.6, show_legend=False)
    + geom_text(
        trend_num.groupby(GROUP, sort=False).tail(1),
        aes(label=GROUP),
        ha="left",
        nudge_x=1.5,
        size=8,
        show_legend=False,
    )
    + scale_x_continuous(expand=(0.02, 0, 0.16, 0))
    + scale_color_manual(values=IMPRINT_PALETTE, limits=trend_num[GROUP].unique().tolist())
    + axis_labels(p_trend, names[0])
)

# Panel B: supporting bar chart
panel_b = (
    ggplot(p_quarter, aes(x=X, y=Y, fill=GROUP))
    + geom_col(width=0.7, show_legend=False)
    + scale_x_discrete(limits=p_quarter[X].unique().tolist())
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=p_quarter[GROUP].unique().tolist())
    + axis_labels(p_quarter, names[1])
)

# Panel C: scatter
panel_c = (
    ggplot(p_margin.astype({X: float}), aes(x=X, y=Y))
    + geom_point(size=1.8, color=IMPRINT_PALETTE[0], alpha=0.7)
    + axis_labels(p_margin, names[2])
)

# Panel D: heatmap
panel_d = (
    ggplot(p_heat, aes(x=X, y=GROUP, fill=Y))
    + geom_tile(show_legend=False, color=PAGE_BG, size=1.0)
    + geom_text(aes(label=Y), format_string="{:.0f}", size=7, color="#FFFFFF", show_legend=False)
    + scale_x_discrete(limits=p_heat[X].unique().tolist())
    + scale_y_discrete(limits=p_heat[GROUP].unique().tolist()[::-1])
    + scale_fill_gradient(low=IMPRINT_PALETTE[0], high=IMPRINT_PALETTE[2])
    + axis_labels(p_heat, names[3])
    + labs(y="")
)

# Panel E: supporting bar chart
panel_e = (
    ggplot(p_perf, aes(x=X, y=Y))
    + geom_col(fill=IMPRINT_PALETTE[0], width=0.6)
    + scale_x_discrete(limits=p_perf[X].unique().tolist())
    + axis_labels(p_perf, names[4])
)

# Mosaic: A spans the two columns that C and D share below it; B sits above E
headroom = theme(plot_margin_top=0.08)  # space above the top row for the figure title
left_col = (panel_a + headroom) / (panel_c | panel_d)
right_col = (panel_b + headroom) / panel_e
layout = (left_col | right_col) & anyplot_theme & theme(figure_size=(8, 4.5), dpi=400)

fig = layout.draw()
fig.set_facecolor(PAGE_BG)
fig.text(
    0.5,
    0.975,
    "subplot-mosaic · python · plotnine · anyplot.ai",
    ha="center",
    va="top",
    fontsize=13,
    fontweight="bold",
    color=INK,
)
fig.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
