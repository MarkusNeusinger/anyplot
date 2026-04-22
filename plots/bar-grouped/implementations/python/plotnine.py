""" pyplots.ai
bar-grouped: Grouped Bar Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import pandas as pd
from plotnine import aes, element_text, geom_bar, ggplot, labs, position_dodge, scale_fill_manual, theme, theme_minimal


# Data - Quarterly revenue by product line
data = {
    "Quarter": ["Q1", "Q1", "Q1", "Q2", "Q2", "Q2", "Q3", "Q3", "Q3", "Q4", "Q4", "Q4"],
    "Product": [
        "Software",
        "Hardware",
        "Services",
        "Software",
        "Hardware",
        "Services",
        "Software",
        "Hardware",
        "Services",
        "Software",
        "Hardware",
        "Services",
    ],
    "Revenue": [120, 85, 45, 135, 92, 52, 148, 78, 61, 165, 88, 70],
}
df = pd.DataFrame(data)

# Define colors - Python Blue and Yellow, plus a complementary color
colors = ["#306998", "#FFD43B", "#4B8BBE"]

# Create grouped bar chart
plot = (
    ggplot(df, aes(x="Quarter", y="Revenue", fill="Product"))
    + geom_bar(stat="identity", position=position_dodge(width=0.8), width=0.7)
    + scale_fill_manual(values=colors)
    + labs(x="Quarter", y="Revenue ($ millions)", title="bar-grouped · plotnine · pyplots.ai", fill="Product Line")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
    )
)

# Save
plot.save("plot.png", dpi=300)
