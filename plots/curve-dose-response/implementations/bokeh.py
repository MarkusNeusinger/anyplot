""" pyplots.ai
curve-dose-response: Pharmacological Dose-Response Curve
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-18
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import Band, ColumnDataSource, Label, Legend, LegendItem, Span, Whisker
from bokeh.plotting import figure
from scipy.optimize import curve_fit


# Data
np.random.seed(42)

concentrations = np.array([1e-9, 3e-9, 1e-8, 3e-8, 1e-7, 3e-7, 1e-6, 3e-6, 1e-5, 3e-5, 1e-4])


def logistic_4pl(x, bottom, top, ec50, hill):
    return bottom + (top - bottom) / (1 + (ec50 / x) ** hill)


# Compound A - agonist with EC50 ~100 nM
true_params_a = [5, 95, 1e-7, 1.2]
response_a_mean = logistic_4pl(concentrations, *true_params_a)
response_a_sem = np.random.uniform(2, 5, len(concentrations))
response_a_raw = response_a_mean + np.random.normal(0, 3, len(concentrations))

# Compound B - less potent agonist with EC50 ~1 uM
true_params_b = [8, 85, 1e-6, 1.5]
response_b_mean = logistic_4pl(concentrations, *true_params_b)
response_b_sem = np.random.uniform(2, 6, len(concentrations))
response_b_raw = response_b_mean + np.random.normal(0, 3, len(concentrations))

# Fit 4PL to noisy data
popt_a, pcov_a = curve_fit(logistic_4pl, concentrations, response_a_raw, p0=[0, 100, 1e-7, 1], maxfev=10000)
popt_b, pcov_b = curve_fit(logistic_4pl, concentrations, response_b_raw, p0=[0, 100, 1e-6, 1], maxfev=10000)

# Smooth fitted curves
conc_smooth = np.logspace(-9.5, -3.5, 300)
fit_a = logistic_4pl(conc_smooth, *popt_a)
fit_b = logistic_4pl(conc_smooth, *popt_b)

# 95% CI for Compound A via parameter covariance
n_samples = 200
ci_samples = np.zeros((n_samples, len(conc_smooth)))
for i in range(n_samples):
    sampled_params = np.random.multivariate_normal(popt_a, pcov_a)
    ci_samples[i] = logistic_4pl(conc_smooth, *sampled_params)
ci_lower_a = np.percentile(ci_samples, 2.5, axis=0)
ci_upper_a = np.percentile(ci_samples, 97.5, axis=0)

# EC50 values from fit
ec50_a = popt_a[2]
ec50_b = popt_b[2]
half_response_a = popt_a[0] + (popt_a[1] - popt_a[0]) / 2
half_response_b = popt_b[0] + (popt_b[1] - popt_b[0]) / 2

# Potency fold-difference for storytelling
fold_diff = ec50_b / ec50_a

# Plot
colors_a = "#306998"
colors_b = "#E8833A"

p = figure(
    width=4800,
    height=2700,
    title="curve-dose-response · bokeh · pyplots.ai",
    x_axis_label="Concentration (M)",
    y_axis_label="Response (%)",
    x_axis_type="log",
    x_range=(3e-10, 3e-4),
    y_range=(-5, 115),
    toolbar_location=None,
)

# Confidence band for Compound A
band_source = ColumnDataSource(data={"conc": conc_smooth, "lower": ci_lower_a, "upper": ci_upper_a})
band = Band(
    base="conc",
    lower="lower",
    upper="upper",
    source=band_source,
    fill_alpha=0.15,
    fill_color=colors_a,
    line_color=colors_a,
    line_alpha=0.0,
)
p.add_layout(band)

# Fitted curves
source_a = ColumnDataSource(data={"conc": conc_smooth, "response": fit_a})
source_b = ColumnDataSource(data={"conc": conc_smooth, "response": fit_b})

line_a = p.line("conc", "response", source=source_a, line_width=5, line_color=colors_a)
line_b = p.line("conc", "response", source=source_b, line_width=5, line_color=colors_b)

# Data points with error bars
pts_source_a = ColumnDataSource(
    data={
        "conc": concentrations,
        "response": response_a_raw,
        "upper": response_a_raw + response_a_sem,
        "lower": response_a_raw - response_a_sem,
    }
)
pts_source_b = ColumnDataSource(
    data={
        "conc": concentrations,
        "response": response_b_raw,
        "upper": response_b_raw + response_b_sem,
        "lower": response_b_raw - response_b_sem,
    }
)

whisker_a = Whisker(
    base="conc", upper="upper", lower="lower", source=pts_source_a, line_color=colors_a, line_width=3, line_alpha=0.6
)
whisker_a.upper_head.line_color = colors_a
whisker_a.upper_head.size = 12
whisker_a.lower_head.line_color = colors_a
whisker_a.lower_head.size = 12
p.add_layout(whisker_a)

whisker_b = Whisker(
    base="conc", upper="upper", lower="lower", source=pts_source_b, line_color=colors_b, line_width=3, line_alpha=0.6
)
whisker_b.upper_head.line_color = colors_b
whisker_b.upper_head.size = 12
whisker_b.lower_head.line_color = colors_b
whisker_b.lower_head.size = 12
p.add_layout(whisker_b)

scatter_a = p.scatter(
    "conc", "response", source=pts_source_a, size=18, color=colors_a, line_color="white", line_width=2
)
scatter_b = p.scatter(
    "conc", "response", source=pts_source_b, size=18, color=colors_b, line_color="white", line_width=2
)

# EC50 reference lines - Compound A
ec50_vline_a = Span(
    location=ec50_a, dimension="height", line_color=colors_a, line_width=2, line_dash="dashed", line_alpha=0.45
)
p.add_layout(ec50_vline_a)
ec50_hline_src_a = ColumnDataSource(data={"x": [3e-10, ec50_a], "y": [half_response_a, half_response_a]})
p.line("x", "y", source=ec50_hline_src_a, line_color=colors_a, line_width=2, line_dash="dashed", line_alpha=0.45)

# EC50 reference lines - Compound B
ec50_vline_b = Span(
    location=ec50_b, dimension="height", line_color=colors_b, line_width=2, line_dash="dashed", line_alpha=0.45
)
p.add_layout(ec50_vline_b)
ec50_hline_src_b = ColumnDataSource(data={"x": [3e-10, ec50_b], "y": [half_response_b, half_response_b]})
p.line("x", "y", source=ec50_hline_src_b, line_color=colors_b, line_width=2, line_dash="dashed", line_alpha=0.45)

# Top and bottom asymptote dashed lines
top_asymptote = Span(
    location=popt_a[1], dimension="width", line_color="#999999", line_width=2, line_dash="dotted", line_alpha=0.35
)
bottom_asymptote = Span(
    location=popt_a[0], dimension="width", line_color="#999999", line_width=2, line_dash="dotted", line_alpha=0.35
)
p.add_layout(top_asymptote)
p.add_layout(bottom_asymptote)

# Asymptote labels - positioned at left side near the asymptote lines
top_asym_label = Label(
    x=5e-10,
    y=popt_a[1] + 2,
    text=f"Top asymptote ({popt_a[1]:.0f}%)",
    text_font_size="20pt",
    text_color="#888888",
    text_font_style="italic",
)
bottom_asym_label = Label(
    x=5e-10,
    y=popt_a[0] - 7,
    text=f"Bottom asymptote ({popt_a[0]:.0f}%)",
    text_font_size="20pt",
    text_color="#888888",
    text_font_style="italic",
)
p.add_layout(top_asym_label)
p.add_layout(bottom_asym_label)

# EC50 annotations with potency context
ec50_a_label = Label(
    x=ec50_a * 2.5,
    y=half_response_a + 6,
    text=f"EC\u2085\u2080 = {ec50_a:.1e} M",
    text_font_size="26pt",
    text_color=colors_a,
    text_font_style="bold",
)
ec50_b_label = Label(
    x=ec50_b * 2.5,
    y=half_response_b + 6,
    text=f"EC\u2085\u2080 = {ec50_b:.1e} M",
    text_font_size="26pt",
    text_color=colors_b,
    text_font_style="bold",
)
p.add_layout(ec50_a_label)
p.add_layout(ec50_b_label)

# Potency comparison annotation - placed in lower-right open space
potency_label = Label(
    x=2e-5,
    y=25,
    text=f"Compound A is {fold_diff:.0f}\u00d7 more potent",
    text_font_size="22pt",
    text_color="#555555",
    text_font_style="italic",
)
p.add_layout(potency_label)

# Legend - positioned at top-right in clear space above curves
legend = Legend(
    items=[
        LegendItem(label="Compound A (Hill = {:.1f})".format(popt_a[3]), renderers=[line_a, scatter_a]),
        LegendItem(label="Compound B (Hill = {:.1f})".format(popt_b[3]), renderers=[line_b, scatter_b]),
    ],
    location="top_right",
)
legend.label_text_font_size = "22pt"
legend.background_fill_color = "#FFFFFF"
legend.background_fill_alpha = 0.92
legend.border_line_color = "#CCCCCC"
legend.border_line_width = 1
legend.spacing = 14
legend.padding = 20
legend.glyph_width = 40
legend.glyph_height = 30
p.add_layout(legend)

# Style - publication-quality with removed spines
p.title.text_font_size = "36pt"
p.title.text_font_style = "bold"
p.title.text_color = "#333333"
p.xaxis.axis_label_text_font_size = "26pt"
p.yaxis.axis_label_text_font_size = "26pt"
p.xaxis.axis_label_text_color = "#444444"
p.yaxis.axis_label_text_color = "#444444"
p.xaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_font_size = "20pt"
p.xaxis.major_label_text_color = "#555555"
p.yaxis.major_label_text_color = "#555555"

p.xgrid.grid_line_alpha = 0.15
p.ygrid.grid_line_alpha = 0.15
p.xgrid.grid_line_dash = [6, 4]
p.ygrid.grid_line_dash = [6, 4]
p.xgrid.grid_line_color = "#AAAAAA"
p.ygrid.grid_line_color = "#AAAAAA"

p.background_fill_color = "#F8F9FA"
p.border_fill_color = "#FFFFFF"
p.outline_line_color = None

# Remove spines for clean, modern look
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
save(p, filename="plot.html", title="Dose-Response Curve")
