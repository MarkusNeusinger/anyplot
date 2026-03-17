""" pyplots.ai
heatmap-risk-matrix: Risk Assessment Matrix (Probability vs Impact)
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 79/100 | Created: 2026-03-17
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_text,
    geom_label,
    geom_point,
    geom_tile,
    ggplot,
    labs,
    scale_fill_gradientn,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data: Background grid with risk scores
likelihood_levels = [1, 2, 3, 4, 5]
impact_levels = [1, 2, 3, 4, 5]

grid_rows = []
for li in likelihood_levels:
    for imp in impact_levels:
        grid_rows.append({"likelihood": li, "impact": imp, "risk_score": li * imp})

grid_df = pd.DataFrame(grid_rows)

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
        "impact": [3, 4, 5, 3, 4, 2, 5, 2, 4, 3, 1, 4],
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

# Add jitter to avoid overlap
jitter_x = np.random.uniform(-0.25, 0.25, len(risks))
jitter_y = np.random.uniform(-0.25, 0.25, len(risks))
risks["lk_jitter"] = risks["likelihood"] + jitter_y
risks["imp_jitter"] = risks["impact"] + jitter_x

# Axis labels
likelihood_labels = {1: "Rare", 2: "Unlikely", 3: "Possible", 4: "Likely", 5: "Almost\nCertain"}
impact_labels = {1: "Negligible", 2: "Minor", 3: "Moderate", 4: "Major", 5: "Catastrophic"}

# Color scale: green → yellow → orange → red
risk_colors = ["#2e7d32", "#8bc34a", "#ffeb3b", "#ff9800", "#d32f2f"]

# Plot
plot = (
    ggplot()
    + geom_tile(data=grid_df, mapping=aes(x="impact", y="likelihood", fill="risk_score"), color="white", size=1.5)
    + scale_fill_gradientn(colors=risk_colors, limits=(1, 25), name="Risk Score")
    + geom_point(
        data=risks,
        mapping=aes(x="imp_jitter", y="lk_jitter"),
        color="white",
        fill="#1a1a2e",
        size=5,
        stroke=0.8,
        shape="o",
    )
    + geom_label(
        data=risks,
        mapping=aes(x="imp_jitter", y="lk_jitter", label="risk_name"),
        color="white",
        fill="#1a1a2e",
        size=7,
        nudge_y=0.28,
        alpha=0.85,
        label_padding=0.15,
        label_size=0,
    )
    + scale_x_continuous(breaks=impact_levels, labels=[impact_labels[i] for i in impact_levels], expand=(0, 0.5))
    + scale_y_continuous(
        breaks=likelihood_levels, labels=[likelihood_labels[i] for i in likelihood_levels], expand=(0, 0.5)
    )
    + labs(x="Impact", y="Likelihood", title="heatmap-risk-matrix · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center", weight="bold"),
        axis_title=element_text(size=20, weight="bold"),
        axis_text_x=element_text(size=14),
        axis_text_y=element_text(size=14),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300, width=16, height=9)
