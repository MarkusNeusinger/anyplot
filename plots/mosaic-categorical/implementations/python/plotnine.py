""" anyplot.ai
mosaic-categorical: Mosaic Plot for Categorical Association Analysis
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-19
"""

import os

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_rect,
    geom_text,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Data - Titanic survival data by passenger class
data = {
    "class": ["First", "First", "Second", "Second", "Third", "Third"],
    "survival": ["Survived", "Did Not Survive", "Survived", "Did Not Survive", "Survived", "Did Not Survive"],
    "count": [203, 122, 118, 167, 178, 528],
}
df = pd.DataFrame(data)
survival_order = ["Survived", "Did Not Survive"]

# Calculate proportions for mosaic geometry
total = df["count"].sum()
class_totals = df.groupby("class")["count"].sum()
class_order = ["First", "Second", "Third"]
widths = {c: class_totals[c] / total for c in class_order}

# Build rectangle data for each cell — widths ∝ class size, heights ∝ conditional proportion
gap = 0.02
rects = []
x_pos = 0
x_centers = {}
survival_rates = {}

for cls in class_order:
    class_data = df[df["class"] == cls]
    class_total = class_data["count"].sum()
    width = widths[cls] - gap
    x_centers[cls] = x_pos + width / 2
    survived_n = class_data[class_data["survival"] == "Survived"]["count"].values[0]
    survival_rates[cls] = survived_n / class_total

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
                "survival": row["survival"],
                "count": row["count"],
                "x_center": x_pos + width / 2,
                "y_center": y_pos + height / 2,
            }
        )
        y_pos += height + gap / 2

    x_pos += widths[cls]

rect_df = pd.DataFrame(rects)

# Class name labels and per-class survival rate annotations below the mosaic
class_labels = pd.DataFrame({"x": [x_centers[c] for c in class_order], "y": [-0.055] * 3, "label": class_order})
rate_labels = pd.DataFrame(
    {
        "x": [x_centers[c] for c in class_order],
        "y": [-0.115] * 3,
        "label": [f"{survival_rates[c]:.0%} survived" for c in class_order],
    }
)

# Okabe-Ito: green → Survived (first series), vermillion → Did Not Survive
colors = {"Survived": IMPRINT[0], "Did Not Survive": IMPRINT[1]}

# scale_x_continuous / scale_y_continuous give explicit domain + expansion control —
# avoids clipping the below-axis class and rate labels
plot = (
    ggplot(rect_df)
    + geom_rect(aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="survival"), color=PAGE_BG, size=1.5)
    + geom_text(aes(x="x_center", y="y_center", label="count"), color="white", size=14, fontweight="bold")
    + geom_text(data=class_labels, mapping=aes(x="x", y="y", label="label"), size=14, color=INK, fontweight="bold")
    + geom_text(data=rate_labels, mapping=aes(x="x", y="y", label="label"), size=12, color=INK_SOFT)
    + scale_fill_manual(values=colors, breaks=["Survived", "Did Not Survive"])
    + scale_x_continuous(expand=(0, 0.01), limits=(0, 1.01))
    + scale_y_continuous(expand=(0, 0), limits=(-0.17, 1.04))
    + labs(
        title="mosaic-categorical · python · plotnine · anyplot.ai",
        subtitle="First-class survival rate (62%) was 2.5× higher than Third-class (25%)",
        y="Conditional Survival Proportion",
        fill="Outcome",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_border=element_blank(),
        panel_grid=element_blank(),
        axis_line_x=element_line(color=INK_SOFT, size=0.5),
        axis_line_y=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=24, ha="center", color=INK, fontweight="bold"),
        plot_subtitle=element_text(size=17, ha="center", color=INK_SOFT),
        axis_title_x=element_blank(),
        axis_title_y=element_text(size=20, color=INK),
        axis_text_x=element_blank(),
        axis_ticks_major_x=element_blank(),
        axis_text_y=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="right",
    )
)

plot.save(f"plot-{THEME}.png", dpi=300)
