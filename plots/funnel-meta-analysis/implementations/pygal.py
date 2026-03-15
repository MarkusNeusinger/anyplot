"""pyplots.ai
funnel-meta-analysis: Meta-Analysis Funnel Plot for Publication Bias
Library: pygal | Python 3.13
Quality: pending | Created: 2026-03-15
"""

import numpy as np
import pygal
from pygal.style import Style


# Data: 15 RCTs comparing drug vs placebo (log odds ratios)
np.random.seed(42)
study_names = [
    "Adams 2018",
    "Baker 2019",
    "Chen 2019",
    "Davis 2020",
    "Evans 2020",
    "Foster 2021",
    "Garcia 2021",
    "Harris 2022",
    "Ibrahim 2022",
    "Jones 2022",
    "Kim 2023",
    "Lee 2023",
    "Martinez 2023",
    "Nelson 2024",
    "O'Brien 2024",
]

# Effect sizes (log odds ratios) and standard errors
# Larger studies (small SE) cluster near the pooled effect
# Smaller studies (large SE) scatter more widely
# Slight asymmetry to suggest possible publication bias
effect_sizes = np.array(
    [-0.52, -0.38, -0.71, -0.45, -0.30, -0.62, -0.48, -0.41, -0.55, -0.35, -0.80, -0.43, -0.28, -0.50, -0.65]
)
std_errors = np.array([0.08, 0.12, 0.18, 0.10, 0.15, 0.22, 0.14, 0.09, 0.20, 0.16, 0.25, 0.11, 0.19, 0.13, 0.24])

# Summary (pooled) effect size
pooled_effect = -0.47

# Pseudo 95% confidence limits: pooled_effect +/- 1.96 * SE
se_range = np.linspace(0, 0.30, 100)
ci_upper = pooled_effect + 1.96 * se_range
ci_lower = pooled_effect - 1.96 * se_range

# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#cccccc",
    colors=("#306998", "#E8792B", "#999999", "#999999"),
    title_font_size=48,
    label_font_size=28,
    major_label_font_size=24,
    legend_font_size=24,
    value_font_size=20,
    tooltip_font_size=24,
    stroke_width=3,
    font_family="Arial",
)

# Chart - XY scatter for funnel plot
chart = pygal.XY(
    width=4800,
    height=2700,
    title="funnel-meta-analysis · pygal · pyplots.ai",
    x_title="Log Odds Ratio (Effect Size)",
    y_title="Standard Error",
    style=custom_style,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    dots_size=14,
    stroke=False,
    show_y_guides=True,
    show_x_guides=True,
    margin=80,
    inverse_y_axis=True,
    truncate_legend=-1,
)

# Funnel boundaries (pseudo 95% CI) - left boundary
funnel_left_points = [(float(pooled_effect - 1.96 * se), float(se)) for se in np.linspace(0, 0.30, 50)]
chart.add(
    "95% Pseudo CI", funnel_left_points, stroke=True, show_dots=False, stroke_style={"width": 3, "dasharray": "10, 5"}
)

# Funnel boundaries - right boundary
funnel_right_points = [(float(pooled_effect + 1.96 * se), float(se)) for se in np.linspace(0, 0.30, 50)]
chart.add(None, funnel_right_points, stroke=True, show_dots=False, stroke_style={"width": 3, "dasharray": "10, 5"})

# Vertical line at pooled effect
chart.add(
    "Pooled Effect (LOR = {:.2f})".format(pooled_effect),
    [(float(pooled_effect), 0.0), (float(pooled_effect), 0.30)],
    stroke=True,
    show_dots=False,
    stroke_style={"width": 4},
)

# Vertical dashed line at null effect (0)
chart.add(
    "Null Effect (LOR = 0)",
    [(0.0, 0.0), (0.0, 0.30)],
    stroke=True,
    show_dots=False,
    stroke_style={"width": 3, "dasharray": "8, 8"},
)

# Study points with tooltips
study_points = []
for name, es, se in zip(study_names, effect_sizes, std_errors, strict=True):
    study_points.append({"value": (float(es), float(se)), "label": f"{name}: LOR={es:.2f}, SE={se:.2f}"})
chart.add("Studies", study_points, stroke=False, dots_size=14)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
