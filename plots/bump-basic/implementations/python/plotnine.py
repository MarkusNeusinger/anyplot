""" pyplots.ai
bump-basic: Basic Bump Chart
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 94/100 | Updated: 2026-02-22
"""

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_reverse,
    theme,
    theme_minimal,
)


# Data - Streaming platform market share rankings over 8 quarters
platforms = ["StreamVue", "WavePlay", "CloudCast", "PixelFlix", "SonicNet", "EchoTV"]
quarters = ["Q1'24", "Q2'24", "Q3'24", "Q4'24", "Q1'25", "Q2'25", "Q3'25", "Q4'25"]
n_periods = len(quarters)

rankings = {
    "StreamVue": [1, 1, 1, 2, 2, 3, 3, 4],
    "WavePlay": [2, 3, 3, 1, 1, 1, 1, 1],
    "CloudCast": [4, 2, 2, 3, 3, 2, 2, 2],
    "PixelFlix": [3, 4, 4, 4, 5, 5, 4, 3],
    "SonicNet": [5, 5, 5, 5, 4, 4, 5, 5],
    "EchoTV": [6, 6, 6, 6, 6, 6, 6, 6],
}

rows = []
for platform, ranks in rankings.items():
    for i, rank in enumerate(ranks):
        rows.append({"platform": platform, "quarter": quarters[i], "qnum": i + 1, "rank": rank})
df = pd.DataFrame(rows)

# Subset for end labels
df_end = df[df["qnum"] == n_periods].copy()

# Visual hierarchy: protagonist entities vs supporting cast
protagonists = ["StreamVue", "WavePlay"]
supporting = ["CloudCast", "PixelFlix", "SonicNet", "EchoTV"]

df_hero = df[df["platform"].isin(protagonists)]
df_support = df[df["platform"].isin(supporting)]

# Crossover emphasis at Q4'24 (qnum=4) where WavePlay overtakes StreamVue
df_crossover = pd.DataFrame(
    [{"qnum": 4, "rank": 1, "platform": "WavePlay"}, {"qnum": 4, "rank": 2, "platform": "StreamVue"}]
)

# Colorblind-safe palette — Python Blue first, warm orange for WavePlay
# Replaced red with teal (#17becf) for deuteranopia safety
palette = {
    "StreamVue": "#306998",
    "WavePlay": "#e8963e",
    "CloudCast": "#59a14f",
    "PixelFlix": "#17becf",
    "SonicNet": "#9d7660",
    "EchoTV": "#bab0ac",
}

# Plot — layered for visual hierarchy
plot = (
    ggplot(df, aes(x="qnum", y="rank", color="platform", group="platform"))
    # Supporting lines: thinner, more transparent
    + geom_line(data=df_support, size=1.8, alpha=0.4)
    + geom_point(data=df_support, size=4, stroke=0.6, fill="white")
    + geom_point(data=df_support, size=2.5, alpha=0.5)
    # Protagonist lines: bold and saturated
    + geom_line(data=df_hero, size=3.5, alpha=0.95)
    + geom_point(data=df_hero, size=7, stroke=1.0, fill="white")
    + geom_point(data=df_hero, size=4.5)
    # Crossover emphasis at Q4'24
    + geom_point(data=df_crossover, size=12, alpha=0.15)
    # End labels — bold for protagonists, italic for supporting
    + geom_text(
        aes(label="platform"),
        data=df_end[df_end["platform"].isin(protagonists)],
        nudge_x=0.35,
        ha="left",
        size=13,
        fontweight="bold",
    )
    + geom_text(
        aes(label="platform"),
        data=df_end[df_end["platform"].isin(supporting)],
        nudge_x=0.35,
        ha="left",
        size=11,
        fontstyle="italic",
        alpha=0.7,
    )
    + scale_y_reverse(breaks=range(1, len(platforms) + 1))
    + scale_x_continuous(breaks=range(1, n_periods + 1), labels=quarters, limits=(0.5, n_periods + 2))
    + scale_color_manual(values=palette)
    + labs(x="Quarter", y="Market Share Ranking", title="bump-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, color="#3c3c3c"),
        axis_title=element_text(size=20, color="#555555"),
        axis_text=element_text(size=16, color="#666666"),
        axis_text_x=element_text(rotation=0),
        plot_title=element_text(size=24, weight="bold", color="#2b2b2b"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(alpha=0.15, size=0.4, color="#cccccc"),
        panel_background=element_rect(fill="white", color="none"),
        plot_background=element_rect(fill="#fafafa", color="none"),
        legend_position="none",
    )
)

plot.save("plot.png", dpi=300)
