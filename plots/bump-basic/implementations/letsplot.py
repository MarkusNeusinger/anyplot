"""pyplots.ai
bump-basic: Basic Bump Chart
Library: letsplot 4.8.2 | Python 3.14.3
"""

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
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

# Cohesive muted palette — Python Blue anchors, warm/cool balance
colors = ["#306998", "#C47D2A", "#3A9E78", "#8B6AAE", "#D4707A"]

# Hero entity (Beta Inc) has the most dramatic arc — highlight it
df_hero = df[df["entity"] == "Beta Inc"]
df_rest = df[df["entity"] != "Beta Inc"]

# Plot — layered: background lines, then hero emphasis
tooltip_cfg = layer_tooltips().title("@entity").line("@|@period").line("Rank|@rank")

plot = (
    ggplot(df_rest, aes(x="period_num", y="rank", color="entity", group="entity"))
    # Background lines — thinner, slightly transparent
    + geom_line(size=2.0, alpha=0.55, tooltips=tooltip_cfg)
    + geom_point(size=5, alpha=0.65, tooltips=tooltip_cfg)
    # Hero line — Beta Inc's dramatic rise-and-fall stands out
    + geom_line(
        aes(x="period_num", y="rank", color="entity", group="entity"),
        data=df_hero,
        size=3.5,
        alpha=1.0,
        tooltips=tooltip_cfg,
    )
    + geom_point(
        aes(x="period_num", y="rank", color="entity", group="entity"),
        data=df_hero,
        size=8,
        alpha=1.0,
        tooltips=tooltip_cfg,
    )
    # End-of-line entity labels
    + geom_text(aes(label="entity"), data=df_labels, nudge_x=0.3, hjust=0, size=12)
    + scale_y_reverse(breaks=[1, 2, 3, 4, 5])
    + scale_x_continuous(breaks=[1, 2, 3, 4, 5, 6], labels=["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"], limits=[0.5, 7.8])
    + scale_color_manual(values=colors)
    + labs(x="Quarterly Period", y="Market Rank Position", title="bump-basic · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_position="none",
        axis_ticks=element_blank(),
        # Subtle y-axis grid only — remove x-axis grid for cleaner look
        panel_grid_major_x=element_blank(),
        panel_grid_minor_x=element_blank(),
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.5),
        panel_grid_minor_y=element_blank(),
        plot_background=element_rect(fill="white", color="white"),
        # Generous margins
        plot_margin=[40, 60, 30, 20],
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x to get 4800 x 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML (interactive — tooltips show entity, period, and rank on hover)
ggsave(plot, "plot.html", path=".")
