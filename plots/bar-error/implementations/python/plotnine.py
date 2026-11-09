"""anyplot.ai
bar-error: Bar Chart with Error Bars
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
"""

import os

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_col,
    geom_errorbar,
    ggplot,
    labs,
    scale_x_discrete,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # Imprint palette position 1 — a single-series plot uses it alone

# Columns: set these to your table's column names
SURVEY_CATEGORY = "Survey category"  # role: category
SATISFACTION = "Satisfaction score (1–5)"  # role: value
MARGIN = "95% CI half-width"  # role: error

# Data: replace this block with your own table, for example df = pd.read_csv("survey.csv")
df = pd.DataFrame(
    {
        SURVEY_CATEGORY: [
            "Product Quality",
            "Customer Service",
            "Delivery Speed",
            "Price Value",
            "Website UX",
            "Return Policy",
        ],
        SATISFACTION: [4.2, 3.8, 4.5, 3.5, 4.0, 4.3],
        MARGIN: [0.3, 0.4, 0.2, 0.5, 0.35, 0.25],
    }
)

# Plot: reads only df and the constants above
bounds = df.assign(lower=df[SATISFACTION] - df[MARGIN], upper=df[SATISFACTION] + df[MARGIN])
order = df.sort_values(SATISFACTION, ascending=False)[SURVEY_CATEGORY].tolist()

plot = (
    ggplot(bounds, aes(x=SURVEY_CATEGORY, y=SATISFACTION))
    + geom_col(fill=BRAND, width=0.65)
    + geom_errorbar(aes(ymin="lower", ymax="upper"), width=0.22, size=0.8, color=INK)
    + scale_x_discrete(limits=order)
    + scale_y_continuous(limits=(0, None), expand=(0, 0, 0.06, 0))
    + labs(title="bar-error · python · plotnine · anyplot.ai", caption=f"Error bars: ± {MARGIN}")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.12),
        axis_line_x=element_line(color=INK_SOFT, size=0.5),
        axis_ticks=element_blank(),
        plot_title=element_text(size=12, weight="bold", color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_caption=element_text(size=8, style="italic", color=INK_MUTED),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
