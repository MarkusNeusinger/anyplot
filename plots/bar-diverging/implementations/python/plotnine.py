""" pyplots.ai
bar-diverging: Diverging Bar Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-25
"""

import pandas as pd
from plotnine import (
    aes,
    coord_flip,
    element_line,
    element_text,
    geom_bar,
    geom_hline,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Data - Customer satisfaction survey across product categories
# Net satisfaction score: % satisfied - % dissatisfied (range -100 to +100)
categories = [
    "Mobile App",
    "Customer Service",
    "Website",
    "Delivery Speed",
    "Product Quality",
    "Pricing",
    "Return Policy",
    "Packaging",
    "Email Support",
    "Chat Support",
    "Documentation",
    "Warranty",
]

values = [72, 45, 38, 25, 18, 8, -5, -12, -22, -35, -48, -62]

df = pd.DataFrame({"category": categories, "value": values})

# Sort by value for better pattern recognition
df = df.sort_values("value", ascending=True).reset_index(drop=True)

# Create ordered categorical for proper sorting in plot
df["category"] = pd.Categorical(df["category"], categories=df["category"], ordered=True)

# Color based on positive/negative
df["sentiment"] = df["value"].apply(lambda x: "Positive" if x >= 0 else "Negative")

# Plot
plot = (
    ggplot(df, aes(x="category", y="value", fill="sentiment"))
    + geom_bar(stat="identity", width=0.7)
    + geom_hline(yintercept=0, color="#333333", size=0.8)
    + coord_flip()
    + scale_fill_manual(values={"Positive": "#306998", "Negative": "#E74C3C"})
    + labs(
        x="Product Category",
        y="Net Satisfaction Score (%)",
        title="bar-diverging · plotnine · pyplots.ai",
        fill="Sentiment",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24, ha="center"),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_position="right",
        panel_grid_major_y=element_line(alpha=0.3),
        panel_grid_minor=element_line(alpha=0),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
