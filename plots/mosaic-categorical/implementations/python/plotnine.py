"""anyplot.ai
mosaic-categorical: Mosaic Plot for Categorical Association Analysis
Library: plotnine | Python 3.13
Quality: 91/100 | Updated: 2026-05-19
"""

import os

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_rect,
    geom_text,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

# Data - Titanic-style survival data by passenger class
data = {
    "class": ["First", "First", "Second", "Second", "Third", "Third"],
    "survival": ["Survived", "Did Not Survive", "Survived", "Did Not Survive", "Survived", "Did Not Survive"],
    "count": [203, 122, 118, 167, 178, 528],
}
df = pd.DataFrame(data)
survival_order = ["Survived", "Did Not Survive"]

# Calculate proportions for mosaic plot
total = df["count"].sum()

# Calculate widths (proportional to class totals)
class_totals = df.groupby("class")["count"].sum()
class_order = ["First", "Second", "Third"]
widths = {c: class_totals[c] / total for c in class_order}

# Build rectangles for mosaic plot
gap = 0.02
rects = []
x_pos = 0

for cls in class_order:
    class_data = df[df["class"] == cls]
    class_total = class_data["count"].sum()
    width = widths[cls] - gap

    y_pos = 0
    for surv in survival_order:
        row = class_data[class_data["survival"] == surv].iloc[0]
        height = (row["count"] / class_total) * (1 - gap)
        rects.append(
            {
                "xmin": x_pos,
                "xmax": x_pos + width,
                "ymin": y_pos,
                "ymax": y_pos + height,
                "class": cls,
                "survival": row["survival"],
                "count": row["count"],
                "x_center": x_pos + width / 2,
                "y_center": y_pos + height / 2,
            }
        )
        y_pos += height + gap / 2

    x_pos += widths[cls]

rect_df = pd.DataFrame(rects)

# Colors - Okabe-Ito: green for Survived (first series), vermillion for Did Not Survive
colors = {"Survived": OKABE_ITO[0], "Did Not Survive": OKABE_ITO[1]}

# Class labels positioned below plot area
class_labels = pd.DataFrame(
    {
        "x": [
            widths["First"] / 2,
            widths["First"] + widths["Second"] / 2,
            widths["First"] + widths["Second"] + widths["Third"] / 2,
        ],
        "y": [-0.06, -0.06, -0.06],
        "label": class_order,
    }
)

# Plot
plot = (
    ggplot(rect_df)
    + geom_rect(aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="survival"), color=PAGE_BG, size=1.5)
    + geom_text(aes(x="x_center", y="y_center", label="count"), color="white", size=14, fontweight="bold")
    + geom_text(data=class_labels, mapping=aes(x="x", y="y", label="label"), size=14, color=INK_SOFT, fontweight="bold")
    + scale_fill_manual(values=colors)
    + labs(
        title="mosaic-categorical · python · plotnine · anyplot.ai",
        x="Passenger Class (width proportional to class size)",
        y="Survival Proportion",
        fill="Outcome",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.5),
        panel_grid=element_blank(),
        plot_title=element_text(size=24, ha="center", color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_text_x=element_blank(),
        axis_ticks_major_x=element_blank(),
        legend_title=element_text(size=18, color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="right",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300)
