""" pyplots.ai
box-basic: Basic Box Plot
Library: plotnine 0.15.3 | Python 3.14
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_boxplot,
    ggplot,
    labs,
    scale_fill_manual,
    scale_y_continuous,
    stat_summary,
    theme,
    theme_minimal,
)


# Data
np.random.seed(42)
categories = ["Engineering", "Marketing", "Sales", "Support", "Research"]
records = []

for cat in categories:
    n = np.random.randint(60, 120)
    if cat == "Engineering":
        values = np.random.normal(95000, 15000, n)
    elif cat == "Marketing":
        values = np.random.normal(75000, 12000, n)
    elif cat == "Sales":
        base = np.random.normal(68000, 18000, n)
        outliers = np.random.normal(135000, 6000, 4)
        values = np.concatenate([base, outliers])
    elif cat == "Support":
        values = np.random.normal(55000, 8000, n)
    else:  # Research
        values = np.random.normal(85000, 20000, n)
    records.extend({"department": cat, "salary": v} for v in values)

df = pd.DataFrame(records)
dept_order = ["Support", "Marketing", "Sales", "Research", "Engineering"]
df["department"] = pd.Categorical(df["department"], categories=dept_order, ordered=True)

# Compute medians for storytelling annotations
medians = df.groupby("department", observed=True)["salary"].median()
eng_median = medians["Engineering"]
sup_median = medians["Support"]
gap = eng_median - sup_median

# Custom palette — cohesive muted tones starting from Python Blue
palette = ["#7FAACC", "#E8A87C", "#D4A5C9", "#82C9B0", "#306998"]

# Plot with stat_summary and annotate for storytelling
plot = (
    ggplot(df, aes(x="department", y="salary", fill="department"))
    + geom_boxplot(
        outlier_size=3.5, outlier_alpha=0.7, outlier_colour="#C0392B", size=0.5, alpha=0.88, width=0.6, color="#444444"
    )
    # Median diamond markers via stat_summary — distinctive plotnine feature
    + stat_summary(fun_y=np.median, geom="point", size=5, shape="D", color="#1a1a1a", fill="#1a1a1a")
    + scale_fill_manual(values=palette)
    + scale_y_continuous(labels=lambda vals: [f"${v / 1000:.0f}k" for v in vals], breaks=range(20000, 160001, 20000))
    + coord_cartesian(ylim=(12000, 156000))
    # Annotation: salary gap between Engineering and Support
    + annotate(
        "text",
        x=3,
        y=151000,
        label=f"Engineering earns ${gap / 1000:.0f}k more than Support",
        color="#306998",
        size=10,
        ha="center",
        fontweight="bold",
    )
    + annotate("segment", x=1, xend=5, y=144000, yend=144000, color="#306998", size=0.6, linetype="dashed", alpha=0.5)
    # Annotation: Sales outlier cluster callout
    + annotate(
        "label",
        x=3.5,
        y=132000,
        label="Senior hires\nabove market rate",
        size=9,
        color="#8B0000",
        fill="#FFF0F0",
        alpha=0.9,
        label_size=0,
        ha="left",
    )
    + annotate("segment", x=3.18, xend=3.42, y=132000, yend=132000, color="#C0392B", size=0.5, alpha=0.5)
    # Annotation: Support tight distribution insight
    + annotate(
        "text", x=1, y=28000, label="Narrow spread\n(σ ≈ $8k)", color="#666666", size=8, ha="center", fontstyle="italic"
    )
    + labs(x="Department", y="Salary ($)", title="box-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, color="#333333"),
        plot_title=element_text(size=24, color="#1a1a1a", weight="bold", margin={"b": 14}),
        axis_title_x=element_text(size=20, color="#222222", margin={"t": 14}),
        axis_title_y=element_text(size=20, color="#222222", margin={"r": 14}),
        axis_text=element_text(size=16, color="#555555"),
        legend_position="none",
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#e0e0e0", size=0.5),
        axis_ticks_major_x=element_blank(),
        axis_ticks_major_y=element_blank(),
        plot_background=element_rect(fill="white", color="white"),
        panel_background=element_rect(fill="white", color="white"),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
