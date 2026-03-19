"""pyplots.ai
curve-oc: Operating Characteristic (OC) Curve
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-19
"""

import numpy as np
import pandas as pd
from lets_plot import *
from scipy.stats import binom


LetsPlot.setup_html()

# Data - OC curves for acceptance sampling plans
fraction_defective = np.linspace(0, 0.20, 200)

# Sampling plans: (sample_size, acceptance_number) - vary independently
plans = [(50, 1, "n=50, c=1"), (100, 2, "n=100, c=2"), (80, 1, "n=80, c=1"), (150, 3, "n=150, c=3")]

# Quality levels
aql = 0.02  # Acceptable Quality Level
ltpd = 0.10  # Lot Tolerance Percent Defective

# Compute OC curves using binomial CDF
rows = []
for n, c, label in plans:
    pa = binom.cdf(c, n, fraction_defective)
    for p, prob in zip(fraction_defective, pa):
        rows.append({"fraction_defective": p, "probability_acceptance": prob, "plan": label})

df = pd.DataFrame(rows)

# Risk points for primary plan (n=50, c=1)
pa_aql = float(binom.cdf(1, 50, aql))
pa_ltpd = float(binom.cdf(1, 50, ltpd))
alpha = 1 - pa_aql
beta = pa_ltpd

# Risk markers
df_risk = pd.DataFrame({"x": [aql, ltpd], "y": [pa_aql, pa_ltpd], "label": [f"α = {alpha:.3f}", f"β = {beta:.3f}"]})

# Reference lines data
df_vlines = pd.DataFrame(
    {"x": [aql, aql, ltpd, ltpd], "y": [0.0, 1.0, 0.0, 1.0], "group": ["aql", "aql", "ltpd", "ltpd"]}
)

df_hlines = pd.DataFrame(
    {"x": [0.0, aql, 0.0, ltpd], "y": [pa_aql, pa_aql, pa_ltpd, pa_ltpd], "group": ["alpha", "alpha", "beta", "beta"]}
)

# Quality zone backgrounds
df_zones = pd.DataFrame(
    {
        "xmin": [0.0, aql, ltpd],
        "xmax": [aql, ltpd, 0.20],
        "ymin": [0.0, 0.0, 0.0],
        "ymax": [1.0, 1.0, 1.0],
        "fill": ["#E8F5E9", "#FFF8E1", "#FFEBEE"],
        "zone": ["Acceptable\nQuality", "Indifference\nZone", "Rejectable\nQuality"],
        "lx": [0.01, 0.06, 0.15],
    }
)

# Colorblind-safe palette (Okabe-Ito: blue, vermillion, sky blue, teal)
colors = ["#306998", "#D55E00", "#56B4E9", "#009E73"]

plot = (
    ggplot()
    # Quality zone shading
    + geom_rect(
        data=df_zones,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="fill"),
        alpha=0.4,
        color="rgba(0,0,0,0)",
    )
    + scale_fill_identity()
    # Zone labels
    + geom_text(data=df_zones, mapping=aes(x="lx", label="zone"), y=0.5, size=10, color="#AAAAAA", fontface="italic")
    # Vertical reference lines (AQL, LTPD)
    + geom_line(data=df_vlines, mapping=aes(x="x", y="y", group="group"), linetype="dotted", color="#999999", size=0.7)
    # Horizontal risk reference lines
    + geom_line(data=df_hlines, mapping=aes(x="x", y="y", group="group"), linetype="dashed", color="#BBBBBB", size=0.5)
    # OC curves with formatted tooltips
    + geom_line(
        data=df,
        mapping=aes(x="fraction_defective", y="probability_acceptance", color="plan"),
        size=2.2,
        tooltips=layer_tooltips()
        .format("fraction_defective", ".3f")
        .format("probability_acceptance", ".3f")
        .line("@plan")
        .line("p = @fraction_defective")
        .line("P(accept) = @probability_acceptance"),
    )
    # Risk point markers
    + geom_point(data=df_risk, mapping=aes(x="x", y="y"), size=7, shape=21, fill="#DC2626", color="white", stroke=2.5)
    # Alpha risk label (above-right of point)
    + geom_text(
        data=df_risk.iloc[:1],
        mapping=aes(x="x", y="y", label="label"),
        size=12,
        color="#DC2626",
        fontface="bold",
        nudge_x=0.015,
        nudge_y=0.05,
    )
    # Beta risk label (right of point, offset to avoid LTPD label)
    + geom_text(
        data=df_risk.iloc[1:2],
        mapping=aes(x="x", y="y", label="label"),
        size=12,
        color="#DC2626",
        fontface="bold",
        nudge_x=0.025,
        nudge_y=0.03,
    )
    # AQL label near bottom of its vertical line
    + geom_text(
        data=pd.DataFrame({"x": [aql], "label": ["AQL"]}),
        mapping=aes(x="x", label="label"),
        y=0.08,
        size=13,
        color="#444444",
        fontface="bold",
    )
    # LTPD label positioned above beta to avoid crowding
    + geom_text(
        data=pd.DataFrame({"x": [ltpd], "label": ["LTPD"]}),
        mapping=aes(x="x", label="label"),
        y=0.12,
        size=13,
        color="#444444",
        fontface="bold",
    )
    + scale_color_manual(values=colors)
    + scale_x_continuous(breaks=[0.0, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18, 0.20], limits=[0.0, 0.20])
    + scale_y_continuous(limits=[0.0, 1.05], breaks=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    + labs(
        x="Fraction Defective (p)",
        y="Probability of Acceptance P(a)",
        title="curve-oc · letsplot · pyplots.ai",
        subtitle="Comparing acceptance sampling plans — producer's & consumer's risk at AQL=0.02, LTPD=0.10",
        color="Sampling Plan",
    )
    + theme(
        axis_title=element_text(size=20, color="#333333"),
        axis_text=element_text(size=16, color="#555555"),
        plot_title=element_text(size=24, color="#222222", face="bold"),
        plot_subtitle=element_text(size=16, color="#666666", face="italic"),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18, face="bold"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor_x=element_blank(),
        panel_grid_major_y=element_line(color="#EEEEEE", size=0.4),
        panel_grid_minor_y=element_blank(),
        panel_background=element_rect(fill="white", color="white"),
        plot_background=element_rect(fill="white", color="white"),
        axis_line_x=element_line(color="#AAAAAA", size=0.8),
        axis_line_y=element_line(color="#AAAAAA", size=0.8),
        axis_ticks=element_line(color="#CCCCCC", size=0.4),
        legend_position=[0.82, 0.88],
        legend_background=element_rect(fill="white", color="#EEEEEE", size=0.5),
        plot_margin=[30, 30, 30, 20],
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
