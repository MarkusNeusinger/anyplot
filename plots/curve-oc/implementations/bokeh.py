""" pyplots.ai
curve-oc: Operating Characteristic (OC) Curve
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-19
"""

from math import comb

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import BoxAnnotation, ColumnDataSource, Label, Legend, LegendItem, Span
from bokeh.plotting import figure


# Data - compute binomial CDF for OC curves: P(accept) = sum C(n,k)*p^k*(1-p)^(n-k), k=0..c
fraction_defective = np.linspace(0, 0.15, 200)

plans = [(50, 1), (100, 2), (150, 3)]
oc_curves = []
for n, c in plans:
    pa = np.ones(len(fraction_defective))
    for i, p_val in enumerate(fraction_defective):
        if p_val > 0:
            pa[i] = sum(comb(n, k) * p_val**k * (1 - p_val) ** (n - k) for k in range(c + 1))
    oc_curves.append(pa)

# AQL and LTPD reference points
aql = 0.01
ltpd = 0.08

# Risk values at AQL and LTPD for plan 2 (n=100, c=2)
n2, c2 = plans[1]
pa_at_aql = sum(comb(n2, k) * aql**k * (1 - aql) ** (n2 - k) for k in range(c2 + 1))
alpha = 1 - pa_at_aql
beta = sum(comb(n2, k) * ltpd**k * (1 - ltpd) ** (n2 - k) for k in range(c2 + 1))
pa_at_ltpd = beta

# Colorblind-safe palette: blue, amber, purple (avoids green-orange confusion)
color_1 = "#306998"
color_2 = "#D4820E"
color_3 = "#8B5CF6"
colors = [color_1, color_2, color_3]

p = figure(
    width=4800,
    height=2700,
    title="curve-oc · bokeh · pyplots.ai",
    x_axis_label="Fraction Defective (p)",
    y_axis_label="Probability of Acceptance P(a)",
    x_range=(-0.003, 0.125),
    y_range=(-0.03, 1.06),
    toolbar_location=None,
)

# Shaded risk regions using BoxAnnotation for visual storytelling
producer_risk_zone = BoxAnnotation(left=0, right=aql, fill_color="#306998", fill_alpha=0.04)
p.add_layout(producer_risk_zone)

consumer_risk_zone = BoxAnnotation(left=ltpd, right=0.125, fill_color="#C0392B", fill_alpha=0.04)
p.add_layout(consumer_risk_zone)

# Zone labels for storytelling
zone_reject = Label(
    x=0.090,
    y=0.50,
    text="Rejectable\nQuality",
    text_font_size="20pt",
    text_color="#C0392B",
    text_alpha=0.35,
    text_font_style="italic",
)
p.add_layout(zone_reject)

# OC curves with distinct line dashes for additional differentiation
line_dashes = ["solid", [12, 6], [6, 4, 2, 4]]
lines = []
for i, pa in enumerate(oc_curves):
    source = ColumnDataSource(data={"p": fraction_defective, "pa": pa})
    line = p.line("p", "pa", source=source, line_width=5, line_color=colors[i], line_dash=line_dashes[i])
    lines.append(line)

# AQL vertical reference line
aql_line = Span(
    location=aql, dimension="height", line_color="#555555", line_width=2, line_dash="dashed", line_alpha=0.6
)
p.add_layout(aql_line)

aql_label = Label(
    x=aql + 0.003, y=0.94, text="AQL = 1%", text_font_size="22pt", text_color="#444444", text_font_style="italic"
)
p.add_layout(aql_label)

# LTPD vertical reference line
ltpd_line = Span(
    location=ltpd, dimension="height", line_color="#555555", line_width=2, line_dash="dashed", line_alpha=0.6
)
p.add_layout(ltpd_line)

ltpd_label = Label(
    x=ltpd + 0.003, y=0.94, text="LTPD = 8%", text_font_size="22pt", text_color="#444444", text_font_style="italic"
)
p.add_layout(ltpd_label)

# Producer's risk (alpha) marker on plan 2 at AQL
risk_source_alpha = ColumnDataSource(data={"x": [aql], "y": [pa_at_aql]})
p.scatter(
    "x", "y", source=risk_source_alpha, size=24, color=color_2, line_color="white", line_width=3, marker="diamond"
)

alpha_label = Label(
    x=aql + 0.006,
    y=pa_at_aql - 0.06,
    text=f"Producer's risk α = {alpha:.3f}",
    text_font_size="20pt",
    text_color=color_2,
    text_font_style="bold",
)
p.add_layout(alpha_label)

# Consumer's risk (beta) marker on plan 2 at LTPD
risk_source_beta = ColumnDataSource(data={"x": [ltpd], "y": [pa_at_ltpd]})
p.scatter("x", "y", source=risk_source_beta, size=24, color=color_2, line_color="white", line_width=3, marker="diamond")

beta_label = Label(
    x=ltpd - 0.025,
    y=pa_at_ltpd + 0.06,
    text=f"Consumer's risk β = {beta:.3f}",
    text_font_size="20pt",
    text_color=color_2,
    text_font_style="bold",
)
p.add_layout(beta_label)

# Legend
plan_labels = ["n=50, c=1", "n=100, c=2", "n=150, c=3"]
legend = Legend(
    items=[LegendItem(label=lbl, renderers=[ln]) for lbl, ln in zip(plan_labels, lines, strict=True)],
    location="top_right",
)
legend.label_text_font_size = "22pt"
legend.background_fill_color = "#FFFFFF"
legend.background_fill_alpha = 0.92
legend.border_line_color = "#CCCCCC"
legend.border_line_width = 1
legend.spacing = 14
legend.padding = 20
legend.glyph_width = 50
legend.glyph_height = 30
legend.label_text_color = "#333333"
p.add_layout(legend)

# Style
p.title.text_font_size = "36pt"
p.title.text_font_style = "bold"
p.title.text_color = "#2C3E50"
p.xaxis.axis_label_text_font_size = "26pt"
p.yaxis.axis_label_text_font_size = "26pt"
p.xaxis.axis_label_text_color = "#2C3E50"
p.yaxis.axis_label_text_color = "#2C3E50"
p.xaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_font_size = "20pt"
p.xaxis.major_label_text_color = "#555555"
p.yaxis.major_label_text_color = "#555555"

p.xgrid.grid_line_alpha = 0.12
p.ygrid.grid_line_alpha = 0.12
p.xgrid.grid_line_dash = [6, 4]
p.ygrid.grid_line_dash = [6, 4]
p.xgrid.grid_line_color = "#999999"
p.ygrid.grid_line_color = "#999999"

p.background_fill_color = "#F8F9FA"
p.border_fill_color = "#FFFFFF"
p.outline_line_color = None

p.xaxis.axis_line_color = None
p.yaxis.axis_line_color = None
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.axis_label_text_font_style = "bold"
p.yaxis.axis_label_text_font_style = "bold"

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", title="Operating Characteristic (OC) Curve")
