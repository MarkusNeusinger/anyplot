""" pyplots.ai
funnel-meta-analysis: Meta-Analysis Funnel Plot for Publication Bias
Library: pygal 3.1.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-15
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
# Slight rightward asymmetry to suggest possible publication bias
effect_sizes = np.array(
    [-0.52, -0.38, -0.71, -0.45, -0.30, -0.62, -0.48, -0.41, -0.55, -0.35, -0.80, -0.43, -0.28, -0.50, -0.65]
)
std_errors = np.array([0.08, 0.12, 0.18, 0.10, 0.15, 0.22, 0.14, 0.09, 0.20, 0.16, 0.25, 0.11, 0.19, 0.13, 0.24])

# Summary (pooled) effect size
pooled_effect = -0.47

# Separate studies by precision for visual hierarchy
# High precision (SE < 0.15) cluster tightly near pooled effect
# Low precision (SE >= 0.15) show the asymmetric scatter suggesting bias
high_precision_mask = std_errors < 0.15
low_precision_mask = ~high_precision_mask

# Style with cohesive palette - both CI boundaries share the same color
custom_style = Style(
    background="white",
    plot_background="#FAFAFA",
    foreground="#2D2D2D",
    foreground_strong="#1A1A1A",
    foreground_subtle="#E0E0E0",
    colors=(
        "#7BA7CC",  # 0: CI left boundary (muted blue)
        "#7BA7CC",  # 1: CI right boundary (same muted blue)
        "#444444",  # 2: Pooled effect line (dark grey)
        "#AAAAAA",  # 3: Null effect line (light grey)
        "#306998",  # 4: High-precision studies (Python blue, bold)
        "#E8792B",  # 5: Low-precision studies (orange, draws attention to asymmetry)
    ),
    title_font_size=44,
    label_font_size=26,
    major_label_font_size=22,
    legend_font_size=22,
    value_font_size=18,
    tooltip_font_size=22,
    stroke_width=3,
    font_family="Arial",
)

# Chart
chart = pygal.XY(
    width=4800,
    height=2700,
    title="funnel-meta-analysis · pygal · pyplots.ai",
    x_title="Log Odds Ratio (Effect Size)",
    y_title="Standard Error (precision ↑)",
    style=custom_style,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=18,
    dots_size=12,
    stroke=False,
    show_y_guides=True,
    show_x_guides=False,
    margin=60,
    inverse_y_axis=True,
    truncate_legend=-1,
    x_value_formatter=lambda x: f"{x:.2f}",
    y_value_formatter=lambda y: f"{y:.2f}",
    print_values=False,
    print_zeroes=False,
)

# Funnel boundaries (pseudo 95% CI) - left boundary
funnel_left = [(float(pooled_effect - 1.96 * se), float(se)) for se in np.linspace(0, 0.30, 50)]
chart.add("95% Pseudo CI", funnel_left, stroke=True, show_dots=False, stroke_style={"width": 4, "dasharray": "12, 6"})

# Funnel boundaries - right boundary (same legend group via None, now same color)
funnel_right = [(float(pooled_effect + 1.96 * se), float(se)) for se in np.linspace(0, 0.30, 50)]
chart.add(None, funnel_right, stroke=True, show_dots=False, stroke_style={"width": 4, "dasharray": "12, 6"})

# Vertical line at pooled effect
chart.add(
    f"Pooled Effect (LOR = {pooled_effect:.2f})",
    [(float(pooled_effect), 0.0), (float(pooled_effect), 0.30)],
    stroke=True,
    show_dots=False,
    stroke_style={"width": 5},
)

# Vertical dashed line at null effect (0)
chart.add(
    "Null Effect (LOR = 0)",
    [(0.0, 0.0), (0.0, 0.30)],
    stroke=True,
    show_dots=False,
    stroke_style={"width": 3, "dasharray": "8, 8"},
)

# High-precision studies (large, closer to pooled effect)
hp_points = []
for name, es, se in zip(
    np.array(study_names)[high_precision_mask],
    effect_sizes[high_precision_mask],
    std_errors[high_precision_mask],
    strict=True,
):
    hp_points.append({"value": (float(es), float(se)), "label": f"{name}: LOR={es:.2f}, SE={se:.2f}"})
chart.add("High-precision studies", hp_points, stroke=False, dots_size=16)

# Low-precision studies (smaller, show the asymmetric scatter)
lp_points = []
for name, es, se in zip(
    np.array(study_names)[low_precision_mask],
    effect_sizes[low_precision_mask],
    std_errors[low_precision_mask],
    strict=True,
):
    lp_points.append({"value": (float(es), float(se)), "label": f"{name}: LOR={es:.2f}, SE={se:.2f}"})
chart.add("Low-precision studies (bias region)", lp_points, stroke=False, dots_size=12)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
