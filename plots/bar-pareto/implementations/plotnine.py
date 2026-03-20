""" pyplots.ai
bar-pareto: Pareto Chart with Cumulative Line
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-20
"""

import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_bar,
    geom_hline,
    geom_line,
    geom_point,
    geom_text,
    ggplot,
    labs,
    scale_x_discrete,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data — manufacturing defect types sorted by frequency
categories = [
    "Scratches",
    "Dents",
    "Misalignment",
    "Cracks",
    "Discoloration",
    "Burrs",
    "Warping",
    "Contamination",
    "Chipping",
    "Porosity",
]
counts = [186, 145, 112, 87, 64, 43, 29, 18, 11, 5]

df = pd.DataFrame({"category": categories, "count": counts})
df = df.sort_values("count", ascending=False).reset_index(drop=True)
df["category"] = pd.Categorical(df["category"], categories=df["category"], ordered=True)

# Cumulative percentage scaled to primary y-axis
total = df["count"].sum()
df["cum_pct"] = df["count"].cumsum() / total * 100
max_count = df["count"].max()
scale_factor = max_count / 100
df["cum_scaled"] = df["cum_pct"] * scale_factor

# Labels for cumulative percentage on each point
df["pct_label"] = df["cum_pct"].apply(lambda v: f"{v:.0f}%")

y_max = max_count * 1.1

# Plot
plot = (
    ggplot(df, aes(x="category"))
    + geom_bar(aes(y="count"), stat="identity", fill="#306998", width=0.7)
    + geom_line(aes(y="cum_scaled", group=1), color="#E85D3A", size=1.5)
    + geom_point(aes(y="cum_scaled"), color="#E85D3A", size=4, fill="white", stroke=1.5)
    # Percentage labels on cumulative line
    + geom_text(aes(y="cum_scaled", label="pct_label"), size=10, va="bottom", nudge_y=6, color="#C04422")
    # 80% threshold reference line
    + geom_hline(yintercept=80 * scale_factor, linetype="dashed", color="#999999", size=0.8)
    + annotate(
        "text", x=10.5, y=80 * scale_factor + 4, label="80%", size=11, color="#777777", ha="right", fontweight="bold"
    )
    + scale_y_continuous(name="Defect Count", expand=(0, 0, 0.08, 0), limits=(0, y_max))
    + scale_x_discrete(expand=(0.05, 0.6))
    + labs(x="Defect Type", title="bar-pareto · plotnine · pyplots.ai")
    + theme_minimal(base_size=14)
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", margin={"b": 15}),
        axis_title_x=element_text(size=20, margin={"t": 12}),
        axis_title_y=element_text(size=20, margin={"r": 12}),
        axis_text=element_text(size=16, color="#333333"),
        axis_text_x=element_text(rotation=30, ha="right"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(alpha=0.15, size=0.4, color="#999999"),
        axis_ticks=element_blank(),
        plot_background=element_rect(fill="white", color="white"),
        panel_background=element_rect(fill="white", color="white"),
        plot_margin=0.02,
    )
)

# Save
plot.save("plot.png", dpi=300)
