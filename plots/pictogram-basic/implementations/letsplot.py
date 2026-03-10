"""pyplots.ai
pictogram-basic: Pictogram Chart (Isotype Visualization)
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-10
"""

from lets_plot import *


LetsPlot.setup_html()

# Data - Fruit production (thousands of tonnes)
categories = ["Apples", "Oranges", "Bananas", "Grapes", "Mangoes"]
values = [35, 22, 18, 12, 8]
colors = ["#306998", "#E8843C", "#E8C53C", "#7B4F8B", "#3DAE6F"]
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

# Alternating background lanes for visual rhythm (even rows)
even_lanes = {
    "ymin": [float(len(categories) - 1 - i) - 0.48 for i in range(len(categories)) if i % 2 == 0],
    "ymax": [float(len(categories) - 1 - i) + 0.48 for i in range(len(categories)) if i % 2 == 0],
}

# Value labels at end of each row
label_data = {
    "col": [max_icons + 0.3] * len(categories),
    "row": [float(len(categories) - 1 - i) for i in range(len(categories))],
    "label": [f"{v}k tonnes" for v in values],
}

# Top producer annotation for storytelling emphasis
anno_data = {"col": [max_icons + 0.3], "row": [float(len(categories) - 1) + 0.38], "label": ["\u2605 Top producer"]}

# Y-axis labels
y_breaks = [float(len(categories) - 1 - i) for i in range(len(categories))]

# Plot with layered composition for visual depth
plot = (
    ggplot()
    # Subtle alternating row bands for readability
    + geom_rect(aes(ymin="ymin", ymax="ymax"), data=even_lanes, xmin=-0.6, xmax=max_icons + 2.2, fill="#f0f0f0", size=0)
    # Main pictogram tiles with interactive tooltips
    + geom_tile(
        aes(x="col", y="row", alpha="alpha", fill="category"),
        data=tile_data,
        width=0.82,
        height=0.82,
        color="white",
        size=2.5,
        tooltips=layer_tooltips().line("@category").line("Total: @value thousand tonnes").format("@value", "d"),
    )
    + scale_alpha_identity()
    + scale_fill_manual(values=colors, limits=categories)
    # Value labels (20pt for optimal legibility)
    + geom_text(
        aes(x="col", y="row", label="label"), data=label_data, size=20, color="#333333", hjust=0, fontface="bold"
    )
    # Top producer annotation for data storytelling
    + geom_text(
        aes(x="col", y="row", label="label"), data=anno_data, size=16, color="#306998", hjust=0, fontface="italic"
    )
    + scale_y_continuous(breaks=y_breaks, labels=categories, limits=[-0.6, len(categories) - 0.3], expand=[0, 0])
    + scale_x_continuous(limits=[-0.6, max_icons + 2.3], expand=[0, 0])
    + labs(
        x="",
        y="",
        title="pictogram-basic \u00b7 letsplot \u00b7 pyplots.ai",
        subtitle="Fruit Production \u2014 Each square represents 5 thousand tonnes",
    )
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold", color="#222222"),
        plot_subtitle=element_text(size=20, color="#666666"),
        axis_title=element_blank(),
        axis_text_y=element_text(size=20, face="bold", color="#333333"),
        axis_text_x=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
        legend_position="none",
        plot_background=element_rect(fill="white", color="white", size=0),
        panel_background=element_rect(fill="white", color="white", size=0),
    )
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
