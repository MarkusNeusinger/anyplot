"""pyplots.ai
probability-weibull: Weibull Probability Plot for Reliability Analysis
Library: pygal 3.1.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-11
"""

import numpy as np
import pygal
from pygal.style import Style
from scipy import stats


# Data — turbine blade fatigue-life (hours) with failures and suspensions
np.random.seed(42)
n_failures = 18
n_censored = 5
beta_true = 2.5
eta_true = 8000

failure_times = np.sort(stats.weibull_min.rvs(beta_true, scale=eta_true, size=n_failures))
censored_times = np.sort(np.random.uniform(2000, 9000, n_censored))

all_times = np.concatenate([failure_times, censored_times])
is_failure = np.concatenate([np.ones(n_failures), np.zeros(n_censored)])

sort_idx = np.argsort(all_times)
all_times = all_times[sort_idx]
is_failure = is_failure[sort_idx]

# Median rank plotting positions (i-0.3)/(n+0.4) for failures only
failure_ranks = np.cumsum(is_failure)
total_failures = failure_ranks[-1]
median_ranks = (failure_ranks - 0.3) / (total_failures + 0.4)

failure_mask = is_failure.astype(bool)
failure_x = all_times[failure_mask]
failure_prob = median_ranks[failure_mask]

# Weibull linearization: ln(-ln(1-F)) for y-axis, ln(time) for x-axis
weibull_y_failures = np.log(-np.log(1.0 - failure_prob))
ln_x_failures = np.log(failure_x)

# Fit line using least squares on linearized data
slope, intercept, r_value, _, _ = stats.linregress(ln_x_failures, weibull_y_failures)
beta_est = slope
eta_est = np.exp(-intercept / beta_est)

# Fitted line spanning full data range
x_fit_range = np.linspace(np.log(min(all_times) * 0.7), np.log(max(all_times) * 1.3), 100)
y_fit_line = slope * x_fit_range + intercept

# Censored points — place on the fitted line at their log-time
censored_x = all_times[~failure_mask]
ln_censored_x = np.log(censored_x)
censored_y_on_line = slope * ln_censored_x + intercept

# 63.2% reference line (characteristic life): F = 0.632 → ln(-ln(1-0.632)) ≈ 0.0
ref_y = np.log(-np.log(1 - 0.632))

# B10 life: F = 0.10 → time where 10% of units have failed
b10_y = np.log(-np.log(1 - 0.10))
b10_ln_x = (b10_y - intercept) / slope
b10_hours = np.exp(b10_ln_x)

# Characteristic life intersection: where fitted line crosses 63.2%
eta_ln_x = (ref_y - intercept) / slope

# Axis labels — convert back from log/Weibull scale for readability
x_tick_values = [1000, 2000, 3000, 5000, 7000, 10000, 15000]
x_tick_ln = [np.log(v) for v in x_tick_values]

prob_levels = [0.01, 0.05, 0.10, 0.20, 0.50, 0.632, 0.80, 0.90, 0.95, 0.99]
y_tick_weibull = [np.log(-np.log(1.0 - p)) for p in prob_levels]
y_tick_labels = [f"{p * 100:.1f}%" if p == 0.632 else f"{p * 100:.0f}%" for p in prob_levels]

# Style — cohesive blue-tonal palette with warm accent for annotations
font = "DejaVu Sans, Helvetica, Arial, sans-serif"
custom_style = Style(
    background="white",
    plot_background="#fafbfc",
    foreground="#2c3e50",
    foreground_strong="#1a252f",
    foreground_subtle="#e0e4e8",
    guide_stroke_color="#e0e4e8",
    guide_stroke_dasharray="4, 8",
    colors=(
        "#4a7fb5",  # fit line — medium blue
        "#1b3a5c",  # failures — dark navy
        "#7cadd4",  # censored — light steel blue
        "#95a5a6",  # 63.2% reference — cool gray
        "#d35400",  # η marker — warm burnt orange (accent)
        "#27ae60",  # B10 marker — muted green (distinct from blue)
    ),
    font_family=font,
    title_font_family=font,
    title_font_size=56,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=38,
    legend_font_family=font,
    value_font_size=32,
    tooltip_font_size=28,
    tooltip_font_family=font,
    opacity=0.92,
    opacity_hover=1.0,
    stroke_opacity=1,
    stroke_opacity_hover=1,
)

# Axis bounds — tighter y-range to reduce wasted space at extremes
x_min_ln = np.log(800)
x_max_ln = np.log(18000)
y_min_w = np.log(-np.log(1 - 0.008))
y_max_w = np.log(-np.log(1 - 0.993))

# Chart configuration
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="Turbine Blade Fatigue Life · probability-weibull · pygal · pyplots.ai",
    x_title="Time to Failure (hours, log scale)",
    y_title="Cumulative Failure Probability",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=30,
    stroke=False,
    dots_size=10,
    show_x_guides=True,
    show_y_guides=True,
    margin_bottom=100,
    margin_left=90,
    margin_right=60,
    margin_top=60,
    truncate_legend=-1,
    range=(y_min_w, y_max_w),
    xrange=(x_min_ln, x_max_ln),
    print_values=False,
    print_zeroes=False,
    js=[],
    x_labels=[float(v) for v in x_tick_ln],
    y_labels=[float(v) for v in y_tick_weibull],
    x_value_formatter=lambda x: f"{np.exp(x):,.0f}h",
    value_formatter=lambda y: f"{(1 - np.exp(-np.exp(y))) * 100:.1f}%",
    tooltip_border_radius=10,
    tooltip_fancy_mode=True,
    dynamic_print_values=True,
)

# Override label display for axes
chart.y_labels = [{"value": float(v), "label": lbl} for v, lbl in zip(y_tick_weibull, y_tick_labels, strict=True)]
chart.x_labels = [{"value": float(v), "label": f"{int(t):,}"} for v, t in zip(x_tick_ln, x_tick_values, strict=True)]

# Fitted line — medium blue, prominent stroke
fit_points = [(float(x), float(y)) for x, y in zip(x_fit_range, y_fit_line, strict=True)]
chart.add(
    f"Weibull Fit (β={beta_est:.2f}, η={eta_est:,.0f}h, R²={r_value**2:.3f})",
    fit_points,
    stroke=True,
    show_dots=False,
    stroke_style={"width": 8, "linecap": "round", "linejoin": "round"},
)

# Failure data points — dark navy with per-point tooltip labels
failure_points = [
    {
        "value": (float(x), float(y)),
        "label": f"Failure at {np.exp(x):,.0f}h — F={((1 - np.exp(-np.exp(y))) * 100):.1f}%",
    }
    for x, y in zip(ln_x_failures, weibull_y_failures, strict=True)
]
chart.add(f"Failures (n={n_failures})", failure_points, stroke=False, dots_size=12)

# Censored data points — light steel blue, visually lighter than failures
censored_points = [
    {"value": (float(x), float(y)), "label": f"Censored at {np.exp(x):,.0f}h (suspended test)"}
    for x, y in zip(ln_censored_x, censored_y_on_line, strict=True)
]
chart.add(f"Censored (n={n_censored})", censored_points, stroke=False, dots_size=9)

# 63.2% reference line — cool gray dashed
ref_line = [(float(x_min_ln), float(ref_y)), (float(x_max_ln), float(ref_y))]
chart.add(
    "63.2% Characteristic Life",
    ref_line,
    stroke=True,
    show_dots=False,
    stroke_style={"width": 4, "dasharray": "16, 10", "linecap": "round"},
)

# η marker — warm burnt orange accent, on-chart printed value
eta_marker = [
    {"value": (float(eta_ln_x), float(ref_y)), "label": f"η = {eta_est:,.0f}h (Characteristic Life at 63.2%)"}
]
chart.add(
    f"η = {eta_est:,.0f}h",
    eta_marker,
    stroke=False,
    dots_size=22,
    print_values=True,
    formatter=lambda x: f"η = {eta_est:,.0f}h",
)

# B10 marker — muted green, distinct from blues, on-chart printed value
b10_marker = [{"value": (float(b10_ln_x), float(b10_y)), "label": f"B10 = {b10_hours:,.0f}h (10% Failure Life)"}]
chart.add(
    f"B10 = {b10_hours:,.0f}h",
    b10_marker,
    stroke=False,
    dots_size=22,
    print_values=True,
    formatter=lambda x: f"B10 = {b10_hours:,.0f}h",
)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
