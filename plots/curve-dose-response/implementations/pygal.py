""" pyplots.ai
curve-dose-response: Pharmacological Dose-Response Curve
Library: pygal 3.1.0 | Python 3.14.3
Quality: 75/100 | Created: 2026-03-18
"""

import numpy as np
import pygal
from pygal.style import Style
from scipy.optimize import curve_fit


# Data
np.random.seed(42)
concentrations = np.logspace(-9, -4, 8)
log_conc = np.log10(concentrations)

four_pl = lambda x, bottom, top, ec50, hill: bottom + (top - bottom) / (1 + (ec50 / x) ** hill)

# Compound A — potent agonist
response_a_true = four_pl(concentrations, 5, 95, 1e-7, 1.2)
response_a_sem = np.random.uniform(2, 5, len(concentrations))
response_a = response_a_true + np.random.normal(0, response_a_sem)

# Compound B — moderate agonist
response_b_true = four_pl(concentrations, 10, 85, 1e-6, 0.9)
response_b_sem = np.random.uniform(2, 6, len(concentrations))
response_b = response_b_true + np.random.normal(0, response_b_sem)

# Fit 4PL curves
popt_a, pcov_a = curve_fit(four_pl, concentrations, response_a, p0=[0, 100, 1e-7, 1], maxfev=10000)
popt_b, pcov_b = curve_fit(four_pl, concentrations, response_b, p0=[0, 100, 1e-6, 1], maxfev=10000)

# Smooth fitted curves
conc_smooth = np.logspace(-9.5, -3.5, 200)
log_smooth = np.log10(conc_smooth)
fit_a = four_pl(conc_smooth, *popt_a)
fit_b = four_pl(conc_smooth, *popt_b)

# EC50 values from fit
ec50_a = popt_a[2]
ec50_b = popt_b[2]
half_a = popt_a[0] + (popt_a[1] - popt_a[0]) / 2
half_b = popt_b[0] + (popt_b[1] - popt_b[0]) / 2

# 95% CI for Compound A via parameter covariance sampling
np.random.seed(99)
param_samples = np.random.multivariate_normal(popt_a, pcov_a, size=200)
fit_ensemble = np.array([four_pl(conc_smooth, *p) for p in param_samples])
ci_lower = np.percentile(fit_ensemble, 2.5, axis=0)
ci_upper = np.percentile(fit_ensemble, 97.5, axis=0)

# Plot
palette_a = "#306998"
palette_b = "#E74C3C"
palette_ci = "#89ABD0"

color_sequence = (
    (
        palette_a,
        palette_b,  # fitted curves
        palette_a,
        palette_b,  # data points
        palette_ci,
        palette_ci,  # CI bounds
        palette_a,
        palette_a,  # EC50 A (vert + horiz)
        palette_b,
        palette_b,  # EC50 B (vert + horiz)
    )
    + (palette_a,) * 24
    + (palette_b,) * 24
)

custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333",
    foreground_strong="#333",
    foreground_subtle="#cccccc",
    colors=color_sequence,
    title_font_size=28,
    label_font_size=18,
    major_label_font_size=16,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
)

chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="curve-dose-response \u00b7 pygal \u00b7 pyplots.ai",
    x_title="log\u2081\u2080 Concentration (M)",
    y_title="Response (%)",
    show_dots=True,
    dots_size=4,
    stroke=True,
    show_x_guides=False,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    x_label_rotation=0,
    truncate_legend=-1,
)

# Fitted curves
chart.add(
    "Compound A (fit)",
    list(zip(log_smooth.tolist(), fit_a.tolist())),
    show_dots=False,
    stroke_style={"width": 6, "linecap": "round", "linejoin": "round"},
)
chart.add(
    "Compound B (fit)",
    list(zip(log_smooth.tolist(), fit_b.tolist())),
    show_dots=False,
    stroke_style={"width": 6, "linecap": "round", "linejoin": "round"},
)

# Data points
chart.add("Compound A", list(zip(log_conc.tolist(), response_a.tolist())), stroke=False, dots_size=14)
chart.add("Compound B", list(zip(log_conc.tolist(), response_b.tolist())), stroke=False, dots_size=14)

# 95% CI bounds for Compound A
chart.add(
    "95% CI (A)",
    list(zip(log_smooth.tolist(), ci_upper.tolist())),
    show_dots=False,
    stroke_style={"width": 2, "dasharray": "8, 6", "linecap": "round"},
)
chart.add(
    None,
    list(zip(log_smooth.tolist(), ci_lower.tolist())),
    show_dots=False,
    stroke_style={"width": 2, "dasharray": "8, 6", "linecap": "round"},
)

# EC50 reference lines — Compound A
log_ec50_a = np.log10(ec50_a)
chart.add(
    f"EC50 A = {ec50_a:.1e} M",
    [(log_ec50_a, 0), (log_ec50_a, half_a)],
    show_dots=False,
    stroke_style={"width": 3, "dasharray": "12, 8"},
)
chart.add(
    None,
    [(log_smooth[0], half_a), (log_ec50_a, half_a)],
    show_dots=False,
    stroke_style={"width": 3, "dasharray": "12, 8"},
)

# EC50 reference lines — Compound B
log_ec50_b = np.log10(ec50_b)
chart.add(
    f"EC50 B = {ec50_b:.1e} M",
    [(log_ec50_b, 0), (log_ec50_b, half_b)],
    show_dots=False,
    stroke_style={"width": 3, "dasharray": "12, 8"},
)
chart.add(
    None,
    [(log_smooth[0], half_b), (log_ec50_b, half_b)],
    show_dots=False,
    stroke_style={"width": 3, "dasharray": "12, 8"},
)

# Error bars for Compound A
for i in range(len(log_conc)):
    x = log_conc[i]
    y = response_a[i]
    sem = response_a_sem[i]
    cap = 0.06
    chart.add(None, [(x, y - sem), (x, y + sem)], stroke=True, show_dots=False, stroke_style={"width": 3})
    chart.add(None, [(x - cap, y - sem), (x + cap, y - sem)], stroke=True, show_dots=False, stroke_style={"width": 3})
    chart.add(None, [(x - cap, y + sem), (x + cap, y + sem)], stroke=True, show_dots=False, stroke_style={"width": 3})

# Error bars for Compound B
for i in range(len(log_conc)):
    x = log_conc[i]
    y = response_b[i]
    sem = response_b_sem[i]
    cap = 0.06
    chart.add(None, [(x, y - sem), (x, y + sem)], stroke=True, show_dots=False, stroke_style={"width": 3})
    chart.add(None, [(x - cap, y - sem), (x + cap, y - sem)], stroke=True, show_dots=False, stroke_style={"width": 3})
    chart.add(None, [(x - cap, y + sem), (x + cap, y + sem)], stroke=True, show_dots=False, stroke_style={"width": 3})

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
