""" pyplots.ai
marimekko-basic: Basic Marimekko Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import altair as alt
import pandas as pd


# Data - Market share by region and product line
data = {
    "Region": ["North America"] * 4 + ["Europe"] * 4 + ["Asia Pacific"] * 4 + ["Latin America"] * 4,
    "Product": ["Electronics", "Clothing", "Food", "Home"] * 4,
    "Revenue": [
        120,
        80,
        60,
        40,  # North America (total: 300, largest market)
        90,
        70,
        50,
        30,  # Europe (total: 240)
        100,
        60,
        80,
        60,  # Asia Pacific (total: 300)
        40,
        30,
        35,
        25,  # Latin America (total: 130, smallest market)
    ],
}

df = pd.DataFrame(data)

# Calculate totals for each region (determines bar widths)
region_totals = df.groupby("Region")["Revenue"].sum().reset_index()
region_totals.columns = ["Region", "RegionTotal"]
grand_total = region_totals["RegionTotal"].sum()
region_totals["WidthPct"] = region_totals["RegionTotal"] / grand_total * 100

# Calculate cumulative x positions for each region
region_totals = region_totals.sort_values("RegionTotal", ascending=False)
region_totals["x_start"] = region_totals["WidthPct"].cumsum() - region_totals["WidthPct"]
region_totals["x_end"] = region_totals["WidthPct"].cumsum()
region_totals["x_mid"] = (region_totals["x_start"] + region_totals["x_end"]) / 2

# Merge back to main dataframe
df = df.merge(region_totals, on="Region")

# Calculate y positions (percentages within each region)
df["PctWithinRegion"] = df["Revenue"] / df["RegionTotal"] * 100

# Sort by product for consistent stacking order
product_order = ["Electronics", "Clothing", "Food", "Home"]
df["ProductOrder"] = df["Product"].map({p: i for i, p in enumerate(product_order)})
df = df.sort_values(["Region", "ProductOrder"])

# Calculate cumulative y positions within each region
df["y_end"] = df.groupby("Region")["PctWithinRegion"].cumsum()
df["y_start"] = df["y_end"] - df["PctWithinRegion"]

# Color palette - Python Blue primary, then colorblind-safe colors
colors = ["#306998", "#FFD43B", "#4ECDC4", "#E76F51"]

# Create the Marimekko chart using rect marks
chart = (
    alt.Chart(df)
    .mark_rect(stroke="white", strokeWidth=2)
    .encode(
        x=alt.X("x_start:Q", axis=None),  # Hide default x-axis
        x2="x_end:Q",
        y=alt.Y("y_start:Q", title="Product Mix (%)", scale=alt.Scale(domain=[0, 100])),
        y2="y_end:Q",
        color=alt.Color(
            "Product:N",
            scale=alt.Scale(domain=product_order, range=colors),
            legend=alt.Legend(title="Product Line", titleFontSize=18, labelFontSize=16, symbolSize=300),
        ),
        tooltip=[
            alt.Tooltip("Region:N", title="Region"),
            alt.Tooltip("Product:N", title="Product"),
            alt.Tooltip("Revenue:Q", title="Revenue ($M)", format=",.0f"),
            alt.Tooltip("PctWithinRegion:Q", title="% of Region", format=".1f"),
        ],
    )
    .properties(
        width=1600, height=900, title=alt.Title("marimekko-basic · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
)

# Add region labels at the bottom with market size
region_totals["Label"] = (
    region_totals["Region"] + "\n($" + (region_totals["RegionTotal"]).astype(int).astype(str) + "M)"
)
region_labels = (
    alt.Chart(region_totals)
    .mark_text(align="center", baseline="top", dy=15, fontSize=18, fontWeight="bold")
    .encode(
        x=alt.X("x_mid:Q", scale=alt.Scale(domain=[0, 100])),
        y=alt.value(900),  # Position at bottom of chart
        text="Label:N",
    )
)

# Combine chart with labels
final_chart = (
    alt.layer(chart, region_labels)
    .configure_axis(labelFontSize=16, titleFontSize=20, grid=True, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save as PNG (scale_factor=3 for 4800x2700)
final_chart.save("plot.png", scale_factor=3.0)

# Save as HTML for interactivity
final_chart.save("plot.html")
