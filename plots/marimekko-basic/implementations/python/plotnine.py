""" pyplots.ai
marimekko-basic: Basic Marimekko Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import pandas as pd
from plotnine import (
    aes,
    element_blank,
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


# Data - Market share by region and product line
data = {
    "region": [
        "North America",
        "North America",
        "North America",
        "North America",
        "Europe",
        "Europe",
        "Europe",
        "Europe",
        "Asia Pacific",
        "Asia Pacific",
        "Asia Pacific",
        "Asia Pacific",
        "Latin America",
        "Latin America",
        "Latin America",
        "Latin America",
    ],
    "product": [
        "Electronics",
        "Software",
        "Services",
        "Hardware",
        "Electronics",
        "Software",
        "Services",
        "Hardware",
        "Electronics",
        "Software",
        "Services",
        "Hardware",
        "Electronics",
        "Software",
        "Services",
        "Hardware",
    ],
    "value": [
        180,
        120,
        90,
        60,  # North America: total 450
        140,
        80,
        100,
        40,  # Europe: total 360
        200,
        60,
        40,
        80,  # Asia Pacific: total 380
        50,
        30,
        40,
        30,
    ],  # Latin America: total 150
}
df = pd.DataFrame(data)

# Calculate totals per region (determines bar width)
region_totals = df.groupby("region")["value"].sum().reset_index()
region_totals.columns = ["region", "total"]
total_all = region_totals["total"].sum()

# Calculate cumulative x positions (bar widths)
region_totals["width_pct"] = region_totals["total"] / total_all * 100
region_totals["xmax"] = region_totals["width_pct"].cumsum()
region_totals["xmin"] = region_totals["xmax"] - region_totals["width_pct"]
region_totals["xcenter"] = (region_totals["xmin"] + region_totals["xmax"]) / 2

# Merge back to get x positions
df = df.merge(region_totals[["region", "xmin", "xmax", "total"]], on="region")

# Calculate y positions within each region (stacked segments)
df["pct_within"] = df["value"] / df["total"] * 100

# Sort by product within region for consistent stacking
product_order = ["Electronics", "Software", "Services", "Hardware"]
df["product_order"] = df["product"].map({p: i for i, p in enumerate(product_order)})
df = df.sort_values(["region", "product_order"]).reset_index(drop=True)

# Calculate cumulative y positions within each region
rects = []
for region in df["region"].unique():
    region_df = df[df["region"] == region].copy()
    y_pos = 0
    for _, row in region_df.iterrows():
        rect = {
            "region": row["region"],
            "product": row["product"],
            "value": row["value"],
            "xmin": row["xmin"],
            "xmax": row["xmax"],
            "ymin": y_pos,
            "ymax": y_pos + row["pct_within"],
        }
        rect["ycenter"] = (rect["ymin"] + rect["ymax"]) / 2
        rect["xcenter"] = (rect["xmin"] + rect["xmax"]) / 2
        rects.append(rect)
        y_pos += row["pct_within"]

plot_df = pd.DataFrame(rects)

# Add labels with value for larger segments
plot_df["label"] = plot_df.apply(lambda r: f"${r['value']}M" if (r["ymax"] - r["ymin"]) > 10 else "", axis=1)

# Color palette for products
product_colors = {
    "Electronics": "#306998",  # Python Blue
    "Software": "#FFD43B",  # Python Yellow
    "Services": "#4ECDC4",  # Teal
    "Hardware": "#FF6B6B",  # Coral
}

# Create plot
plot = (
    ggplot(plot_df)
    + geom_rect(aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="product"), color="white", size=1.0)
    + geom_text(aes(x="xcenter", y="ycenter", label="label"), size=12, color="black", fontweight="bold")
    + scale_fill_manual(values=product_colors)
    + scale_x_continuous(
        breaks=region_totals["xcenter"].tolist(), labels=region_totals["region"].tolist(), expand=(0.01, 0.01)
    )
    + scale_y_continuous(breaks=[0, 25, 50, 75, 100], labels=["0%", "25%", "50%", "75%", "100%"], expand=(0.01, 0.01))
    + labs(
        x="Market Segment (width = total market size)",
        y="Product Share (%)",
        title="Market Share by Region · marimekko-basic · plotnine · pyplots.ai",
        fill="Product Line",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center", weight="bold"),
        axis_title=element_text(size=20),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=14),
        legend_position="right",
        panel_grid_major_x=element_blank(),
        panel_grid_minor_x=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
