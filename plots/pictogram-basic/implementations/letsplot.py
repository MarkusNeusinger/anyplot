""" pyplots.ai
pictogram-basic: Pictogram Chart (Isotype Visualization)
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-10
"""

from lets_plot import *


LetsPlot.setup_html()

# Data - Fruit production (thousands of tonnes)
categories = ["Apples", "Oranges", "Bananas", "Grapes", "Mangoes"]
values = [35, 22, 18, 12, 8]
icon_value = 5  # Each icon represents 5 thousand tonnes
max_icons = max(v // icon_value + (1 if v % icon_value else 0) for v in values)

# Build pictogram grid using numeric y positions
tile_data = {"category": [], "col": [], "row": [], "alpha": [], "value": []}

for i, (cat, val) in enumerate(zip(categories, values)):
    y_pos = len(categories) - 1 - i  # Highest value at top
    full_icons = int(val // icon_value)
    remainder = val % icon_value
    for c in range(full_icons):
        tile_data["category"].append(cat)
        tile_data["col"].append(float(c))
        tile_data["row"].append(float(y_pos))
        tile_data["alpha"].append(1.0)
        tile_data["value"].append(val)
    if remainder > 0:
        tile_data["category"].append(cat)
        tile_data["col"].append(float(full_icons))
        tile_data["row"].append(float(y_pos))
        tile_data["alpha"].append(remainder / icon_value)
        tile_data["value"].append(val)

# Value labels at end of each row for storytelling
label_data = {
    "col": [max_icons + 0.3] * len(categories),
    "row": [float(len(categories) - 1 - i) for i in range(len(categories))],
    "label": [f"{v}k tonnes" for v in values],
}

# Color palette per category
palette = ["#306998", "#E8843C", "#E8C53C", "#7B4F8B", "#3DAE6F"]

# Y-axis labels
y_breaks = [float(len(categories) - 1 - i) for i in range(len(categories))]

# Plot using geom_tile with tooltips for lets-plot interactivity
plot = (
    ggplot(tile_data, aes(x="col", y="row"))
    + geom_tile(
        aes(alpha="alpha", fill="category"),
        width=0.85,
        height=0.85,
        color="white",
        size=2,
        tooltips=layer_tooltips().line("@category").line("Total: @value thousand tonnes").format("@value", "d"),
    )
    + geom_text(
        aes(x="col", y="row", label="label"), data=label_data, size=18, color="#444444", hjust=0, fontface="bold"
    )
    + scale_alpha_identity()
    + scale_fill_manual(values=palette, limits=categories)
    + scale_y_continuous(breaks=y_breaks, labels=categories, expand=[0.08, 0])
    + scale_x_continuous(limits=[-0.6, max_icons + 2.8], expand=[0, 0])
    + labs(
        x="",
        y="",
        title="pictogram-basic · letsplot · pyplots.ai",
        subtitle="Fruit Production — Each square represents 5 thousand tonnes",
    )
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        plot_subtitle=element_text(size=20, color="#666666"),
        axis_title=element_blank(),
        axis_text_y=element_text(size=20, face="bold"),
        axis_text_x=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
        legend_position="none",
    )
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
