""" pyplots.ai
lollipop-basic: Basic Lollipop Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import pandas as pd
from plotnine import aes, element_line, element_text, geom_point, geom_segment, ggplot, labs, theme, theme_minimal


# Data - Product sales by category, sorted by value
data = {
    "category": [
        "Electronics",
        "Furniture",
        "Clothing",
        "Groceries",
        "Sports",
        "Books",
        "Toys",
        "Beauty",
        "Garden",
        "Automotive",
    ],
    "value": [245, 198, 176, 152, 134, 118, 95, 87, 72, 58],
}

df = pd.DataFrame(data)
df = df.sort_values("value", ascending=True).reset_index(drop=True)
df["category"] = pd.Categorical(df["category"], categories=df["category"], ordered=True)

# Plot
plot = (
    ggplot(df, aes(x="category", y="value"))
    # Stems - thin lines from baseline to value
    + geom_segment(aes(x="category", xend="category", y=0, yend="value"), color="#306998", size=1.5)
    # Circular markers at data values
    + geom_point(color="#306998", size=6, fill="#306998")
    + labs(x="Product Category", y="Sales (thousands $)", title="lollipop-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        axis_text_x=element_text(angle=45, ha="right"),
        plot_title=element_text(size=24),
        panel_grid_minor=element_line(alpha=0),
        panel_grid_major_x=element_line(alpha=0),
        panel_grid_major_y=element_line(alpha=0.3, linetype="dashed"),
    )
)

plot.save("plot.png", dpi=300)
