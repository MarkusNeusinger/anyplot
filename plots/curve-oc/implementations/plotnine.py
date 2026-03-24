""" pyplots.ai
curve-oc: Operating Characteristic (OC) Curve
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-19
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    geom_ribbon,
    geom_vline,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    scale_linetype_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from scipy.stats import binom


# Data
fraction_defective = np.linspace(0, 0.15, 200)

sampling_plans = [
    {"n": 50, "c": 1, "label": "n=50, c=1"},
    {"n": 100, "c": 2, "label": "n=100, c=2"},
    {"n": 150, "c": 3, "label": "n=150, c=3"},
]

rows = []
for plan in sampling_plans:
    prob_accept = binom.cdf(plan["c"], plan["n"], fraction_defective)
    for i, p in enumerate(fraction_defective):
        rows.append({"fraction_defective": p, "probability_acceptance": prob_accept[i], "plan": plan["label"]})

df = pd.DataFrame(rows)
plan_order = [p["label"] for p in sampling_plans]
df["plan"] = pd.Categorical(df["plan"], categories=plan_order, ordered=True)

# Discrimination envelope between the steepest and most gradual curves
envelope_df = df.pivot(index="fraction_defective", columns="plan", values="probability_acceptance").reset_index()
envelope = pd.DataFrame(
    {
        "fraction_defective": envelope_df["fraction_defective"],
        "ymin": envelope_df["n=50, c=1"],
        "ymax": envelope_df["n=150, c=3"],
    }
)

# AQL and LTPD reference points
aql = 0.01
ltpd = 0.08

# Risk points for the primary plan (n=100, c=2)
plan_ref = sampling_plans[1]
alpha = 1 - binom.cdf(plan_ref["c"], plan_ref["n"], aql)
beta = binom.cdf(plan_ref["c"], plan_ref["n"], ltpd)

risk_points = pd.DataFrame(
    [
        {
            "fraction_defective": aql,
            "probability_acceptance": 1 - alpha,
            "label": f"Producer's risk (α={alpha:.2f})",
            "plan": plan_ref["label"],
        },
        {
            "fraction_defective": ltpd,
            "probability_acceptance": beta,
            "label": f"Consumer's risk (β={beta:.2f})",
            "plan": plan_ref["label"],
        },
    ]
)

# Colorblind-safe palette (blue, orange, purple)
colors = {"n=50, c=1": "#306998", "n=100, c=2": "#E0652B", "n=150, c=3": "#9467BD"}
linetypes = {"n=50, c=1": "solid", "n=100, c=2": "dashed", "n=150, c=3": "dashdot"}

# Plot
plot = (
    ggplot(df, aes(x="fraction_defective", y="probability_acceptance", color="plan", linetype="plan"))
    # Shaded risk zones
    + annotate("rect", xmin=0, xmax=aql, ymin=0, ymax=1.05, fill="#306998", alpha=0.06)
    + annotate("rect", xmin=ltpd, xmax=0.15, ymin=0, ymax=1.05, fill="#E0652B", alpha=0.06)
    # Discrimination envelope as ribbon (distinctive plotnine grammar)
    + geom_ribbon(
        aes(x="fraction_defective", ymin="ymin", ymax="ymax"),
        data=envelope,
        inherit_aes=False,
        fill="#306998",
        alpha=0.10,
    )
    + geom_line(size=2, alpha=0.9)
    + geom_vline(xintercept=aql, linetype="dashed", color="#888888", size=0.7, alpha=0.7)
    + geom_vline(xintercept=ltpd, linetype="dashed", color="#888888", size=0.7, alpha=0.7)
    + geom_point(
        aes(x="fraction_defective", y="probability_acceptance"),
        data=risk_points,
        inherit_aes=False,
        size=6,
        color="#E0652B",
        fill="white",
        stroke=1.5,
        shape="o",
    )
    # Zone labels
    + annotate("text", x=0.003, y=0.15, label="Accept\nZone", size=10, color="#306998", alpha=0.6, ha="left")
    + annotate("text", x=0.135, y=0.15, label="Reject\nZone", size=10, color="#E0652B", alpha=0.6, ha="right")
    # AQL/LTPD labels
    + annotate("text", x=aql + 0.003, y=0.06, label="AQL", size=12, color="#555555", fontstyle="italic")
    + annotate("text", x=ltpd + 0.003, y=0.12, label="LTPD", size=12, color="#555555", fontstyle="italic")
    # Risk annotations
    + annotate(
        "text",
        x=risk_points["fraction_defective"].iloc[0] + 0.008,
        y=risk_points["probability_acceptance"].iloc[0],
        label=f"α = {alpha:.2f}",
        size=11,
        color="#E0652B",
        fontweight="bold",
    )
    + annotate(
        "text",
        x=risk_points["fraction_defective"].iloc[1] + 0.008,
        y=risk_points["probability_acceptance"].iloc[1] + 0.06,
        label=f"β = {beta:.2f}",
        size=11,
        color="#E0652B",
        fontweight="bold",
    )
    # Scales with dual encoding (color + linetype)
    + scale_color_manual(values=colors)
    + scale_linetype_manual(values=linetypes)
    + scale_x_continuous(
        breaks=np.arange(0, 0.16, 0.02), labels=lambda lst: [f"{v:.0%}" for v in lst], limits=(0, 0.15)
    )
    + scale_y_continuous(breaks=np.arange(0, 1.1, 0.2), limits=(0, 1.05))
    + labs(
        x="Fraction Defective (p)",
        y="Probability of Acceptance P(a)",
        title="curve-oc · plotnine · pyplots.ai",
        color="Sampling Plan",
        linetype="Sampling Plan",
    )
    + guides(color=guide_legend(override_aes={"size": 4, "alpha": 1}))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, color="#2a2a2a"),
        axis_title=element_text(size=20, weight="bold"),
        axis_text=element_text(size=16, color="#444444"),
        plot_title=element_text(size=24, weight="bold", color="#1a1a1a"),
        legend_title=element_text(size=18, weight="bold"),
        legend_text=element_text(size=16),
        legend_position=(0.78, 0.75),
        legend_background=element_rect(fill="white", alpha=0.85),
        legend_key_size=20,
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#e0e0e0", size=0.4),
        axis_line=element_line(color="#333333", size=0.6),
        plot_background=element_rect(fill="#fafafa", color="none"),
        panel_background=element_rect(fill="#fafafa", color="none"),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
