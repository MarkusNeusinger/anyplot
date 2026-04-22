""" pyplots.ai
pictogram-basic: Pictogram Chart (Isotype Visualization)
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-10
"""

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_text,
    geom_text,
    geom_tile,
    ggplot,
    guide_legend,
    labs,
    scale_color_identity,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_discrete,
    theme,
    theme_void,
)


# Data: Fruit production (thousands of tonnes) — sorted by value for visual hierarchy
categories = ["Apples", "Grapes", "Oranges", "Bananas", "Strawberries"]
values = [35, 28, 22, 18, 12]
unit_value = 5  # Each icon = 5 thousand tonnes

# Colorblind-safe palette (well-separated hues, starts with Python Blue)
fruit_colors = {
    "Apples": "#306998",  # Python Blue
    "Grapes": "#8E44AD",  # Purple
    "Oranges": "#E67E22",  # Orange
    "Bananas": "#27AE60",  # Green (distinct from orange for colorblind safety)
    "Strawberries": "#C0392B",  # Dark red
}

# Tile dimensions
tile_w, tile_h = 0.82, 0.70

# Build icon tiles: full icons + partial icons (half-filled approach)
cat_order = categories[::-1]  # highest value at top

tile_rows = []

for cat, val in zip(categories, values, strict=True):
    full_icons = val // unit_value
    remainder = val % unit_value
    color = fruit_colors[cat]

    # Full icon tiles
    for i in range(full_icons):
        tile_rows.append({"category": cat, "col": i + 1, "border": "none", "width": tile_w, "layer": "full"})

    # Partial icon: background outline (dashed border) + left-aligned fill
    if remainder > 0:
        px = full_icons + 1
        frac = remainder / unit_value
        # Outline tile (dashed border in category color, tinted fill)
        tile_rows.append({"category": cat, "col": px, "border": color, "width": tile_w, "layer": "outline"})
        # Filled portion — shifted left so it fills from the left edge
        filled_w = tile_w * frac
        offset = (tile_w - filled_w) / 2  # shift left
        tile_rows.append(
            {"category": cat, "col": px - offset, "border": "none", "width": filled_w, "layer": "partial_fill"}
        )

df = pd.DataFrame(tile_rows)
df["category"] = pd.Categorical(df["category"], categories=cat_order, ordered=True)

# Separate layers for correct z-ordering
df_full = df[df["layer"] == "full"].copy()
df_outline = df[df["layer"] == "outline"].copy()
df_partial = df[df["layer"] == "partial_fill"].copy()

# Value labels at end of each row
max_cols = {
    cat: (val // unit_value) + (1 if val % unit_value > 0 else 0) for cat, val in zip(categories, values, strict=True)
}
label_df = pd.DataFrame(
    {
        "category": pd.Categorical(categories, categories=cat_order, ordered=True),
        "col": [max_cols[c] + 0.7 for c in categories],
        "label": [f"{v}k" for v in values],
    }
)

# Dynamic x-axis limit
x_max = max(max_cols.values()) + 2.0

# Build plot with layered grammar of graphics — fill mapped to category via scale_fill_manual
plot = (
    ggplot(df_full, aes(x="col", y="category"))
    # Layer 1: Full icon tiles — fill mapped to category (grammar-of-graphics aesthetic mapping)
    + geom_tile(aes(fill="category"), width=tile_w, height=tile_h)
    # Layer 2: Partial icon outline (dashed border, tinted category fill at low alpha)
    + geom_tile(
        aes(fill="category", color="border"),
        data=df_outline,
        height=tile_h,
        width=tile_w,
        alpha=0.2,
        linetype="dashed",
        size=0.6,
        show_legend=False,
    )
    # Layer 3: Partial icon fill (left-aligned filled portion)
    + geom_tile(aes(fill="category", width="width"), data=df_partial, height=tile_h, show_legend=False)
    # Layer 4: Value labels
    + geom_text(
        aes(x="col", y="category", label="label"), data=label_df, size=16, color="#444444", ha="left", fontweight="bold"
    )
    # Grammar-of-graphics scales: category-mapped fill with structured guide_legend
    + scale_fill_manual(
        name="Each \u25a0", values=fruit_colors, breaks=["Apples"], labels=["= 5k tonnes"], guide=guide_legend(nrow=1)
    )
    + scale_color_identity()
    + scale_x_continuous(limits=(0.3, x_max), expand=(0, 0))
    + scale_y_discrete(expand=(0.2, 0.15))
    # Labels
    + labs(
        x="",
        y="",
        title="pictogram-basic \u00b7 plotnine \u00b7 pyplots.ai",
        caption="Partial squares show fractional units  \u00b7  Source: FAO estimates",
    )
    # Clean infographic theme
    + theme_void()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=26, weight="bold", margin={"b": 20}),
        plot_caption=element_text(size=14, color="#777777", ha="left", margin={"t": 18}),
        axis_text_y=element_text(size=20, color="#333333", ha="right", margin={"r": 14}),
        axis_text_x=element_blank(),
        legend_position="bottom",
        legend_title=element_text(size=14, weight="bold", color="#555555"),
        legend_text=element_text(size=14, color="#555555"),
        plot_margin=0.06,
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
