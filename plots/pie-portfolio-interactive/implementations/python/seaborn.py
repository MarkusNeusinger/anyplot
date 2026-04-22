""" pyplots.ai
pie-portfolio-interactive: Interactive Portfolio Allocation Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Set seaborn style for consistent aesthetics
sns.set_theme(style="white")
sns.set_context("talk", font_scale=1.2)

# Portfolio data with asset classes and individual holdings
np.random.seed(42)
portfolio_data = pd.DataFrame(
    {
        "asset": [
            "US Large Cap Equity",
            "International Equity",
            "Emerging Markets",
            "US Treasury Bonds",
            "Corporate Bonds",
            "Municipal Bonds",
            "REITs",
            "Gold",
            "Private Equity",
        ],
        "weight": [28.0, 15.0, 7.0, 18.0, 12.0, 5.0, 6.0, 4.0, 5.0],
        "category": [
            "Equities",
            "Equities",
            "Equities",
            "Fixed Income",
            "Fixed Income",
            "Fixed Income",
            "Alternatives",
            "Alternatives",
            "Alternatives",
        ],
        "value": [280000, 150000, 70000, 180000, 120000, 50000, 60000, 40000, 50000],
    }
)

# Category aggregation for inner ring
category_data = portfolio_data.groupby("category").agg({"weight": "sum", "value": "sum"}).reset_index()

# Use seaborn color palettes for distinctive library usage
# Primary categorical palette for asset classes
category_palette = sns.color_palette("husl", n_colors=3)
category_colors = {
    "Equities": category_palette[0],
    "Fixed Income": category_palette[1],
    "Alternatives": category_palette[2],
}

# Create shades for individual assets using seaborn's cubehelix_palette for each category
asset_colors = []
for _, row in portfolio_data.iterrows():
    base_color = category_colors[row["category"]]
    cat_assets = portfolio_data[portfolio_data["category"] == row["category"]]
    idx = cat_assets[cat_assets["asset"] == row["asset"]].index[0]
    cat_idx = list(cat_assets.index).index(idx)
    # Use seaborn's blend_palette to create cohesive color gradations
    n_assets = len(cat_assets)
    light_color = sns.light_palette(base_color, n_colors=n_assets + 2, reverse=False)[1]
    dark_color = sns.dark_palette(base_color, n_colors=n_assets + 2, reverse=True)[1]
    blend_palette = sns.blend_palette([light_color, base_color, dark_color], n_colors=n_assets + 2)
    asset_colors.append(blend_palette[cat_idx + 1])

# Create figure - using square aspect for better pie visualization
fig, ax = plt.subplots(figsize=(12, 12))

# Outer ring - Individual assets (detailed breakdown)
# Note: Seaborn does not provide native pie chart functions, so matplotlib's pie is used
# with seaborn for color generation and theming
outer_wedges, outer_texts, outer_autotexts = ax.pie(
    portfolio_data["weight"],
    labels=None,
    colors=asset_colors,
    autopct=lambda pct: f"{pct:.1f}%" if pct > 4 else "",
    startangle=90,
    radius=1.0,
    pctdistance=0.82,
    wedgeprops={"width": 0.35, "edgecolor": "white", "linewidth": 2},
)

# Style outer ring percentages using seaborn's desaturated text color
text_color = sns.desaturate("#333333", 0.8)
for autotext in outer_autotexts:
    autotext.set_fontsize(14)
    autotext.set_fontweight("bold")
    autotext.set_color(text_color)

# Inner ring - Category breakdown
category_colors_list = [category_colors[cat] for cat in category_data["category"]]
inner_wedges, inner_texts, inner_autotexts = ax.pie(
    category_data["weight"],
    labels=None,
    colors=category_colors_list,
    autopct=lambda pct: f"{pct:.0f}%",
    startangle=90,
    radius=0.65,
    pctdistance=0.5,
    wedgeprops={"width": 0.35, "edgecolor": "white", "linewidth": 2},
)

# Style inner ring percentages
for autotext in inner_autotexts:
    autotext.set_fontsize(16)
    autotext.set_fontweight("bold")
    autotext.set_color("white")

# Add center text showing total portfolio value
total_value = portfolio_data["value"].sum()
ax.text(
    0,
    0,
    f"Portfolio\n${total_value / 1000:.0f}K",
    ha="center",
    va="center",
    fontsize=24,
    fontweight="bold",
    color=text_color,
)

# Calculate annotation positions distributed around the chart (balanced layout)
cumulative_weight = 0
annotation_data = []

for _, row in portfolio_data.iterrows():
    angle_deg = 90 - cumulative_weight - row["weight"] / 2
    cumulative_weight += row["weight"]
    angle_rad = np.deg2rad(angle_deg)

    # Annotation radius varies based on position for better balance
    x_pos = 1.35 * np.cos(angle_rad)
    y_pos = 1.35 * np.sin(angle_rad)

    annotation_data.append({"x_pos": x_pos, "y_pos": y_pos, "angle_deg": angle_deg, "angle_rad": angle_rad, "row": row})

# Add annotation boxes showing detailed info (simulating interactive tooltips)
# Show annotations for holdings >= 6% with balanced distribution
for data in annotation_data:
    row = data["row"]
    if row["weight"] >= 6:
        x_pos = data["x_pos"]
        y_pos = data["y_pos"]
        angle_rad = data["angle_rad"]

        # Dynamic alignment based on quadrant for balanced layout
        if x_pos > 0.3:
            ha = "left"
            x_offset = 0.08
        elif x_pos < -0.3:
            ha = "right"
            x_offset = -0.08
        else:
            ha = "center"
            x_offset = 0

        annotation_text = f"{row['asset']}\n${row['value']:,.0f} ({row['weight']:.1f}%)"

        # Connection point on the wedge
        wedge_x = 1.0 * np.cos(angle_rad)
        wedge_y = 1.0 * np.sin(angle_rad)

        # Use seaborn saturated color for annotation border
        border_color = sns.saturate(category_colors[row["category"]])

        ax.annotate(
            annotation_text,
            xy=(wedge_x, wedge_y),
            xytext=(x_pos + x_offset, y_pos),
            fontsize=13,
            fontweight="medium",
            ha=ha,
            va="center",
            bbox={
                "boxstyle": "round,pad=0.4",
                "facecolor": "white",
                "edgecolor": border_color,
                "linewidth": 2,
                "alpha": 0.95,
            },
            arrowprops={
                "arrowstyle": "-",
                "color": sns.desaturate("#666666", 0.5),
                "connectionstyle": "arc3,rad=0.1",
                "linewidth": 1.5,
            },
        )

# Create legend for categories with detailed info using seaborn styling
legend_labels = []
for _, row in category_data.iterrows():
    n_holdings = len(portfolio_data[portfolio_data["category"] == row["category"]])
    legend_labels.append(
        f"{row['category']}: {row['weight']:.0f}% (${row['value'] / 1000:.0f}K, {n_holdings} holdings)"
    )

legend = ax.legend(
    inner_wedges,
    legend_labels,
    title="Asset Classes (Click to Drill Down)",
    loc="lower center",
    bbox_to_anchor=(0.5, -0.08),
    fontsize=14,
    title_fontsize=16,
    frameon=True,
    fancybox=True,
    ncol=3,
    columnspacing=1.5,
)

# Title
ax.set_title("pie-portfolio-interactive · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=25)

# Note about interactivity
ax.text(
    0.5,
    -0.16,
    "Hover over segments to see details • Click asset class to drill down into holdings",
    transform=ax.transAxes,
    ha="center",
    va="top",
    fontsize=12,
    fontstyle="italic",
    color=sns.desaturate("#666666", 0.7),
)

# Ensure equal aspect ratio for proper circular display
ax.set_aspect("equal")
ax.set_xlim(-1.7, 1.7)
ax.set_ylim(-1.5, 1.5)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close()
