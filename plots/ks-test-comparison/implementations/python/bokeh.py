""" pyplots.ai
ks-test-comparison: Kolmogorov-Smirnov Plot for Distribution Comparison
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 93/100 | Created: 2026-02-17
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import Band, ColumnDataSource, Label, Legend, LegendItem, NumeralTickFormatter, Range1d, Span
from bokeh.plotting import figure
from bokeh.resources import CDN
from scipy import stats


# Data — Credit scoring: Good vs Bad customer score distributions
np.random.seed(42)
good_scores = np.random.beta(5, 2, 400) * 600 + 300  # Good customers: higher scores
bad_scores = np.random.beta(2, 4, 350) * 600 + 300  # Bad customers: lower scores

# Compute ECDFs using a concise helper pattern
good_sorted = np.sort(good_scores)
good_ecdf = np.arange(1, len(good_sorted) + 1) / len(good_sorted)

bad_sorted = np.sort(bad_scores)
bad_ecdf = np.arange(1, len(bad_sorted) + 1) / len(bad_sorted)

# K-S test
ks_stat, p_value = stats.ks_2samp(good_scores, bad_scores)

# Find point of maximum divergence
all_values = np.sort(np.concatenate([good_scores, bad_scores]))
good_ecdf_at = np.searchsorted(good_sorted, all_values, side="right") / len(good_sorted)
bad_ecdf_at = np.searchsorted(bad_sorted, all_values, side="right") / len(bad_sorted)
max_idx = np.argmax(np.abs(good_ecdf_at - bad_ecdf_at))
max_x = all_values[max_idx]
max_y_good = good_ecdf_at[max_idx]
max_y_bad = bad_ecdf_at[max_idx]

# Build step function arrays — interleave x,y pairs for step rendering
good_x_step = np.concatenate([[good_sorted[0]], np.repeat(good_sorted, 2)[1:]])
good_y_step = np.concatenate([[0], np.repeat(good_ecdf, 2)[:-1]])
bad_x_step = np.concatenate([[bad_sorted[0]], np.repeat(bad_sorted, 2)[1:]])
bad_y_step = np.concatenate([[0], np.repeat(bad_ecdf, 2)[:-1]])

good_source = ColumnDataSource(data={"x": good_x_step, "y": good_y_step})
bad_source = ColumnDataSource(data={"x": bad_x_step, "y": bad_y_step})

# Build shaded region between ECDFs at maximum divergence point (storytelling)
ks_y_lower = min(max_y_good, max_y_bad)
ks_y_upper = max(max_y_good, max_y_bad)

# Plot
p = figure(
    width=4800,
    height=2700,
    title="ks-test-comparison \u00b7 bokeh \u00b7 pyplots.ai",
    x_axis_label="Credit Score",
    y_axis_label="Cumulative Proportion",
    y_range=Range1d(-0.03, 1.08),
    toolbar_location=None,
)

# Shaded band between ECDFs near the max divergence region for visual storytelling
# Create a narrow band around the max divergence point to highlight the gap
band_mask = (all_values >= max_x - 15) & (all_values <= max_x + 15)
band_x = all_values[band_mask]
band_upper = np.maximum(good_ecdf_at[band_mask], bad_ecdf_at[band_mask])
band_lower = np.minimum(good_ecdf_at[band_mask], bad_ecdf_at[band_mask])
band_source = ColumnDataSource(data={"x": band_x, "upper": band_upper, "lower": band_lower})
band = Band(
    base="x", upper="upper", lower="lower", source=band_source, fill_color="#D62728", fill_alpha=0.15, line_color=None
)
p.add_layout(band)

# Draw ECDF step lines with differentiated styling for visual hierarchy
good_line = p.line(x="x", y="y", source=good_source, line_width=6, line_color="#306998", alpha=0.95)
bad_line = p.line(x="x", y="y", source=bad_source, line_width=5, line_color="#E8833A", alpha=0.85, line_dash=[14, 7])

# Highlight maximum divergence with a vertical segment
ks_segment_source = ColumnDataSource(data={"x0": [max_x], "y0": [ks_y_lower], "x1": [max_x], "y1": [ks_y_upper]})
ks_line = p.segment(
    x0="x0", y0="y0", x1="x1", y1="y1", source=ks_segment_source, line_width=6, line_color="#D62728", line_dash="solid"
)

# Endpoint markers for the K-S segment — diamond markers for distinction
ks_marker_source = ColumnDataSource(data={"x": [max_x, max_x], "y": [ks_y_lower, ks_y_upper]})
ks_markers = p.scatter(x="x", y="y", source=ks_marker_source, size=22, color="#D62728", marker="diamond")

# Annotation: K-S statistic and p-value with background box
p_text = "p < 0.001" if p_value < 0.001 else f"p = {p_value:.4f}"
ks_label = Label(
    x=max_x,
    y=(ks_y_lower + ks_y_upper) / 2,
    text=f"D = {ks_stat:.3f},  {p_text}",
    text_font_size="24pt",
    text_color="#D62728",
    text_font_style="bold",
    text_baseline="middle",
    x_offset=25,
    background_fill_color="white",
    background_fill_alpha=0.8,
)
p.add_layout(ks_label)

# Subtle vertical reference line at max divergence point (Bokeh Span model)
max_div_span = Span(
    location=max_x, dimension="height", line_color="#D62728", line_alpha=0.15, line_width=2, line_dash="dotted"
)
p.add_layout(max_div_span)

# Legend — use add_layout with explicit "center" place for correct positioning
legend = Legend(
    items=[
        LegendItem(label="Good Customers (ECDF)", renderers=[good_line]),
        LegendItem(label="Bad Customers (ECDF)", renderers=[bad_line]),
        LegendItem(label="Max Distance (K-S Statistic)", renderers=[ks_line]),
    ],
    location="top_left",
)
legend.label_text_font_size = "22pt"
legend.background_fill_color = "#f8f8f8"
legend.background_fill_alpha = 0.9
legend.border_line_color = "#cccccc"
legend.border_line_alpha = 0.5
legend.border_line_width = 2
legend.glyph_height = 30
legend.glyph_width = 40
legend.padding = 20
legend.spacing = 12
legend.margin = 25
p.add_layout(legend, "center")

# Typography and styling — publication-grade
p.title.text_font_size = "28pt"
p.title.text_font_style = "bold"
p.title.text_color = "#333333"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = "#444444"
p.yaxis.axis_label_text_color = "#444444"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = "#555555"
p.yaxis.major_label_text_color = "#555555"

# Remove spines / axis lines for clean look
p.xaxis.axis_line_color = "#cccccc"
p.yaxis.axis_line_color = "#cccccc"
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.major_tick_line_color = "#cccccc"
p.yaxis.major_tick_line_color = "#cccccc"

# Subtle grid
p.xgrid.grid_line_color = "#e0e0e0"
p.ygrid.grid_line_color = "#e0e0e0"
p.xgrid.grid_line_alpha = 0.4
p.ygrid.grid_line_alpha = 0.4

p.outline_line_color = None
p.background_fill_color = "white"
p.border_fill_color = "white"

# Y-axis tick formatter for proportions
p.yaxis.formatter = NumeralTickFormatter(format="0.0")

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="ks-test-comparison \u00b7 bokeh \u00b7 pyplots.ai")
