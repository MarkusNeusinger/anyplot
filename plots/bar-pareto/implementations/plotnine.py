""" pyplots.ai
bar-pareto: Pareto Chart with Cumulative Line
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-20
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
    scale_fill_manual,
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

# Vital few (contribute to first 80%) vs useful many
df["vital"] = df["cum_pct"].shift(1, fill_value=0) < 80
df["bar_fill"] = df["vital"].map({True: "vital", False: "useful"})

# Labels for cumulative percentage
df["pct_label"] = df["cum_pct"].apply(lambda v: f"{v:.0f}%")

y_max = max_count * 1.12

# Plot
plot = (
    ggplot(df, aes(x="category"))
    + geom_bar(aes(y="count", fill="bar_fill"), stat="identity", width=0.7)
    + scale_fill_manual(values={"vital": "#306998", "useful": "#A8C4D9"})
    + geom_line(aes(y="cum_scaled", group=1), color="#E85D3A", size=1.5)
    + geom_point(aes(y="cum_scaled"), color="#E85D3A", size=4, fill="white", stroke=1.5)
    # Percentage labels on cumulative line
    + geom_text(
        aes(y="cum_scaled", label="pct_label"), size=9, va="bottom", nudge_y=6, color="#C04422", fontweight="bold"
    )
    # 80% threshold reference line
    + geom_hline(yintercept=80 * scale_factor, linetype="dashed", color="#999999", size=0.8)
    + annotate(
        "text",
        x=0.5,
        y=80 * scale_factor + 5,
        label="80% threshold",
        size=10,
        color="#777777",
        ha="left",
        fontweight="bold",
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
        legend_position="none",
        plot_margin=0.02,
    )
)

# Draw to matplotlib figure, then add secondary y-axis for cumulative %
fig = plot.draw()
ax = fig.axes[0]

ax2 = ax.twinx()
ax2.set_ylim(0, y_max / scale_factor)
ax2.set_ylabel("Cumulative %", fontsize=20, color="#333333")
ax2.set_yticks([0, 20, 40, 60, 80, 100])
ax2.set_yticklabels([f"{t}%" for t in [0, 20, 40, 60, 80, 100]], fontsize=16, color="#333333")
ax2.tick_params(axis="y", length=0)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
ax2.spines["left"].set_visible(False)
ax2.spines["bottom"].set_visible(False)

# Save
fig.savefig("plot.png", dpi=300, bbox_inches="tight")
