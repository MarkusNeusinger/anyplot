""" pyplots.ai
probability-weibull: Weibull Probability Plot for Reliability Analysis
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-11
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Span
from bokeh.plotting import figure
from bokeh.resources import CDN
from scipy import stats


# Data - Turbine blade fatigue-life data (hours to failure)
np.random.seed(42)
n_failures = 25
n_censored = 5
n_total = n_failures + n_censored

# Generate Weibull-distributed failure times (shape=2.5, scale=5000)
true_beta = 2.5
true_eta = 5000
failure_times = np.sort(stats.weibull_min.rvs(true_beta, scale=true_eta, size=n_failures))

# Censored observations (suspended tests, typically at higher times)
censored_times = np.sort(np.random.uniform(4000, 7000, size=n_censored))

# Combine and compute median rank plotting positions for failures only
# Using Bernard's approximation: (i - 0.3) / (n + 0.4)
ranks = np.arange(1, n_failures + 1)
median_rank = (ranks - 0.3) / (n_total + 0.4)

# Weibull linearized y-axis: ln(-ln(1 - F))
weibull_y = np.log(-np.log(1 - median_rank))
log_failure_times = np.log(failure_times)

# Fit line in linearized space: weibull_y = beta * ln(t) - beta * ln(eta)
slope_fit, intercept_fit, r_value, _, _ = stats.linregress(log_failure_times, weibull_y)
beta_fit = slope_fit
eta_fit = np.exp(-intercept_fit / beta_fit)
r_squared = r_value**2

# Fitted line data
log_t_line = np.linspace(np.log(failure_times.min()) - 0.5, np.log(failure_times.max()) + 0.5, 200)
weibull_y_line = beta_fit * log_t_line - beta_fit * np.log(eta_fit)

# Reference probability levels for y-axis labels
prob_levels = np.array([0.01, 0.05, 0.10, 0.20, 0.50, 0.632, 0.90, 0.99])
weibull_y_levels = np.log(-np.log(1 - prob_levels))

# B10 life calculation (10% failure probability)
b10_weibull_y = np.log(-np.log(1 - 0.10))
b10_life = eta_fit * (-np.log(1 - 0.10)) ** (1 / beta_fit)

# 63.2% characteristic life reference
char_life_y = np.log(-np.log(1 - 0.632))

# Censored points plotting positions (placed at approximate positions)
censored_median_rank = np.array([0.75, 0.80, 0.85, 0.88, 0.92])
censored_weibull_y = np.log(-np.log(1 - censored_median_rank))

# Data sources
failure_source = ColumnDataSource(
    data={
        "time": failure_times,
        "log_time": log_failure_times,
        "weibull_y": weibull_y,
        "prob_pct": [f"{p * 100:.1f}%" for p in median_rank],
        "time_fmt": [f"{t:.0f}" for t in failure_times],
    }
)

censored_source = ColumnDataSource(
    data={
        "time": censored_times,
        "log_time": np.log(censored_times),
        "weibull_y": censored_weibull_y,
        "time_fmt": [f"{t:.0f}" for t in censored_times],
    }
)

line_source = ColumnDataSource(data={"log_time": log_t_line, "weibull_y": weibull_y_line})

# Plot
p = figure(
    width=4800,
    height=2700,
    title="Turbine Blade Fatigue Life \u00b7 probability-weibull \u00b7 bokeh \u00b7 pyplots.ai",
    x_axis_label="Time to Failure (hours)",
    y_axis_label="Cumulative Failure Probability",
    x_range=(log_t_line.min() - 0.2, log_t_line.max() + 0.2),
    y_range=(weibull_y_levels[0] - 0.3, weibull_y_levels[-1] + 0.3),
)

# Background styling
p.background_fill_color = "#F7F9FC"
p.border_fill_color = "#FFFFFF"

# 63.2% characteristic life reference line
char_life_span = Span(
    location=char_life_y, dimension="width", line_color="#E67E22", line_width=4, line_dash="dashed", line_alpha=0.6
)
p.add_layout(char_life_span)

# Fitted line
p.line("log_time", "weibull_y", source=line_source, line_color="#1A5276", line_width=5, legend_label="Weibull Fit")

# Failure data points (filled circles)
failure_renderer = p.scatter(
    "log_time",
    "weibull_y",
    source=failure_source,
    size=30,
    color="#306998",
    alpha=0.9,
    line_color="white",
    line_width=3,
    legend_label="Failures",
)

# Censored data points (hollow circles)
censored_renderer = p.scatter(
    "log_time",
    "weibull_y",
    source=censored_source,
    size=30,
    color="white",
    alpha=0.9,
    line_color="#306998",
    line_width=4,
    legend_label="Censored",
)

# Hover tools
hover_failure = HoverTool(
    renderers=[failure_renderer],
    tooltips=[("Time", "@time_fmt hours"), ("Cum. Probability", "@prob_pct")],
    mode="mouse",
)
p.add_tools(hover_failure)

hover_censored = HoverTool(renderers=[censored_renderer], tooltips=[("Censored at", "@time_fmt hours")], mode="mouse")
p.add_tools(hover_censored)

# Parameter annotation
param_text = f"\u03b2 = {beta_fit:.2f}  (shape)\n\u03b7 = {eta_fit:.0f} h  (scale)\nR\u00b2 = {r_squared:.4f}"
param_label = Label(
    x=log_t_line.min() + 0.1,
    y=weibull_y_levels[-1] - 0.2,
    text=param_text,
    text_font_size="34pt",
    text_color="#1A5276",
    text_font_style="bold",
    background_fill_color="#F7F9FC",
    background_fill_alpha=0.9,
)
p.add_layout(param_label)

# 63.2% label
char_label = Label(
    x=log_t_line.max() - 1.0,
    y=char_life_y + 0.12,
    text="63.2% (Characteristic Life)",
    text_font_size="24pt",
    text_color="#E67E22",
    text_font_style="italic",
)
p.add_layout(char_label)

# Custom y-axis tick labels showing probability percentages
p.yaxis.ticker = list(weibull_y_levels)
prob_labels = {float(y): f"{p * 100:.1f}%" for y, p in zip(weibull_y_levels, prob_levels, strict=True)}
p.yaxis.major_label_overrides = prob_labels

# Custom x-axis: show actual hours on log scale
log_tick_values = np.log([1000, 2000, 3000, 5000, 7000, 10000])
p.xaxis.ticker = list(log_tick_values)
time_labels = {float(lt): f"{np.exp(lt):.0f}" for lt in log_tick_values}
p.xaxis.major_label_overrides = time_labels

# Style
p.title.text_font_size = "40pt"
p.title.text_color = "#2C3E50"
p.title.align = "center"

p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.axis_label_text_color = "#2C3E50"
p.yaxis.axis_label_text_color = "#2C3E50"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"
p.xaxis.major_label_text_color = "#555555"
p.yaxis.major_label_text_color = "#555555"

p.legend.label_text_font_size = "26pt"
p.legend.location = "bottom_right"
p.legend.background_fill_color = "#F7F9FC"
p.legend.background_fill_alpha = 0.92
p.legend.border_line_color = "#CCCCCC"
p.legend.border_line_alpha = 0.4
p.legend.glyph_height = 40
p.legend.glyph_width = 40
p.legend.padding = 25
p.legend.spacing = 15
p.legend.margin = 20

# Grid
p.xgrid.grid_line_color = "#CCCCCC"
p.ygrid.grid_line_color = "#CCCCCC"
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = [4, 4]
p.ygrid.grid_line_dash = [4, 4]

p.axis.axis_line_color = "#AAAAAA"
p.axis.axis_line_width = 1
p.axis.minor_tick_line_color = None
p.axis.major_tick_line_color = "#AAAAAA"

p.outline_line_color = None

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="Weibull Probability Plot")
