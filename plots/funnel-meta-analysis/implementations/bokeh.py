""" pyplots.ai
funnel-meta-analysis: Meta-Analysis Funnel Plot for Publication Bias
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 81/100 | Created: 2026-03-15
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Label, Span
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

# Funnel confidence limits
se_range = np.linspace(0, 0.55, 100)
upper_limit = summary_effect + 1.96 * se_range
lower_limit = summary_effect - 1.96 * se_range

# Study labels
studies = [f"Study {i + 1}" for i in range(n_studies)]

# Plot
source = ColumnDataSource(data={"effect_size": effect_sizes, "std_error": std_errors, "study": studies})

p = figure(
    width=4800,
    height=2700,
    title="funnel-meta-analysis · bokeh · pyplots.ai",
    x_axis_label="Log Odds Ratio",
    y_axis_label="Standard Error",
    y_range=(0.60, -0.02),
    x_range=(-0.8, 1.4),
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
    fill_alpha=0.08,
    line_color="#306998",
    line_alpha=0.4,
    line_width=2,
    line_dash="dashed",
)

# Summary effect line
p.add_layout(Span(location=summary_effect, dimension="height", line_color="#306998", line_width=3, line_alpha=0.7))

# Null effect line (0 for log scale)
p.add_layout(
    Span(location=0, dimension="height", line_color="#999999", line_width=2, line_dash="dashed", line_alpha=0.6)
)

# Study points
p.scatter(
    x="effect_size",
    y="std_error",
    source=source,
    size=22,
    color="#306998",
    alpha=0.85,
    line_color="white",
    line_width=2.5,
)

# Summary effect label
p.add_layout(
    Label(
        x=summary_effect + 0.02,
        y=0.56,
        text=f"Summary: {summary_effect:.2f}",
        text_font_size="20pt",
        text_color="#306998",
        text_align="left",
        text_baseline="middle",
    )
)

# Null label
p.add_layout(
    Label(
        x=0.02,
        y=0.56,
        text="Null (0)",
        text_font_size="20pt",
        text_color="#999999",
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

p.xaxis.axis_line_color = "#333333"
p.yaxis.axis_line_color = "#333333"
p.xgrid.grid_line_alpha = 0.15
p.ygrid.grid_line_alpha = 0.15
p.xgrid.grid_line_width = 1
p.ygrid.grid_line_width = 1

p.outline_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Save
export_png(p, filename="plot.png")

output_file("plot.html")
save(p)
