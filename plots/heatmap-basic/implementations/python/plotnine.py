""" pyplots.ai
heatmap-basic: Basic Heatmap
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 92/100 | Updated: 2026-02-16
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_text,
    geom_tile,
    ggplot,
    labs,
    scale_color_identity,
    scale_fill_gradient2,
    scale_x_discrete,
    scale_y_discrete,
    theme,
    theme_minimal,
)


# Data - 8x8 matrix: quarterly growth rates (%) by department
np.random.seed(42)
departments = ["Engineering", "Marketing", "Sales", "Finance", "Operations", "HR", "Research", "Support"]
quarters = ["Q1 '23", "Q2 '23", "Q3 '23", "Q4 '23", "Q1 '24", "Q2 '24", "Q3 '24", "Q4 '24"]

# Vectorized growth rates with recovery trend and departmental variation
base_trend = np.linspace(-18, 22, 8)
dept_offsets = np.array([-6, 10, 14, -3, 4, -10, 8, -5])
values = np.round(base_trend[np.newaxis, :] + dept_offsets[:, np.newaxis] + np.random.normal(0, 4, (8, 8)), 1)

# Inject distinctive extreme values for storytelling focal points
values[5, 0] = -32.5  # HR deep crisis in Q1 '23
values[2, 7] = 38.2  # Sales strong recovery in Q4 '24
values[6, 6] = 33.7  # Research surge in Q3 '24

# Build long-form DataFrame via meshgrid indexing
dept_idx, qtr_idx = np.meshgrid(np.arange(8), np.arange(8), indexing="ij")
df = pd.DataFrame(
    {
        "Department": pd.Categorical(
            [departments[i] for i in dept_idx.ravel()], categories=departments[::-1], ordered=True
        ),
        "Quarter": pd.Categorical([quarters[j] for j in qtr_idx.ravel()], categories=quarters, ordered=True),
        "Growth (%)": values.ravel(),
    }
)

# Conditional text color: white on dark blue, dark gray on mid, dark brown on gold
df["text_color"] = np.where(df["Growth (%)"] < -12, "white", np.where(df["Growth (%)"] < 18, "#3a3a3a", "#4a2e00"))

# Signed annotation labels
df["label"] = [f"{v:+.1f}" for v in df["Growth (%)"]]

# Plot
plot = (
    ggplot(df, aes(x="Quarter", y="Department"))
    + geom_tile(aes(fill="Growth (%)"), color="white", size=1.2)
    + geom_text(aes(label="label", color="text_color"), size=10, fontweight="bold", show_legend=False)
    + scale_fill_gradient2(
        low="#14405e", mid="#ede8e3", high="#c47d00", midpoint=0, name="Growth (%)", limits=(-35, 40)
    )
    + scale_color_identity()
    + scale_x_discrete(expand=(0, 0.5))
    + scale_y_discrete(expand=(0, 0.5))
    + labs(
        x="Quarter",
        y="Department",
        title="Quarterly Growth by Department · heatmap-basic · plotnine · pyplots.ai",
        subtitle="Year-over-year growth rate (%) across departments, Q1 2023 – Q4 2024",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(family="sans-serif"),
        plot_title=element_text(size=24, ha="center", weight="bold", margin={"b": 2}),
        plot_subtitle=element_text(size=16, ha="center", color="#555555", margin={"b": 8}),
        axis_title_x=element_text(size=20, margin={"t": 10}),
        axis_title_y=element_text(size=20, margin={"r": 8}),
        axis_text_x=element_text(size=16, rotation=45, ha="right", margin={"t": 4}),
        axis_text_y=element_text(size=16, ha="right", margin={"r": 4}),
        legend_title=element_text(size=16, weight="bold"),
        legend_text=element_text(size=14),
        legend_position="right",
        legend_key_height=40,
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="white", color="none"),
        plot_background=element_rect(fill="#f7f7f7", color="none"),
        plot_margin=0.02,
    )
)

plot.save("plot.png", dpi=300, verbose=False)
