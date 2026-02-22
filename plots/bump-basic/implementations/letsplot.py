"""pyplots.ai
bump-basic: Basic Bump Chart
Library: letsplot 4.8.2 | Python 3.14.3
Quality: /100 | Updated: 2026-02-22
"""

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_text,
    geom_line,
    geom_point,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_color_manual,
    scale_x_continuous,
    scale_y_reverse,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Data - Tech company rankings over 6 quarters
# Designed with dramatic crossovers: a rise-and-fall arc, a comeback story,
# volatile swaps in the middle, and a steady performer at the bottom
data = {
    "entity": (
        ["Alpha Corp"] * 6 + ["Beta Inc"] * 6 + ["Gamma Tech"] * 6 + ["Delta Systems"] * 6 + ["Epsilon Labs"] * 6
    ),
    "period": ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"] * 5,
    "period_num": [1, 2, 3, 4, 5, 6] * 5,
    "rank": [
        1,
        2,
        3,
        2,
        1,
        1,  # Alpha Corp - starts #1, drops mid-year, reclaims top
        3,
        1,
        1,
        3,
        4,
        5,  # Beta Inc - meteoric rise to #1, then collapses
        2,
        3,
        2,
        1,
        2,
        3,  # Gamma Tech - volatile, briefly reaches #1 in Q4
        4,
        4,
        5,
        4,
        3,
        2,  # Delta Systems - steady climber from bottom half
        5,
        5,
        4,
        5,
        5,
        4,  # Epsilon Labs - mostly bottom, slight improvement
    ],
}
df = pd.DataFrame(data)

# Subset for labels at end of lines
df_labels = df[df["period_num"] == 6].copy()

# Colors - Python Blue first, then colorblind-safe palette
colors = ["#306998", "#FFD43B", "#2CA02C", "#9467BD", "#E377C2"]

# Plot
plot = (
    ggplot(df, aes(x="period_num", y="rank", color="entity", group="entity"))
    + geom_line(size=2.5, alpha=0.85, tooltips=layer_tooltips().title("@entity").line("@|@period").line("Rank|@rank"))
    + geom_point(size=6, tooltips=layer_tooltips().title("@entity").line("@|@period").line("Rank|@rank"))
    + geom_text(aes(label="entity"), data=df_labels, nudge_x=0.35, hjust=0, size=11)
    + scale_y_reverse(breaks=[1, 2, 3, 4, 5])
    + scale_x_continuous(breaks=[1, 2, 3, 4, 5, 6], labels=["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"], limits=[0.5, 8.2])
    + scale_color_manual(values=colors)
    + labs(x="Quarter", y="Rank", title="bump-basic \u00b7 letsplot \u00b7 pyplots.ai")
    + theme_minimal()
    + theme(
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_position="none",
        axis_ticks=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x to get 4800 x 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML (interactive — tooltips show entity, period, and rank on hover)
ggsave(plot, "plot.html", path=".")
