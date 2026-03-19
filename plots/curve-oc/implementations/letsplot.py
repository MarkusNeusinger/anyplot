"""pyplots.ai
curve-oc: Operating Characteristic (OC) Curve
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-03-19
"""

import numpy as np
import pandas as pd
from lets_plot import *
from scipy.stats import binom


LetsPlot.setup_html()

# Data - OC curves for acceptance sampling plans
fraction_defective = np.linspace(0, 0.20, 200)

# Sampling plans: (sample_size, acceptance_number)
plans = [(50, 1, "n=50, c=1"), (100, 2, "n=100, c=2"), (150, 3, "n=150, c=3")]

# Quality levels for annotation
aql = 0.02  # Acceptable Quality Level
ltpd = 0.10  # Lot Tolerance Percent Defective

# Compute OC curves using binomial CDF
rows = []
for n, c, label in plans:
    prob_accept = binom.cdf(c, n, fraction_defective)
    for p, pa in zip(fraction_defective, prob_accept):
        rows.append({"fraction_defective": p, "probability_acceptance": pa, "plan": label})

df = pd.DataFrame(rows)

# Risk points for the primary plan (n=50, c=1)
alpha = 1 - binom.cdf(1, 50, aql)  # Producer's risk at AQL
beta = binom.cdf(1, 50, ltpd)  # Consumer's risk at LTPD

# Reference lines data
df_aql_v = pd.DataFrame({"x": [aql, aql], "y": [0.0, 1.0]})
df_ltpd_v = pd.DataFrame({"x": [ltpd, ltpd], "y": [0.0, 1.0]})

# Risk point markers
pa_at_aql = binom.cdf(1, 50, aql)
pa_at_ltpd = binom.cdf(1, 50, ltpd)

df_risk = pd.DataFrame(
    {
        "x": [aql, ltpd],
        "y": [pa_at_aql, pa_at_ltpd],
        "label": [f"α = {alpha:.3f}", f"β = {beta:.3f}"],
        "risk": ["Producer's Risk", "Consumer's Risk"],
    }
)

# Horizontal dashed lines from risk points to y-axis
df_risk_h = pd.DataFrame(
    {
        "x": [0.0, aql, 0.0, ltpd],
        "y": [pa_at_aql, pa_at_aql, pa_at_ltpd, pa_at_ltpd],
        "risk": ["Producer's Risk", "Producer's Risk", "Consumer's Risk", "Consumer's Risk"],
    }
)

# AQL and LTPD label data
df_labels = pd.DataFrame({"x": [aql, ltpd], "y": [-0.06, -0.06], "label": ["AQL", "LTPD"]})

# Colors
colors = ["#306998", "#E07A3A", "#2CA02C"]

# Plot
plot = (
    ggplot()
    # AQL and LTPD vertical reference lines
    + geom_line(data=df_aql_v, mapping=aes(x="x", y="y"), linetype="dotted", color="#888888", size=0.8)
    + geom_line(data=df_ltpd_v, mapping=aes(x="x", y="y"), linetype="dotted", color="#888888", size=0.8)
    # Horizontal risk lines
    + geom_line(data=df_risk_h, mapping=aes(x="x", y="y", group="risk"), linetype="dashed", color="#AAAAAA", size=0.6)
    # OC curves
    + geom_line(
        data=df,
        mapping=aes(x="fraction_defective", y="probability_acceptance", color="plan"),
        size=2.2,
        tooltips=layer_tooltips()
        .line("@plan")
        .line("Fraction defective: @fraction_defective")
        .line("P(accept): @probability_acceptance"),
    )
    # Risk point markers
    + geom_point(data=df_risk, mapping=aes(x="x", y="y"), size=6, shape=21, fill="#DC2626", color="white", stroke=2)
    # Risk labels
    + geom_text(
        data=df_risk, mapping=aes(x="x", y="y", label="label"), size=12, nudge_x=0.012, nudge_y=0.04, color="#DC2626"
    )
    # AQL / LTPD labels
    + geom_text(data=df_labels, mapping=aes(x="x", y="y", label="label"), size=13, color="#555555", fontface="bold")
    + scale_color_manual(values=colors)
    + scale_x_continuous(breaks=[0.0, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18, 0.20], limits=[0.0, 0.20])
    + scale_y_continuous(limits=[-0.1, 1.05], breaks=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    + labs(
        x="Fraction Defective (p)",
        y="Probability of Acceptance P(a)",
        title="curve-oc · letsplot · pyplots.ai",
        color="Sampling Plan",
    )
    + theme(
        axis_title=element_text(size=20, color="#333333"),
        axis_text=element_text(size=16, color="#555555"),
        plot_title=element_text(size=24, color="#222222", face="bold"),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
        panel_grid_major_x=element_blank(),
        panel_grid_minor_x=element_blank(),
        panel_grid_major_y=element_line(color="#E8E8E8", size=0.5),
        panel_grid_minor_y=element_blank(),
        panel_background=element_rect(fill="white", color="white"),
        plot_background=element_rect(fill="white", color="white"),
        axis_line_x=element_line(color="#AAAAAA", size=0.8),
        axis_line_y=element_line(color="#AAAAAA", size=0.8),
        axis_ticks=element_line(color="#AAAAAA", size=0.5),
        legend_position=[0.82, 0.88],
        legend_background=element_rect(fill="white", color="white", size=0),
        plot_margin=[30, 30, 30, 20],
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
