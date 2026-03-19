"""pyplots.ai
curve-oc: Operating Characteristic (OC) Curve
Library: pygal | Python 3.13
Quality: pending | Created: 2026-03-19
"""

from math import comb

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# Data
fraction_defective = np.linspace(0, 0.20, 150)


# Binomial CDF: P(X <= c) for X ~ Bin(n, p)
def binom_cdf(c, n, p):
    p = np.asarray(p, dtype=float)
    result = np.zeros_like(p)
    for k in range(c + 1):
        result += comb(n, k) * p**k * (1 - p) ** (n - k)
    return result


# Sampling plans: (sample_size, acceptance_number)
plans = [(50, 1, "n=50, c=1"), (50, 2, "n=50, c=2"), (100, 2, "n=100, c=2"), (100, 3, "n=100, c=3")]

# Compute OC curves
oc_curves = {}
for n, c, label in plans:
    prob_accept = binom_cdf(c, n, fraction_defective)
    oc_curves[label] = prob_accept

# Quality levels
aql = 0.01  # Acceptable Quality Level (1%)
ltpd = 0.08  # Lot Tolerance Percent Defective (8%)

# Risks for plan n=100, c=2
alpha = float(1 - binom_cdf(2, 100, aql))  # Producer's risk at AQL
beta = float(binom_cdf(2, 100, ltpd))  # Consumer's risk at LTPD

# Style
C_PLAN1 = "#306998"
C_PLAN2 = "#E68A00"
C_PLAN3 = "#2CA02C"
C_PLAN4 = "#9467BD"
C_REF = "#999999"
C_RISK = "#D62728"

custom_style = Style(
    background="white",
    plot_background="#FAFAFA",
    foreground="#2A2A2A",
    foreground_strong="#1A1A1A",
    foreground_subtle="#E0DEDA",
    colors=(C_PLAN1, C_PLAN2, C_PLAN3, C_PLAN4, C_REF, C_REF, C_RISK, C_RISK),
    title_font_size=40,
    label_font_size=26,
    major_label_font_size=24,
    legend_font_size=22,
    value_font_size=16,
    stroke_width=3,
    font_family="sans-serif",
)

chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="curve-oc \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Fraction Defective (p)",
    y_title="Probability of Acceptance P(accept)",
    show_dots=False,
    dots_size=0,
    stroke=True,
    show_x_guides=False,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=20,
    truncate_legend=-1,
    range=(0, 1.05),
    xrange=(0, 0.20),
    allow_interruptions=True,
    js=[],
    print_values=False,
)

# Plot OC curves
for _n, _c, label in plans:
    curve_data = list(zip(fraction_defective.tolist(), oc_curves[label].tolist(), strict=True))
    chart.add(label, curve_data, show_dots=False, stroke_style={"width": 6, "linecap": "round", "linejoin": "round"})

# AQL vertical reference line
chart.add(f"AQL = {aql:.0%}", [(aql, 0), (aql, 1.05)], show_dots=False, stroke_style={"width": 3, "dasharray": "12, 8"})

# LTPD vertical reference line
chart.add(
    f"LTPD = {ltpd:.0%}", [(ltpd, 0), (ltpd, 1.05)], show_dots=False, stroke_style={"width": 3, "dasharray": "12, 8"}
)

# Producer's risk point (alpha at AQL for n=100, c=2)
pa_at_aql = float(binom_cdf(2, 100, aql))
chart.add(f"\u03b1 = {alpha:.3f} (n=100,c=2)", [(aql, pa_at_aql)], stroke=False, show_dots=True, dots_size=14)

# Consumer's risk point (beta at LTPD for n=100, c=2)
chart.add(f"\u03b2 = {beta:.3f} (n=100,c=2)", [(ltpd, beta)], stroke=False, show_dots=True, dots_size=14)

# Render
svg = chart.render(is_unicode=True)
with open("plot.html", "w") as f:
    f.write(svg)
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to="plot.png", dpi=96)
