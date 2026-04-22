""" pyplots.ai
bar-stacked-percent: 100% Stacked Bar Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_text,
    geom_bar,
    geom_text,
    ggplot,
    labs,
    position_fill,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Data - Market share by quarter for tech companies
quarters = ["Q1 2023", "Q2 2023", "Q3 2023", "Q4 2023", "Q1 2024", "Q2 2024"]
data = {
    "Quarter": quarters * 4,
    "Company": (["Apple"] * 6 + ["Samsung"] * 6 + ["Xiaomi"] * 6 + ["Others"] * 6),
    "Share": [
        # Apple
        23,
        21,
        20,
        22,
        21,
        20,
        # Samsung
        22,
        21,
        20,
        19,
        20,
        19,
        # Xiaomi
        12,
        13,
        14,
        14,
        15,
        16,
        # Others
        43,
        45,
        46,
        45,
        44,
        45,
    ],
}
df = pd.DataFrame(data)

# Set categorical ordering for proper display
df["Quarter"] = pd.Categorical(df["Quarter"], categories=quarters, ordered=True)
df["Company"] = pd.Categorical(df["Company"], categories=["Others", "Xiaomi", "Samsung", "Apple"], ordered=True)

# Calculate percentages for labels (values shown on chart)
df_grouped = df.groupby(["Quarter", "Company"], observed=True).agg({"Share": "sum"}).reset_index()
df_grouped["Quarter"] = pd.Categorical(df_grouped["Quarter"], categories=quarters, ordered=True)
df_grouped["Percent"] = df_grouped.groupby("Quarter", observed=True)["Share"].transform(lambda x: x / x.sum() * 100)
df_grouped["Label"] = df_grouped["Percent"].apply(lambda x: f"{x:.0f}%" if x >= 8 else "")

# Colors - Python Blue first, then complementary colors
colors = {
    "Apple": "#306998",  # Python Blue
    "Samsung": "#FFD43B",  # Python Yellow
    "Xiaomi": "#4CAF50",  # Green
    "Others": "#9E9E9E",  # Gray
}

# Create 100% stacked bar chart
plot = (
    ggplot(df_grouped, aes(x="Quarter", y="Share", fill="Company"))
    + geom_bar(stat="identity", position=position_fill(), width=0.7)
    + geom_text(aes(label="Label"), position=position_fill(vjust=0.5), size=14, color="white", fontweight="bold")
    + scale_fill_manual(values=colors)
    + labs(title="bar-stacked-percent · plotnine · pyplots.ai", x="Quarter", y="Market Share (%)", fill="Company")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title_x=element_text(size=20),
        axis_title_y=element_text(size=20),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
