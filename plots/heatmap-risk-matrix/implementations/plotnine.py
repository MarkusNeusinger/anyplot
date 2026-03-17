""" pyplots.ai
heatmap-risk-matrix: Risk Assessment Matrix (Probability vs Impact)
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-17
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_rect,
    element_text,
    geom_label,
    geom_text,
    geom_tile,
    ggplot,
    labs,
    scale_fill_gradientn,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data: Background grid with risk scores and zone classification
likelihood_levels = [1, 2, 3, 4, 5]
impact_levels = [1, 2, 3, 4, 5]

grid_rows = []
for li in likelihood_levels:
    for imp in impact_levels:
        score = li * imp
        if score <= 4:
            zone = "Low"
        elif score <= 9:
            zone = "Medium"
        elif score <= 16:
            zone = "High"
        else:
            zone = "Critical"
        grid_rows.append({"likelihood": li, "impact": imp, "risk_score": score, "zone": zone})

grid_df = pd.DataFrame(grid_rows)

# Position score numbers in top-left corner of each cell to avoid label overlap
grid_df["score_x"] = grid_df["impact"] - 0.38
grid_df["score_y"] = grid_df["likelihood"] + 0.35

# Risk items
np.random.seed(42)
risks = pd.DataFrame(
    {
        "risk_name": [
            "Supply Delay",
            "Budget Overrun",
            "Key Staff Loss",
            "Scope Creep",
            "Vendor Failure",
            "Reg Change",
            "Data Breach",
            "Tech Debt",
            "Market Shift",
            "Integration Bug",
            "Power Outage",
            "Compliance Gap",
        ],
        "likelihood": [3, 4, 2, 5, 2, 3, 1, 4, 3, 4, 1, 3],
        "impact": [3, 4, 5, 3, 4, 2, 5, 2, 4, 3, 4, 4],
        "category": [
            "Operational",
            "Financial",
            "Operational",
            "Technical",
            "Operational",
            "Financial",
            "Technical",
            "Technical",
            "Financial",
            "Technical",
            "Operational",
            "Financial",
        ],
    }
)

# Smart label positioning: detect same-cell risks and offset them
cell_counts = risks.groupby(["likelihood", "impact"]).cumcount()
cell_totals = risks.groupby(["likelihood", "impact"])["risk_name"].transform("count")

# Offset labels vertically within shared cells
label_offsets = []
for idx in range(len(risks)):
    count = cell_counts.iloc[idx]
    total = cell_totals.iloc[idx]
    if total > 1:
        offset = 0.18 if count == 0 else -0.18
    else:
        offset = -0.05
    label_offsets.append(offset)

risks["y_offset"] = label_offsets
risks["label_y"] = risks["likelihood"] + risks["y_offset"]
risks["label_x"] = risks["impact"].astype(float)

# Axis labels
likelihood_labels = {1: "Rare", 2: "Unlikely", 3: "Possible", 4: "Likely", 5: "Almost\nCertain"}
impact_labels = {1: "Negligible", 2: "Minor", 3: "Moderate", 4: "Major", 5: "Catastrophic"}

# Spec palette: green-yellow-orange-red with colorblind-safe tones
risk_colors = ["#1a9641", "#a6d96a", "#ffffbf", "#fdae61", "#f46d43", "#d73027", "#a50026"]


# Plot
plot = (
    ggplot()
    # Background heatmap tiles
    + geom_tile(data=grid_df, mapping=aes(x="impact", y="likelihood", fill="risk_score"), color="#2c2c3a", size=1.2)
    + scale_fill_gradientn(colors=risk_colors, limits=(1, 25), name="Risk\nScore", breaks=[1, 5, 10, 15, 20, 25])
    # Risk score numbers in top-left corner of each cell (avoids overlap with labels)
    + geom_text(
        data=grid_df,
        mapping=aes(x="score_x", y="score_y", label="risk_score"),
        color="#00000055",
        size=11,
        fontweight="bold",
        ha="left",
        va="top",
    )
    # Risk item labels
    + geom_label(
        data=risks,
        mapping=aes(x="label_x", y="label_y", label="risk_name"),
        color="white",
        fill="#1a1a2e",
        size=9,
        alpha=0.9,
        label_padding=0.2,
        label_size=0.3,
        label_r=0.08,
    )
    # Zone annotation above the grid
    + annotate(
        "text",
        x=3,
        y=5.55,
        label="Zones:  Low (1\u20134)  \u00b7  Medium (5\u20139)  \u00b7  High (10\u201316)  \u00b7  Critical (20\u201325)",
        size=9,
        color="#555555",
        fontstyle="italic",
    )
    # Axes
    + scale_x_continuous(breaks=impact_levels, labels=[impact_labels[i] for i in impact_levels], expand=(0, 0.55))
    + scale_y_continuous(
        breaks=likelihood_levels, labels=[likelihood_labels[i] for i in likelihood_levels], expand=(0, 0.65)
    )
    + labs(x="Impact \u2192", y="Likelihood \u2192", title="heatmap-risk-matrix \u00b7 plotnine \u00b7 pyplots.ai")
    # Theme
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center", weight="bold", margin={"b": 15}),
        axis_title_x=element_text(size=20, weight="bold", margin={"t": 10}),
        axis_title_y=element_text(size=20, weight="bold", margin={"r": 10}),
        axis_text_x=element_text(size=15),
        axis_text_y=element_text(size=15),
        legend_title=element_text(size=16, weight="bold"),
        legend_text=element_text(size=14),
        legend_key_height=60,
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill="#fafafa", color="#fafafa"),
        panel_background=element_rect(fill="#fafafa"),
    )
)

# Save
plot.save("plot.png", dpi=300, width=16, height=9)
