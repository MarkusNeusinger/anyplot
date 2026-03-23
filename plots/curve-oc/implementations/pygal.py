""" pyplots.ai
curve-oc: Operating Characteristic (OC) Curve
Library: pygal 3.1.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-19
"""

from math import comb

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# Data — tighter x-range for practical readability
fraction_defective = np.linspace(0, 0.15, 150)

# Sampling plans: (sample_size, acceptance_number, label)
plans = [(50, 1, "n=50, c=1"), (50, 2, "n=50, c=2"), (100, 2, "n=100, c=2"), (100, 3, "n=100, c=3")]

# Compute OC curves — P(accept) = sum C(n,k) * p^k * (1-p)^(n-k) for k=0..c
oc_curves = {}
for n, c, label in plans:
    p = fraction_defective
    oc_curves[label] = sum(comb(n, k) * p**k * (1 - p) ** (n - k) for k in range(c + 1))

# Quality levels
aql = 0.01  # Acceptable Quality Level (1%)
ltpd = 0.08  # Lot Tolerance Percent Defective (8%)

# Risks for reference plan n=100, c=2
pa_at_aql = float(sum(comb(100, k) * aql**k * (1 - aql) ** (100 - k) for k in range(3)))
alpha = 1 - pa_at_aql
beta = float(sum(comb(100, k) * ltpd**k * (1 - ltpd) ** (100 - k) for k in range(3)))

# Colorblind-safe palette — steel blue, orange, teal, purple avoid deuteranopia confusion
C_PLAN1 = "#306998"  # Steel blue (Python blue)
C_PLAN2 = "#E68A00"  # Warm orange
C_PLAN3 = "#17BECF"  # Teal — distinct from blue under colorblindness
C_PLAN4 = "#9467BD"  # Muted purple
C_REF = "#888888"  # Neutral gray for reference lines
C_RISK = "#C44E52"  # Muted red for risk markers

custom_style = Style(
    background="#FAFAFA",
    plot_background="#F4F3EE",
    foreground="#333333",
    foreground_strong="#1A1A1A",
    foreground_subtle="#DAD8D2",
    colors=(C_PLAN1, C_PLAN2, C_PLAN3, C_PLAN4, C_REF, C_REF, C_RISK, C_RISK),
    title_font_size=48,
    label_font_size=30,
    major_label_font_size=28,
    legend_font_size=26,
    value_font_size=18,
    stroke_width=3,
    font_family="sans-serif",
    tooltip_font_size=24,
    opacity=0.85,
    opacity_hover=1.0,
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
    fill=False,
    show_x_guides=False,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=24,
    truncate_legend=-1,
    interpolate="hermite",
    interpolation_parameters={"type": "cardinal", "c": 0.75},
    range=(0, 1.05),
    xrange=(0, 0.15),
    x_value_formatter=lambda x: f"{x:.0%}",
    value_formatter=lambda y: f"{y:.2f}",
    allow_interruptions=True,
    x_labels=[0, 0.01, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.15],
    y_labels=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
    y_labels_major_count=3,
    show_minor_y_labels=True,
    js=[],
    print_values=False,
    margin_top=40,
    margin_bottom=80,
    margin_left=60,
    spacing=20,
    tooltip_fancy_mode=True,
    tooltip_border_radius=6,
    explicit_size=True,
)

# OC curves — reference plan (n=100, c=2) drawn thickest for visual hierarchy
ref_plan = "n=100, c=2"
for _n, _c, label in plans:
    curve_data = list(zip(fraction_defective.tolist(), oc_curves[label].tolist(), strict=True))
    width = 12 if label == ref_plan else 6
    chart.add(
        label,
        curve_data,
        show_dots=False,
        stroke_style={"width": width, "linecap": "round", "linejoin": "round"},
        formatter=lambda v: f"P(accept)={v[1]:.3f}" if isinstance(v, (list, tuple)) else f"{v:.3f}",
    )

# AQL vertical reference line — thin dashed, subordinate to curves
chart.add(
    f"AQL ({aql:.0%})",
    [(aql, 0), (aql, 1.05)],
    show_dots=False,
    stroke_style={"width": 3, "dasharray": "14, 8", "linecap": "round"},
)

# LTPD vertical reference line
chart.add(
    f"LTPD ({ltpd:.0%})",
    [(ltpd, 0), (ltpd, 1.05)],
    show_dots=False,
    stroke_style={"width": 3, "dasharray": "14, 8", "linecap": "round"},
)

# Producer's risk point (alpha at AQL for n=100, c=2)
chart.add(
    f"\u03b1={alpha:.1%} (producer risk)",
    [(aql, pa_at_aql)],
    stroke=False,
    show_dots=True,
    dots_size=22,
    formatter=lambda v: f"\u03b1={1 - v[1]:.1%}" if isinstance(v, (list, tuple)) else f"{v:.3f}",
)

# Consumer's risk point (beta at LTPD for n=100, c=2)
chart.add(
    f"\u03b2={beta:.1%} (consumer risk)",
    [(ltpd, beta)],
    stroke=False,
    show_dots=True,
    dots_size=22,
    formatter=lambda v: f"\u03b2={v[1]:.1%}" if isinstance(v, (list, tuple)) else f"{v:.3f}",
)

# Render SVG natively, convert to PNG via cairosvg
svg = chart.render(is_unicode=True)
with open("plot.html", "w") as f:
    f.write(svg)
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to="plot.png", dpi=96)
