""" pyplots.ai
bar-basic: Basic Bar Chart
Library: plotnine 0.15.3 | Python 3.14
Quality: 91/100 | Created: 2025-12-23
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
    geom_bar,
    geom_text,
    ggplot,
    guides,
    labs,
    scale_fill_manual,
    scale_x_discrete,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data — non-monotonic: Clothing and Home & Garden are close rivals
data = pd.DataFrame(
    {
        "category": ["Electronics", "Clothing", "Home & Garden", "Sports", "Books", "Toys"],
        "value": [45200, 31400, 30800, 19700, 15300, 12400],
    }
)
data["category"] = pd.Categorical(
    data["category"], categories=data.sort_values("value", ascending=False)["category"], ordered=True
)

# Highlight the leading category
data["highlight"] = data["value"] == data["value"].max()

# Annotation: how far ahead is the leader
top_val = data["value"].max()
second_val = data["value"].nlargest(2).iloc[1]
lead_pct = (top_val - second_val) / second_val * 100

# Value label formatting via mapped column (plotnine-idiomatic)
data["label"] = data["value"].apply(lambda v: f"${v:,.0f}")

# Plot
plot = (
    ggplot(data, aes(x="category", y="value", fill="highlight"))
    + geom_bar(stat="identity", width=0.7, show_legend=False)
    + scale_fill_manual(values={True: "#306998", False: "#7BA7C9"})
    + guides(fill="none")
    # Value labels using a pre-formatted column with position nudge
    + geom_text(aes(label="label"), va="bottom", size=14, nudge_y=600)
    # Annotation placed over the leading bar, right-aligned to avoid y-axis crowding
    + annotate(
        "text",
        x=1.5,
        y=top_val - 3000,
        label=f"▲ {lead_pct:.0f}% ahead of 2nd place",
        size=11,
        color="#1a3a5c",
        fontstyle="italic",
        ha="left",
    )
    # Use coord_cartesian for clipping instead of scale limits (plotnine-idiomatic)
    + scale_y_continuous(
        labels=lambda vals: [f"${v / 1000:.0f}K" for v in vals], breaks=range(0, 55000, 10000), expand=(0, 0, 0.08, 0)
    )
    + scale_x_discrete(expand=(0.05, 0.6))
    + coord_cartesian(ylim=(0, None))
    + labs(x="Product Category", y="Sales (USD)", title="bar-basic · plotnine · pyplots.ai")
    + theme_minimal(base_size=14, base_family="sans-serif")
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", margin={"b": 15}),
        axis_title_x=element_text(size=20, margin={"t": 12}),
        axis_title_y=element_text(size=20, margin={"r": 12}),
        axis_text=element_text(size=16, color="#333333"),
        axis_text_x=element_text(rotation=0, ha="center"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(alpha=0.15, size=0.4, color="#999999"),
        panel_spacing=0.15,
        axis_ticks=element_blank(),
        plot_background=element_rect(fill="white", color="white"),
        panel_background=element_rect(fill="white", color="white"),
        plot_margin=0.02,
    )
)

# Save
plot.save("plot.png", dpi=300)
