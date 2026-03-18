""" pyplots.ai
curve-dose-response: Pharmacological Dose-Response Curve
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-18
"""

import numpy as np
import pandas as pd
from lets_plot import *
from scipy.optimize import curve_fit


LetsPlot.setup_html()

# Data - synthetic dose-response for two compounds
np.random.seed(42)
concentrations = np.logspace(-9, -4, 8)

# 4PL model: response = Bottom + (Top - Bottom) / (1 + (EC50/conc)^Hill)
four_pl = lambda conc, bottom, top, ec50, hill: bottom + (top - bottom) / (1 + (ec50 / conc) ** hill)

# Compound A parameters: EC50 = 1e-7 M, Hill = 1.2
bottom_a, top_a, ec50_a, hill_a = 5.0, 95.0, 1e-7, 1.2
response_a = four_pl(concentrations, bottom_a, top_a, ec50_a, hill_a)
response_a_noisy = response_a + np.random.normal(0, 3, len(concentrations))
sem_a = np.random.uniform(2, 5, len(concentrations))

# Compound B parameters: EC50 = 5e-6 M, Hill = 0.9
bottom_b, top_b, ec50_b, hill_b = 8.0, 85.0, 5e-6, 0.9
response_b = four_pl(concentrations, bottom_b, top_b, ec50_b, hill_b)
response_b_noisy = response_b + np.random.normal(0, 3.5, len(concentrations))
sem_b = np.random.uniform(2.5, 5.5, len(concentrations))

# Fit 4PL model to noisy data
popt_a, pcov_a = curve_fit(four_pl, concentrations, response_a_noisy, p0=[5, 95, 1e-7, 1], maxfev=10000)
popt_b, pcov_b = curve_fit(four_pl, concentrations, response_b_noisy, p0=[8, 85, 5e-6, 1], maxfev=10000)

# Generate smooth fitted curves
conc_smooth = np.logspace(-9.5, -3.5, 200)
fit_a = four_pl(conc_smooth, *popt_a)
fit_b = four_pl(conc_smooth, *popt_b)

# 95% CI for Compound A via parameter covariance
perr_a = np.sqrt(np.diag(pcov_a))
ci_a_upper = four_pl(conc_smooth, popt_a[0] - perr_a[0], popt_a[1] + perr_a[1], popt_a[2], popt_a[3])
ci_a_lower = four_pl(conc_smooth, popt_a[0] + perr_a[0], popt_a[1] - perr_a[1], popt_a[2], popt_a[3])

# EC50 values from fits
ec50_fit_a = popt_a[2]
ec50_fit_b = popt_b[2]
half_response_a = popt_a[0] + (popt_a[1] - popt_a[0]) / 2
half_response_b = popt_b[0] + (popt_b[1] - popt_b[0]) / 2

# Data points DataFrame
df_points = pd.DataFrame(
    {
        "concentration": np.concatenate([concentrations, concentrations]),
        "log_conc": np.concatenate([np.log10(concentrations), np.log10(concentrations)]),
        "response": np.concatenate([response_a_noisy, response_b_noisy]),
        "sem": np.concatenate([sem_a, sem_b]),
        "ymin": np.concatenate([response_a_noisy - sem_a, response_b_noisy - sem_b]),
        "ymax": np.concatenate([response_a_noisy + sem_a, response_b_noisy + sem_b]),
        "compound": ["Compound A"] * len(concentrations) + ["Compound B"] * len(concentrations),
    }
)

# Fitted curves DataFrame
df_fit = pd.DataFrame(
    {
        "log_conc": np.concatenate([np.log10(conc_smooth), np.log10(conc_smooth)]),
        "response": np.concatenate([fit_a, fit_b]),
        "compound": ["Compound A"] * len(conc_smooth) + ["Compound B"] * len(conc_smooth),
    }
)

# Confidence band for Compound A
df_ci = pd.DataFrame({"log_conc": np.log10(conc_smooth), "ymin": ci_a_lower, "ymax": ci_a_upper})

# EC50 reference lines
df_ec50_h = pd.DataFrame(
    {
        "log_conc": [np.log10(conc_smooth[0]), np.log10(ec50_fit_a), np.log10(conc_smooth[0]), np.log10(ec50_fit_b)],
        "response": [half_response_a, half_response_a, half_response_b, half_response_b],
        "compound": ["Compound A", "Compound A", "Compound B", "Compound B"],
    }
)

df_ec50_v = pd.DataFrame(
    {
        "log_conc": [np.log10(ec50_fit_a), np.log10(ec50_fit_a), np.log10(ec50_fit_b), np.log10(ec50_fit_b)],
        "response": [0, half_response_a, 0, half_response_b],
        "compound": ["Compound A", "Compound A", "Compound B", "Compound B"],
    }
)

# Asymptote lines
top_asym_a = popt_a[1]
bottom_asym_a = popt_a[0]

# Plot
colors = ["#306998", "#E07A3A"]

plot = (
    ggplot()
    # Confidence band for Compound A
    + geom_ribbon(data=df_ci, mapping=aes(x="log_conc", ymin="ymin", ymax="ymax"), fill="#306998", alpha=0.15)
    # Top and bottom asymptote lines
    + geom_hline(yintercept=top_asym_a, linetype="dotted", color="#999999", size=0.8)
    + geom_hline(yintercept=bottom_asym_a, linetype="dotted", color="#999999", size=0.8)
    # EC50 reference lines
    + geom_line(data=df_ec50_h, mapping=aes(x="log_conc", y="response", color="compound"), linetype="dashed", size=0.8)
    + geom_line(data=df_ec50_v, mapping=aes(x="log_conc", y="response", color="compound"), linetype="dashed", size=0.8)
    # Fitted curves
    + geom_line(data=df_fit, mapping=aes(x="log_conc", y="response", color="compound"), size=2)
    # Error bars
    + geom_errorbar(
        data=df_points, mapping=aes(x="log_conc", ymin="ymin", ymax="ymax", color="compound"), width=0.08, size=0.8
    )
    # Data points
    + geom_point(
        data=df_points,
        mapping=aes(x="log_conc", y="response", color="compound"),
        size=4,
        shape=21,
        fill="white",
        stroke=2,
    )
    + scale_color_manual(values=colors)
    + scale_x_continuous(breaks=list(range(-9, -3)), labels=["1e-9", "1e-8", "1e-7", "1e-6", "1e-5", "1e-4"])
    + labs(x="Concentration (M)", y="Response (%)", title="curve-dose-response · letsplot · pyplots.ai", color="")
    + theme_minimal()
    + theme(
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_position=[0.85, 0.15],
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
