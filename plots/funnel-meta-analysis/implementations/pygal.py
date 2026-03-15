""" pyplots.ai
funnel-meta-analysis: Meta-Analysis Funnel Plot for Publication Bias
Library: pygal 3.1.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-15
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
# High-precision studies cluster near pooled effect; low-precision studies
# show rightward asymmetry (missing negative small studies = publication bias)
# Martinez 2023 (index 12) is clearly outside CI, demonstrating an outlier
effect_sizes = np.array(
    [-0.50, -0.42, -0.68, -0.46, -0.25, -0.55, -0.48, -0.44, -0.38, -0.20, -0.72, -0.43, -0.08, -0.51, -0.58]
)
std_errors = np.array([0.08, 0.11, 0.17, 0.09, 0.16, 0.21, 0.13, 0.07, 0.22, 0.18, 0.26, 0.10, 0.23, 0.12, 0.24])

# Summary (pooled) effect size
pooled_effect = -0.47

# Separate studies by precision for visual hierarchy
high_precision_mask = std_errors < 0.15
low_precision_mask = ~high_precision_mask

# Publication-quality style with refined typography and palette
custom_style = Style(
    background="#FFFFFF",
    plot_background="#F8FAFB",
    foreground="#2B3A4A",
    foreground_strong="#1A2636",
    foreground_subtle="#E4E8EC",
    colors=(
        "#6FA8C7",  # 0: CI left boundary (muted teal-blue)
        "#6FA8C7",  # 1: CI right boundary (matched)
        "#1A2636",  # 2: Pooled effect line (dark navy)
        "#9CA8B4",  # 3: Null effect line (muted grey)
        "#306998",  # 4: High-precision studies (Python blue)
        "#D95F02",  # 5: Low-precision studies (strong orange, colorblind-safe)
    ),
    title_font_size=48,
    label_font_size=28,
    major_label_font_size=24,
    legend_font_size=22,
    value_font_size=18,
    tooltip_font_size=22,
    stroke_width=3,
    font_family="Helvetica, Arial, sans-serif",
    opacity=".9",
    opacity_hover="1",
)

# Custom y-axis labels for clean tick positioning
y_labels_list = [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]

# Chart with refined configuration
chart = pygal.XY(
    width=4800,
    height=2700,
    title="funnel-meta-analysis \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Log Odds Ratio (Effect Size)",
    y_title="Standard Error (precision \u2191)",
    style=custom_style,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=20,
    dots_size=14,
    stroke=False,
    show_y_guides=True,
    show_x_guides=False,
    margin=50,
    inverse_y_axis=True,
    truncate_legend=-1,
    x_value_formatter=lambda x: f"{x:.2f}",
    y_value_formatter=lambda y: f"{y:.2f}",
    y_labels=y_labels_list,
    print_values=False,
    print_zeroes=False,
    range=(0, 0.30),
    xrange=(-1.10, 0.18),
    spacing=25,
    tooltip_border_radius=8,
    explicit_size=True,
)

# Funnel boundaries (pseudo 95% CI) - left boundary
se_values = np.linspace(0, 0.30, 60)
funnel_left = [(float(pooled_effect - 1.96 * se), float(se)) for se in se_values]
chart.add(
    "95% Pseudo CI",
    funnel_left,
    stroke=True,
    show_dots=False,
    stroke_style={"width": 5, "dasharray": "14, 6"},
    formatter=lambda x: "",
)

# Right CI boundary (suppressed from legend via None)
funnel_right = [(float(pooled_effect + 1.96 * se), float(se)) for se in se_values]
chart.add(
    None,
    funnel_right,
    stroke=True,
    show_dots=False,
    stroke_style={"width": 5, "dasharray": "14, 6"},
    formatter=lambda x: "",
)

# Vertical line at pooled effect (prominent, solid)
chart.add(
    f"Pooled Effect (LOR = {pooled_effect:.2f})",
    [(float(pooled_effect), 0.0), (float(pooled_effect), 0.30)],
    stroke=True,
    show_dots=False,
    stroke_style={"width": 7},
    formatter=lambda x: "",
)

# Vertical dashed line at null effect (0)
chart.add(
    "Null Effect (LOR = 0)",
    [(0.0, 0.0), (0.0, 0.30)],
    stroke=True,
    show_dots=False,
    stroke_style={"width": 3, "dasharray": "10, 8"},
    formatter=lambda x: "",
)

# High-precision studies (larger markers, tightly clustered near pooled effect)
hp_points = []
for name, es, se in zip(
    np.array(study_names)[high_precision_mask],
    effect_sizes[high_precision_mask],
    std_errors[high_precision_mask],
    strict=True,
):
    hp_points.append({"value": (float(es), float(se)), "label": f"{name}: LOR={es:.2f}, SE={se:.2f}"})
chart.add("High-precision studies", hp_points, stroke=False, dots_size=22, formatter=lambda x: "")

# Low-precision studies (medium markers, asymmetric scatter revealing bias)
lp_points = []
for name, es, se in zip(
    np.array(study_names)[low_precision_mask],
    effect_sizes[low_precision_mask],
    std_errors[low_precision_mask],
    strict=True,
):
    lp_points.append({"value": (float(es), float(se)), "label": f"{name}: LOR={es:.2f}, SE={se:.2f}"})
chart.add("Low-precision studies (bias region)", lp_points, stroke=False, dots_size=16, formatter=lambda x: "")

# Render outputs
chart.render_to_png("plot.png", dpi=192)
chart.render_to_file("plot.html")
