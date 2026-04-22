"""pyplots.ai
heatmap-risk-matrix: Risk Assessment Matrix (Probability vs Impact)
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 80/100 | Created: 2026-03-17
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data
np.random.seed(42)

likelihood_labels = ["Rare", "Unlikely", "Possible", "Likely", "Almost\nCertain"]
impact_labels = ["Negligible", "Minor", "Moderate", "Major", "Catastrophic"]

# Build background grid with risk zones
grid_rows = []
for li in range(1, 6):
    for im in range(1, 6):
        score = li * im
        if score <= 4:
            zone = "Low"
        elif score <= 9:
            zone = "Medium"
        elif score <= 16:
            zone = "High"
        else:
            zone = "Critical"
        grid_rows.append({"likelihood": li, "impact": im, "score": score, "zone": zone, "score_label": str(score)})
grid_df = pd.DataFrame(grid_rows)
grid_df["zone"] = pd.Categorical(grid_df["zone"], categories=["Low", "Medium", "High", "Critical"], ordered=True)

# Risk items with shorter names to avoid label overlap
risks = pd.DataFrame(
    {
        "risk_name": [
            "Server Outage",
            "Data Breach",
            "Budget Overrun",
            "Staff Loss",
            "Vendor Fail",
            "Scope Creep",
            "Reg. Change",
            "Tech Debt",
            "Integ. Bug",
            "Supply Delay",
            "Currency",
            "PR Crisis",
            "Patent Issue",
            "Power Outage",
            "Cyber Attack",
        ],
        "likelihood": [4, 3, 4, 2, 2, 5, 3, 4, 3, 1, 3, 1, 1, 2, 5],
        "impact": [5, 5, 3, 4, 3, 2, 3, 2, 4, 3, 2, 5, 4, 1, 5],
        "category": [
            "Technical",
            "Technical",
            "Financial",
            "Operational",
            "Operational",
            "Operational",
            "Financial",
            "Technical",
            "Technical",
            "Operational",
            "Financial",
            "Operational",
            "Financial",
            "Technical",
            "Technical",
        ],
    }
)

# Compute risk score for size mapping (visual hierarchy)
risks["risk_score"] = risks["likelihood"] * risks["impact"]

# Smart jitter: offset risks sharing same cell
cell_counts = {}
offsets_x = []
offsets_y = []
for _, row in risks.iterrows():
    cell = (row["likelihood"], row["impact"])
    idx = cell_counts.get(cell, 0)
    cell_counts[cell] = idx + 1
    offset_patterns = [(0, 0.15), (0, -0.15), (-0.2, 0), (0.2, 0)]
    ox, oy = offset_patterns[idx % len(offset_patterns)]
    offsets_x.append(ox)
    offsets_y.append(oy)

risks["lk_jitter"] = risks["likelihood"] + np.array(offsets_x)
risks["im_jitter"] = risks["impact"] + np.array(offsets_y)

# Assign label nudge using checkerboard pattern based on grid position
# This ensures adjacent cells always have opposite nudge directions
nudge_vals = []
for _, row in risks.iterrows():
    li, imp = int(row["likelihood"]), int(row["impact"])
    if (li + imp) % 2 == 0:
        nudge_vals.append(0.33)
    else:
        nudge_vals.append(-0.33)
risks["label_nudge_y"] = nudge_vals

# Tooltips for lets-plot distinctive interactivity
risk_tooltips = (
    layer_tooltips()
    .line("@risk_name")
    .line("Category: @category")
    .line("Likelihood: @likelihood")
    .line("Impact: @impact")
    .line("Risk Score: @risk_score")
)

# Zone palette: green-yellow-orange-red as specified
zone_colors = {"Low": "#2A9D8F", "Medium": "#E9C46A", "High": "#F4A261", "Critical": "#C1121F"}

# Category colors
cat_colors = {"Technical": "#306998", "Financial": "#7B2D8E", "Operational": "#D35400"}

# Split risks for alternating label nudge
risks_up = risks[risks["label_nudge_y"] > 0].copy()
risks_down = risks[risks["label_nudge_y"] < 0].copy()

# Plot
plot = (
    ggplot()
    + geom_tile(aes(x="likelihood", y="impact", fill="zone"), data=grid_df, color="white", size=2, tooltips="none")
    + geom_text(aes(x="likelihood", y="impact", label="score_label"), data=grid_df, size=13, color="rgba(0,0,0,0.12)")
    + geom_point(
        aes(x="lk_jitter", y="im_jitter", color="category", size="risk_score"),
        data=risks,
        alpha=0.92,
        tooltips=risk_tooltips,
    )
    + scale_size(range=[4, 12], name="Risk Score", guide="none")
    + scale_fill_manual(values=zone_colors, name="Risk Level")
    + scale_color_manual(values=cat_colors, name="Category")
    + scale_x_continuous(breaks=[1, 2, 3, 4, 5], labels=likelihood_labels, limits=[0.4, 5.8])
    + scale_y_continuous(breaks=[1, 2, 3, 4, 5], labels=impact_labels, limits=[0.4, 5.6])
    + coord_fixed(ratio=1)
    + labs(
        x="Likelihood",
        y="Impact",
        title="heatmap-risk-matrix · lets-plot · pyplots.ai",
        subtitle="Risk score = Likelihood × Impact  |  Marker size scales with severity",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        plot_subtitle=element_text(size=15, color="#555555"),
        axis_title=element_text(size=20, face="bold"),
        axis_text=element_text(size=15),
        legend_title=element_text(size=17, face="bold"),
        legend_text=element_text(size=14),
        panel_grid=element_blank(),
    )
    + ggsize(1600, 900)
)

# Add labels with alternating nudge directions to reduce overlap
if len(risks_up) > 0:
    plot = plot + geom_text(
        aes(x="lk_jitter", y="im_jitter", label="risk_name"), data=risks_up, size=9, nudge_y=0.33, fontface="bold"
    )

if len(risks_down) > 0:
    plot = plot + geom_text(
        aes(x="lk_jitter", y="im_jitter", label="risk_name"), data=risks_down, size=9, nudge_y=-0.33, fontface="bold"
    )

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
