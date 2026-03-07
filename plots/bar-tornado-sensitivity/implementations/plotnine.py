"""pyplots.ai
bar-tornado-sensitivity: Tornado Diagram for Sensitivity Analysis
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-03-07
"""

import pandas as pd
from plotnine import (
    aes,
    coord_flip,
    element_blank,
    element_line,
    element_text,
    geom_col,
    geom_hline,
    ggplot,
    labs,
    scale_fill_manual,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data
base_npv = 120.0

parameters = [
    "Discount Rate",
    "Revenue Growth",
    "Material Cost",
    "Labor Cost",
    "Tax Rate",
    "Inflation Rate",
    "Market Share",
    "Capex",
    "Operating Margin",
    "Terminal Value",
]
low_values = [95.0, 98.0, 102.0, 105.0, 108.0, 110.0, 112.0, 113.0, 115.0, 116.0]
high_values = [148.0, 145.0, 140.0, 137.0, 134.0, 131.0, 129.0, 127.0, 126.0, 124.5]

# Compute deviations from base case
records = []
for param, low, high in zip(parameters, low_values, high_values, strict=True):
    total_range = high - low
    records.append(
        {"parameter": param, "scenario": "Low Scenario", "deviation": low - base_npv, "total_range": total_range}
    )
    records.append(
        {"parameter": param, "scenario": "High Scenario", "deviation": high - base_npv, "total_range": total_range}
    )

df = pd.DataFrame(records)

# Sort by total range: widest at top (highest category level after coord_flip)
sort_order = df.groupby("parameter")["total_range"].first().sort_values(ascending=True).index.tolist()
df["parameter"] = pd.Categorical(df["parameter"], categories=sort_order, ordered=True)

# Plot
plot = (
    ggplot(df, aes(x="parameter", y="deviation", fill="scenario"))
    + geom_col(position="identity", width=0.7)
    + geom_hline(yintercept=0, linetype="dashed", color="#333333", size=0.8)
    + coord_flip()
    + scale_fill_manual(values={"Low Scenario": "#D95F02", "High Scenario": "#306998"})
    + scale_y_continuous(labels=lambda vals: [f"{base_npv + v:.0f}" for v in vals])
    + labs(x="", y="Net Present Value ($M)", title="bar-tornado-sensitivity \u00b7 plotnine \u00b7 pyplots.ai", fill="")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title_x=element_text(size=20),
        axis_title_y=element_text(size=20),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=16),
        plot_title=element_text(size=24, weight="bold"),
        legend_text=element_text(size=16),
        legend_position="top",
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        axis_line_x=element_line(size=0.5, color="#333333"),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
