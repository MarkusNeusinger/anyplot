"""pyplots.ai
curve-dose-response: Pharmacological Dose-Response Curve
Library: pygal 3.1.0 | Python 3.14.3
Quality: 78/100 | Created: 2026-03-18
"""

import cairosvg
import numpy as np
import pygal
from pygal.style import Style
from scipy.optimize import curve_fit


# Data
np.random.seed(42)
concentrations = np.logspace(-9, -4, 8)
log_conc = np.log10(concentrations)


def four_pl(x, bottom, top, ec50, hill):
    return bottom + (top - bottom) / (1 + (ec50 / x) ** hill)


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

# Extract fit parameters
bottom_a, top_a, ec50_a, hill_a = popt_a
bottom_b, top_b, ec50_b, hill_b = popt_b
half_a = bottom_a + (top_a - bottom_a) / 2
half_b = bottom_b + (top_b - bottom_b) / 2
log_ec50_a = np.log10(ec50_a)
log_ec50_b = np.log10(ec50_b)

# 95% CI for Compound A via parameter covariance sampling
np.random.seed(99)
param_samples = np.random.multivariate_normal(popt_a, pcov_a, size=200)
fit_ensemble = np.array([four_pl(conc_smooth, *p) for p in param_samples])
ci_lower = np.percentile(fit_ensemble, 2.5, axis=0)
ci_upper = np.percentile(fit_ensemble, 97.5, axis=0)

# Colors — colorblind-safe blue + orange
C_A = "#306998"
C_B = "#E68A00"
C_CI = "#89ABD0"
C_REF = "#888888"

custom_style = Style(
    background="white",
    plot_background="#F8F6F0",
    foreground="#2A2A2A",
    foreground_strong="#1A1A1A",
    foreground_subtle="#E0DEDA",
    colors=(
        C_A,
        C_B,  # fitted curves
        C_A,
        C_B,  # data points
        C_CI,
        C_CI,  # CI bounds
        C_A,
        C_B,  # EC50 ref lines
        C_REF,  # asymptotes
        C_A,
        C_B,  # error bars
    ),
    title_font_size=40,
    label_font_size=26,
    major_label_font_size=24,
    legend_font_size=22,
    value_font_size=16,
    stroke_width=3,
    font_family="sans-serif",
)

chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="curve-dose-response \u00b7 pygal \u00b7 pyplots.ai",
    x_title="log\u2081\u2080 Concentration (M)",
    y_title="Response (%)",
    show_dots=False,
    dots_size=0,
    stroke=True,
    show_x_guides=False,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=20,
    x_label_rotation=0,
    truncate_legend=-1,
    range=(0, 105),
    allow_interruptions=True,
    js=[],
    print_values=False,
    value_formatter=lambda x: f"{x:.1f}%",
)

# --- Fitted curves (thick, solid) ---
chart.add(
    f"Compound A (EC\u2085\u2080={ec50_a:.1e} M)",
    list(zip(log_smooth.tolist(), fit_a.tolist(), strict=True)),
    show_dots=False,
    stroke_style={"width": 7, "linecap": "round", "linejoin": "round"},
)
chart.add(
    f"Compound B (EC\u2085\u2080={ec50_b:.1e} M)",
    list(zip(log_smooth.tolist(), fit_b.tolist(), strict=True)),
    show_dots=False,
    stroke_style={"width": 7, "linecap": "round", "linejoin": "round"},
)

# --- Data points ---
chart.add(
    "Data A \u00b1 SEM",
    list(zip(log_conc.tolist(), response_a.tolist(), strict=True)),
    stroke=False,
    show_dots=True,
    dots_size=12,
)
chart.add(
    "Data B \u00b1 SEM",
    list(zip(log_conc.tolist(), response_b.tolist(), strict=True)),
    stroke=False,
    show_dots=True,
    dots_size=12,
)

# --- 95% CI bounds for Compound A ---
chart.add(
    "95% CI (A)",
    list(zip(log_smooth.tolist(), ci_upper.tolist(), strict=True)),
    show_dots=False,
    stroke_style={"width": 2, "dasharray": "8, 6", "linecap": "round"},
)
chart.add(
    None,
    list(zip(log_smooth.tolist(), ci_lower.tolist(), strict=True)),
    show_dots=False,
    stroke_style={"width": 2, "dasharray": "8, 6", "linecap": "round"},
)

# --- EC50 reference lines (using allow_interruptions for None breaks) ---
chart.add(
    "EC\u2085\u2080 ref.",
    [(log_ec50_a, 0), (log_ec50_a, half_a), None, (log_smooth[0], half_a), (log_ec50_a, half_a)],
    show_dots=False,
    dots_size=0,
    stroke_style={"width": 3, "dasharray": "12, 8"},
)
chart.add(
    None,
    [(log_ec50_b, 0), (log_ec50_b, half_b), None, (log_smooth[0], half_b), (log_ec50_b, half_b)],
    show_dots=False,
    dots_size=0,
    stroke_style={"width": 3, "dasharray": "12, 8"},
)

# --- Asymptote lines ---
x_lo, x_hi = log_smooth[0], log_smooth[-1]
chart.add(
    "Asymptotes",
    [
        (x_lo, top_a),
        (x_hi, top_a),
        None,
        (x_lo, bottom_a),
        (x_hi, bottom_a),
        None,
        (x_lo, top_b),
        (x_hi, top_b),
        None,
        (x_lo, bottom_b),
        (x_hi, bottom_b),
    ],
    show_dots=False,
    dots_size=0,
    stroke_style={"width": 2, "dasharray": "4, 6"},
)

# --- Error bars (stems + caps) ---
cap = 0.06
for label, resp, sem in [(None, response_a, response_a_sem), (None, response_b, response_b_sem)]:
    pts = []
    for i in range(len(log_conc)):
        x = log_conc[i]
        lo, hi = resp[i] - sem[i], resp[i] + sem[i]
        pts.extend([(x, lo), (x, hi), None, (x - cap, lo), (x + cap, lo), None, (x - cap, hi), (x + cap, hi), None])
    chart.add(label, pts, stroke=True, show_dots=False, dots_size=0, stroke_style={"width": 2})

# Render and save
svg = chart.render(is_unicode=True)
with open("plot.html", "w") as f:
    f.write(svg)
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to="plot.png", dpi=96)
