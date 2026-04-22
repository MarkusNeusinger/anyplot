""" pyplots.ai
funnel-meta-analysis: Meta-Analysis Funnel Plot for Publication Bias
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-15
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Span
from bokeh.plotting import figure


# Data - Meta-analysis of 15 RCTs comparing drug vs placebo (log odds ratios)
np.random.seed(42)

n_studies = 15
true_effect = 0.3

std_errors = np.concatenate(
    [np.random.uniform(0.05, 0.15, 5), np.random.uniform(0.15, 0.30, 6), np.random.uniform(0.30, 0.50, 4)]
)

effect_sizes = true_effect + np.random.normal(0, 1, n_studies) * std_errors
# Add slight positive bias to small studies (simulating publication bias)
small_study_mask = std_errors > 0.30
effect_sizes[small_study_mask] += np.random.uniform(0.05, 0.20, small_study_mask.sum())

# Summary effect (inverse-variance weighted)
weights = 1 / std_errors**2
summary_effect = np.sum(weights * effect_sizes) / np.sum(weights)

# Marker sizes proportional to study weight (inverse variance)
normalized_weights = weights / weights.max()
marker_sizes = 22 + normalized_weights * 30  # range 22-52px

# Color intensity by precision (more precise = darker)
marker_alphas = 0.55 + normalized_weights * 0.40  # range 0.55-0.95

# Determine which studies fall outside the funnel (potential outliers)
expected_lower = summary_effect - 1.96 * std_errors
expected_upper = summary_effect + 1.96 * std_errors
outside_funnel = (effect_sizes < expected_lower) | (effect_sizes > expected_upper)
marker_colors = np.where(outside_funnel, "#C05746", "#306998")

# Funnel confidence limits
se_range = np.linspace(0, 0.55, 100)
upper_limit = summary_effect + 1.96 * se_range
lower_limit = summary_effect - 1.96 * se_range

# Study labels
studies = [f"Study {i + 1}" for i in range(n_studies)]

# Plot
source = ColumnDataSource(
    data={
        "effect_size": effect_sizes,
        "std_error": std_errors,
        "study": studies,
        "weight": np.round(weights, 1),
        "marker_size": marker_sizes,
        "marker_alpha": marker_alphas,
        "marker_color": marker_colors.tolist(),
        "status": ["Outside funnel" if o else "Inside funnel" for o in outside_funnel],
    }
)

p = figure(
    width=4800,
    height=2700,
    title="funnel-meta-analysis · bokeh · pyplots.ai",
    x_axis_label="Log Odds Ratio",
    y_axis_label="Standard Error",
    y_range=(0.60, -0.02),
    x_range=(-0.85, 1.15),
    tools="",
    toolbar_location=None,
)

# Funnel confidence region (pseudo 95% CI)
funnel_xs = np.concatenate([lower_limit, upper_limit[::-1]]).tolist()
funnel_ys = np.concatenate([se_range, se_range[::-1]]).tolist()
p.patch(
    funnel_xs,
    funnel_ys,
    fill_color="#306998",
    fill_alpha=0.15,
    line_color="#306998",
    line_alpha=0.5,
    line_width=2.5,
    line_dash="dashed",
)

# Summary effect line
p.add_layout(Span(location=summary_effect, dimension="height", line_color="#306998", line_width=4, line_alpha=0.85))

# Null effect line (0 for log scale)
p.add_layout(
    Span(location=0, dimension="height", line_color="#888888", line_width=2.5, line_dash="dashed", line_alpha=0.7)
)

# Study points - sized by weight for visual hierarchy
scatter = p.scatter(
    x="effect_size",
    y="std_error",
    source=source,
    size="marker_size",
    fill_alpha="marker_alpha",
    fill_color="marker_color",
    line_color="white",
    line_width=2.5,
)

# HoverTool - distinctive Bokeh interactive feature
hover = HoverTool(
    renderers=[scatter],
    tooltips=[
        ("Study", "@study"),
        ("Effect Size", "@effect_size{0.3f}"),
        ("Std Error", "@std_error{0.3f}"),
        ("Weight", "@weight{0.1f}"),
        ("Status", "@status"),
    ],
)
p.add_tools(hover)

# Summary effect label - positioned in visible area
p.add_layout(
    Label(
        x=summary_effect + 0.03,
        y=0.03,
        text=f"Summary: {summary_effect:.2f}",
        text_font_size="22pt",
        text_color="#306998",
        text_font_style="bold",
        text_align="left",
        text_baseline="top",
    )
)

# Null label
p.add_layout(
    Label(
        x=0.03,
        y=0.03,
        text="Null (0)",
        text_font_size="22pt",
        text_color="#888888",
        text_font_style="bold",
        text_align="left",
        text_baseline="top",
    )
)

# Asymmetry annotation for storytelling
p.add_layout(
    Label(
        x=0.55,
        y=0.42,
        text="← Asymmetry suggests publication bias",
        text_font_size="26pt",
        text_color="#C05746",
        text_font_style="bold",
        text_align="left",
        text_baseline="middle",
    )
)

# Legend annotations for color coding
n_outside = int(outside_funnel.sum())
p.add_layout(
    Label(
        x=-0.78,
        y=0.53,
        text=f"● Inside funnel ({n_studies - n_outside} studies)",
        text_font_size="20pt",
        text_color="#306998",
        text_font_style="normal",
        text_align="left",
        text_baseline="middle",
    )
)
p.add_layout(
    Label(
        x=-0.78,
        y=0.49,
        text=f"● Outside funnel ({n_outside} studies)",
        text_font_size="20pt",
        text_color="#C05746",
        text_font_style="normal",
        text_align="left",
        text_baseline="middle",
    )
)

# Style
p.title.text_font_size = "36pt"
p.title.align = "center"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

p.xaxis.axis_line_color = "#999999"
p.yaxis.axis_line_color = "#999999"
p.xaxis.axis_line_width = 1
p.yaxis.axis_line_width = 1
p.xaxis.major_tick_line_color = "#999999"
p.yaxis.major_tick_line_color = "#999999"
p.xgrid.grid_line_alpha = 0.15
p.ygrid.grid_line_alpha = 0.15
p.xgrid.grid_line_width = 1
p.ygrid.grid_line_width = 1

p.outline_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.background_fill_color = "#FAFAFA"

# Save
export_png(p, filename="plot.png")

output_file("plot.html")
save(p)
