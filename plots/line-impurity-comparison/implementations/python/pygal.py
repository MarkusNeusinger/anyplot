""" pyplots.ai
line-impurity-comparison: Gini Impurity vs Entropy Comparison
Library: pygal 3.1.0 | Python 3.14.3
Quality: 83/100 | Created: 2026-02-17
"""

import numpy as np
import pygal
from pygal.style import Style


# Data — 200 points for smooth curves across full [0, 1] probability range
p = np.linspace(0, 1, 200)
gini = 2 * p * (1 - p)

with np.errstate(divide="ignore", invalid="ignore"):
    entropy = -p * np.log2(p) - (1 - p) * np.log2(1 - p)
entropy = np.nan_to_num(entropy, nan=0.0)

# Absolute difference between curves — for storytelling fill
diff = np.abs(entropy - gini)

# Shared font family
_font = "Helvetica, Arial, sans-serif"

# Style — refined palette: series order is diff-fill, Gini, Entropy, dashed, dot, dot
custom_style = Style(
    background="white",
    plot_background="#fafafa",
    foreground="#2a2a2a",
    foreground_strong="#111111",
    foreground_subtle="#e2e2e2",
    colors=(
        "#d6eaf8",  # 1: diff fill — very pale blue, subtle
        "#1a5276",  # 2: Gini — deep navy blue
        "#d35400",  # 3: Entropy — warm burnt orange
        "#888888",  # 4: vertical dashed line — neutral gray
        "#1a5276",  # 5: Gini peak dot — matches Gini
        "#d35400",  # 6: Entropy peak dot — matches Entropy
    ),
    opacity="1",
    opacity_hover="1",
    stroke_opacity="1",
    stroke_opacity_hover="1",
    stroke_width=8,
    stroke_width_hover=10,
    guide_stroke_color="#ececec",
    guide_stroke_dasharray="3, 5",
    major_guide_stroke_color="#d5d5d5",
    major_guide_stroke_dasharray="0",
    title_font_size=72,
    label_font_size=46,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=38,
    value_label_font_size=38,
    tooltip_font_size=32,
    font_family=_font,
    label_font_family=_font,
    major_label_font_family=_font,
    legend_font_family=_font,
    title_font_family=_font,
    value_font_family=_font,
    value_label_font_family=_font,
)

# Chart — tighter y-range, balanced margins
chart = pygal.XY(
    width=4800,
    height=2700,
    title="line-impurity-comparison \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Probability p (range 0 to 1)",
    y_title="Impurity Measure (normalized)",
    style=custom_style,
    show_dots=False,
    fill=False,
    show_y_guides=True,
    show_x_guides=False,
    show_minor_x_labels=False,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=28,
    truncate_legend=-1,
    xrange=(0, 1),
    range=(0, 1.05),
    x_labels=[0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0],
    y_labels=[0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0],
    show_y_labels=True,
    x_label_rotation=0,
    margin=80,
    margin_bottom=140,
    margin_left=180,
    margin_right=80,
    margin_top=100,
    interpolate="cubic",
    show_x_labels=True,
    print_values=False,
    print_labels=True,
    print_zeroes=False,
    js=[],
)

# Convert to pygal XY point lists
gini_points = list(zip(p.tolist(), gini.tolist(), strict=True))
entropy_points = list(zip(p.tolist(), entropy.tolist(), strict=True))

# Series 1: Shaded region showing |Entropy − Gini| divergence (subtle fill)
diff_points = [(p[i], diff[i]) for i in range(0, len(p), 4)]
chart.add("\u0394 |Entropy \u2212 Gini|", diff_points, fill=True, show_dots=False, stroke_style={"width": 0})

# Series 2: Gini impurity — deep navy, prominent
chart.add("Gini: 2p(1\u2212p)", gini_points, stroke_style={"width": 9})

# Series 3: Entropy — burnt orange, prominent
chart.add(
    "Entropy: \u2212p log\u2082p \u2212 (1\u2212p) log\u2082(1\u2212p)", entropy_points, stroke_style={"width": 9}
)

# Series 4: Vertical dashed line at p=0.5 (hidden from legend)
chart.add(None, [(0.5, 0.0), (0.5, 1.0)], stroke_style={"width": 2, "dasharray": "10, 8"})

# Series 5: Gini peak annotation dot
chart.add(
    None, [{"value": (0.5, 0.5), "label": "Gini peak = 0.50"}], stroke_style={"width": 0}, show_dots=True, dots_size=16
)

# Series 6: Entropy peak annotation dot
chart.add(
    None,
    [{"value": (0.5, 1.0), "label": "Entropy peak = 1.00"}],
    stroke_style={"width": 0},
    show_dots=True,
    dots_size=16,
)

chart.render_to_file("plot.svg")
chart.render_to_png("plot.png")
