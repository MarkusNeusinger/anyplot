"""pyplots.ai
pictogram-basic: Pictogram Chart (Isotype Visualization)
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-03-10
"""

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_text,
    geom_point,
    ggplot,
    labs,
    scale_alpha_identity,
    scale_x_continuous,
    theme,
    theme_minimal,
)


# Data: Fruit production (thousands of tonnes)
categories = ["Apples", "Oranges", "Bananas", "Grapes", "Strawberries"]
values = [35, 22, 18, 28, 12]
unit_value = 5  # Each icon = 5 thousand tonnes

# Expand data into one row per icon position
rows = []
for cat, val in zip(categories, values, strict=True):
    full_icons = val // unit_value
    remainder = val % unit_value
    for i in range(full_icons):
        rows.append({"category": cat, "col": i + 1, "alpha": 1.0})
    if remainder > 0:
        rows.append({"category": cat, "col": full_icons + 1, "alpha": remainder / unit_value})

df = pd.DataFrame(rows)
df["category"] = pd.Categorical(df["category"], categories=categories[::-1], ordered=True)

# Plot
plot = (
    ggplot(df, aes(x="col", y="category", alpha="alpha"))
    + geom_point(size=12, color="#306998", shape="s")
    + scale_alpha_identity()
    + scale_x_continuous(limits=(0.5, 8.5), breaks=range(1, 9))
    + labs(
        x="",
        y="",
        title="Fruit Production · pictogram-basic · plotnine · pyplots.ai",
        caption="Each square = 5 thousand tonnes | Faded = partial unit",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        plot_caption=element_text(size=14, color="#666666"),
        axis_text_y=element_text(size=18),
        axis_text_x=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
