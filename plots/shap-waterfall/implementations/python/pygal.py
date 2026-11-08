""" anyplot.ai
shap-waterfall: SHAP Waterfall Plot for Feature Attribution
Library: pygal 3.1.3 | Python 3.14.10
Quality: 89/100 | Updated: 2026-11-08
"""

import os
import sys


# Prevent this file (pygal.py) from shadowing the installed pygal package
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or os.getcwd()) != _here]

import numpy as np  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint semantic anchors: matte red pushes the prediction up, blue pushes it down
POSITIVE = "#AE3030"
NEGATIVE = "#4467A3"

# Data – customer churn prediction SHAP explanation
feature_names = [
    "Monthly Charges",
    "Contract Type",
    "Tenure",
    "Online Security",
    "Internet Service",
    "Tech Support",
    "Num. of Services",
    "Payment Method",
    "Device Protection",
    "Streaming TV",
]
shap_raw = [0.20, 0.15, -0.12, -0.10, 0.08, -0.06, 0.05, 0.04, -0.03, 0.02]
base_value = 0.25
final_value = round(base_value + sum(shap_raw), 4)  # 0.48

# Sort ascending by abs magnitude (pygal draws the first label at the bottom, the last at the top),
# so the chain climbs from the base value at the bottom to the prediction next to the largest bar on top
idx = sorted(range(len(shap_raw)), key=lambda i: abs(shap_raw[i]))
features = [feature_names[i] for i in idx]
shap_vals = [shap_raw[i] for i in idx]

# Cumulative chain from the base value to the prediction
chain = base_value + np.concatenate([[0.0], np.cumsum(shap_vals)])
left_edges = np.minimum(chain[:-1], chain[1:])

# Value axis: covers the chain only, with room right of the top bar for its value label
step = 10 ** np.floor(np.log10(chain.max() - chain.min()))
axis_lo = np.floor(chain.min() / step) * step
axis_hi = np.ceil((chain.max() + 0.25 * step) / (step / 2)) * (step / 2)
ticks = [t for t in np.arange(axis_lo, axis_hi + 1e-9, step) if min(abs(t - base_value), abs(t - final_value)) > 0.3 * step]
references = [
    {"value": base_value, "label": f"Base {base_value:.2f}"},
    {"value": final_value, "label": f"Prediction {final_value:.2f}"},
]

# Waterfall stacking: a transparent spacer up to each segment's left edge, then the segment itself
spacer_data = [{"value": float(edge), "style": "fill: none; stroke: none"} for edge in left_edges]
shap_data = [
    {"value": abs(v), "color": POSITIVE if v >= 0 else NEGATIVE, "label": f"{v:+.2f}"} for v in shap_vals
]

# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=(PAGE_BG, POSITIVE),
    value_colors=(INK, INK),
    opacity=1,
    opacity_hover=0.85,
    guide_stroke_color=RULE,
    guide_stroke_dasharray="none",
    major_guide_stroke_color=INK,
    major_guide_stroke_dasharray="18,10",
    title_font_size=56,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=40,
    value_label_font_size=40,
    tooltip_font_size=36,
    stroke_width=0,
)

# HorizontalStackedBar enables waterfall stacking via spacer + visible series
chart = pygal.HorizontalStackedBar(
    width=3200,
    height=1800,
    style=custom_style,
    title="Customer Churn Prediction · shap-waterfall · python · pygal · anyplot.ai",
    x_title="Predicted churn probability (base value + SHAP contributions)",
    y_title="Feature (ordered by |SHAP value|)",
    show_legend=False,
    show_y_guides=False,
    show_x_guides=False,
    range=(float(axis_lo), float(axis_hi)),
    print_labels=True,
    print_values=False,
    print_values_position="top",
    truncate_label=-1,
    margin=40,
    spacing=30,
    css=(
        "file://style.css",
        "file://graph.css",
        # Segment values sit just right of each segment; the reference guides are drawn heavier than the grid;
        # title_font_size sizes the axis titles, the plot title is set larger and bold here
        "inline:.text-overlay text.label { text-anchor: start; }",
        "inline:.axis .major.guide.line { stroke-width: 4px; } .axis text.major { font-weight: bold; }",
        "inline:.plot_title { font-size: 62px !important; font-weight: bold; }",
    ),
)

chart.x_labels = features
# Value-axis ticks plus the base value and the prediction as labelled reference guides
chart.y_labels = [{"value": float(t), "label": f"{t:.1f}"} for t in ticks] + references
chart.y_labels_major = [r["value"] for r in references]

chart.add("", spacer_data)
chart.add("SHAP contribution", shap_data)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
