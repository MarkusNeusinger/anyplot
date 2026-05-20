""" anyplot.ai
bar-drilldown: Column Chart with Hierarchical Drilling
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 82/100 | Created: 2026-05-20
"""

import os

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    facet_wrap,
    geom_col,
    geom_text,
    ggplot,
    labs,
    scale_fill_manual,
    scale_y_continuous,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data — Annual retail revenue by category and subcategory ($ millions)
data = {
    "category": (["Electronics"] * 4 + ["Apparel"] * 4 + ["Groceries"] * 4 + ["Sports"] * 4),
    "subcategory": [
        "Phones",
        "Laptops",
        "Tablets",
        "Cameras",
        "Tops",
        "Bottoms",
        "Jackets",
        "Footwear",
        "Beverages",
        "Produce",
        "Dairy",
        "Snacks",
        "Fitness",
        "Outdoor",
        "Team",
        "Aquatics",
    ],
    "revenue": [45, 38, 23, 14, 29, 21, 18, 12, 22, 19, 16, 13, 20, 17, 11, 9],
}

df = pd.DataFrame(data)

cat_order = ["Electronics", "Apparel", "Groceries", "Sports"]
df["category"] = pd.Categorical(df["category"], categories=cat_order, ordered=True)

global_order = df.sort_values("revenue", ascending=False)["subcategory"].tolist()
df["subcategory"] = pd.Categorical(df["subcategory"], categories=global_order, ordered=True)

# Strip labels include category total — L1 summary visible alongside L2 breakdown
cat_totals = df.groupby("category", observed=True)["revenue"].sum().to_dict()
label_order = [f"{c}  ·  ${cat_totals[c]}M total" for c in cat_order]
df["panel_label"] = pd.Categorical(
    [f"{c}  ·  ${cat_totals[str(c)]}M total" for c in df["category"]], categories=label_order, ordered=True
)

plot = (
    ggplot(df, aes(x="subcategory", y="revenue", fill="category"))
    + geom_col(width=0.72)
    + geom_text(aes(label="revenue"), va="bottom", nudge_y=0.5, size=9, color=INK_SOFT)
    + facet_wrap("~panel_label", ncol=2, scales="free")
    + scale_fill_manual(values=OKABE_ITO)
    + scale_y_continuous(expand=(0.08, 0))
    + labs(x="", y="Revenue ($ millions)", title="bar-drilldown · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(6, 6),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        legend_position="none",
        axis_title=element_text(color=INK, size=10),
        axis_text=element_text(color=INK_SOFT, size=8),
        plot_title=element_text(color=INK, size=12),
        strip_background=element_rect(fill=ELEVATED_BG, color="none"),
        strip_text=element_text(color=INK, size=9, face="bold"),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in")
