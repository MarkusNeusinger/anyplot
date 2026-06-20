""" anyplot.ai
curve-oc: Operating Characteristic (OC) Curve
Library: plotnine 0.15.7 | Python 3.13.14
Quality: 84/100 | Updated: 2026-06-20
"""

import os

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


# Theme tokens — Imprint palette
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data
fraction_defective = np.linspace(0, 0.15, 200)

sampling_plans = [
    {"n": 75, "c": 2, "label": "n=75, c=2"},
    {"n": 120, "c": 1, "label": "n=120, c=1"},
    {"n": 200, "c": 2, "label": "n=200, c=2"},
]

rows = []
for plan in sampling_plans:
    prob_accept = binom.cdf(plan["c"], plan["n"], fraction_defective)
    for i, p in enumerate(fraction_defective):
        rows.append({"fraction_defective": p, "probability_acceptance": prob_accept[i], "plan": plan["label"]})

df = pd.DataFrame(rows)
plan_order = [p["label"] for p in sampling_plans]
df["plan"] = pd.Categorical(df["plan"], categories=plan_order, ordered=True)

# Discrimination envelope between most lenient (n=75,c=2) and most strict (n=200,c=2)
envelope_df = df.pivot(index="fraction_defective", columns="plan", values="probability_acceptance").reset_index()
envelope = pd.DataFrame(
    {
        "fraction_defective": envelope_df["fraction_defective"],
        "ymin": envelope_df["n=200, c=2"],
        "ymax": envelope_df["n=75, c=2"],
    }
)

# AQL and LTPD reference points
aql = 0.01
ltpd = 0.08

# Risk metrics for reference plan (n=75, c=2)
plan_ref = sampling_plans[0]
alpha_risk = 1 - binom.cdf(plan_ref["c"], plan_ref["n"], aql)
beta_risk = binom.cdf(plan_ref["c"], plan_ref["n"], ltpd)

risk_points = pd.DataFrame(
    [
        {"fraction_defective": aql, "probability_acceptance": 1 - alpha_risk},
        {"fraction_defective": ltpd, "probability_acceptance": beta_risk},
    ]
)

colors = {p["label"]: c for p, c in zip(sampling_plans, IMPRINT[:3], strict=False)}
linetypes = {"n=75, c=2": "solid", "n=120, c=1": "dashed", "n=200, c=2": "dashdot"}

# Plot
plot = (
    ggplot(df, aes(x="fraction_defective", y="probability_acceptance", color="plan", linetype="plan"))
    # Shaded quality zones
    + annotate("rect", xmin=0, xmax=aql, ymin=0, ymax=1.05, fill=IMPRINT[0], alpha=0.09)
    + annotate("rect", xmin=ltpd, xmax=0.15, ymin=0, ymax=1.05, fill=IMPRINT[4], alpha=0.09)
    # Discrimination envelope ribbon — shows range of plan discrimination power
    + geom_ribbon(
        aes(x="fraction_defective", ymin="ymin", ymax="ymax"),
        data=envelope,
        inherit_aes=False,
        fill=IMPRINT[0],
        alpha=0.10,
    )
    # AQL / LTPD reference lines
    + geom_vline(xintercept=aql, linetype="dashed", color=INK_SOFT, size=0.5, alpha=0.8)
    + geom_vline(xintercept=ltpd, linetype="dashed", color=INK_SOFT, size=0.5, alpha=0.8)
    # OC curves
    + geom_line(size=1.0, alpha=0.9)
    # Producer's and consumer's risk markers on reference plan
    + geom_point(
        aes(x="fraction_defective", y="probability_acceptance"),
        data=risk_points,
        inherit_aes=False,
        size=3,
        color=IMPRINT[0],
        fill=PAGE_BG,
        stroke=1,
        shape="o",
    )
    # AQL / LTPD axis labels
    + annotate("text", x=aql + 0.002, y=0.05, label="AQL", size=3.0, color=INK_MUTED, fontstyle="italic")
    + annotate("text", x=ltpd + 0.002, y=0.11, label="LTPD", size=3.0, color=INK_MUTED, fontstyle="italic")
    # Risk annotations
    + annotate(
        "text",
        x=aql + 0.007,
        y=1 - alpha_risk - 0.07,
        label=f"α = {alpha_risk:.2f}",
        size=2.8,
        color=IMPRINT[0],
        fontweight="bold",
    )
    + annotate(
        "text",
        x=ltpd + 0.007,
        y=beta_risk + 0.06,
        label=f"β = {beta_risk:.2f}",
        size=2.8,
        color=IMPRINT[0],
        fontweight="bold",
    )
    + scale_color_manual(values=colors)
    + scale_linetype_manual(values=linetypes)
    + scale_x_continuous(
        breaks=np.arange(0, 0.16, 0.02), labels=lambda lst: [f"{v:.0%}" for v in lst], limits=(0, 0.15)
    )
    + scale_y_continuous(breaks=np.arange(0, 1.1, 0.2), limits=(0, 1.05))
    + labs(
        x="Fraction Defective (p)",
        y="Probability of Acceptance P(a)",
        title="curve-oc · python · plotnine · anyplot.ai",
        color="Sampling Plan",
        linetype="Sampling Plan",
    )
    + guides(color=guide_legend(override_aes={"size": 4, "alpha": 1}))
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7, color=INK_SOFT),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=12, color=INK),
        legend_title=element_text(size=8, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_position=(0.78, 0.78),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.15),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
