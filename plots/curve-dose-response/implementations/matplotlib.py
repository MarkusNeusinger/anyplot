""" pyplots.ai
curve-dose-response: Pharmacological Dose-Response Curve
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 86/100 | Updated: 2026-03-23
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import t as t_dist


# Data
np.random.seed(42)

concentrations = np.logspace(-9, -4, 8)

bottom_a, top_a, ec50_a, hill_a = 5.0, 95.0, 3e-7, 1.2
bottom_b, top_b, ec50_b, hill_b = 8.0, 80.0, 5e-6, 0.9


def logistic4pl(conc, bottom, top, ec50, hill):
    return bottom + (top - bottom) / (1 + (ec50 / conc) ** hill)


response_a_true = logistic4pl(concentrations, bottom_a, top_a, ec50_a, hill_a)
response_b_true = logistic4pl(concentrations, bottom_b, top_b, ec50_b, hill_b)

sem_a = np.array([2.5, 3.0, 4.5, 5.0, 4.0, 3.5, 2.8, 2.0])
sem_b = np.array([3.0, 3.5, 5.0, 4.5, 5.5, 4.0, 3.0, 2.5])

response_a = response_a_true + np.random.normal(0, 2, len(concentrations))
response_b = response_b_true + np.random.normal(0, 2, len(concentrations))

# Fit 4PL curves
popt_a, pcov_a = curve_fit(logistic4pl, concentrations, response_a, p0=[5, 95, 1e-7, 1.0], maxfev=10000)
popt_b, pcov_b = curve_fit(logistic4pl, concentrations, response_b, p0=[8, 80, 1e-6, 1.0], maxfev=10000)

conc_smooth = np.logspace(-9.5, -3.5, 300)
fit_a = logistic4pl(conc_smooth, *popt_a)
fit_b = logistic4pl(conc_smooth, *popt_b)

# 95% CI for Compound A via delta method
n_params = len(popt_a)
n_data = len(concentrations)
dof = max(n_data - n_params, 1)
t_val = t_dist.ppf(0.975, dof)

delta = 1e-8 * np.abs(popt_a) + 1e-15
jacobian_a = np.zeros((len(conc_smooth), n_params))
for i in range(n_params):
    params_up = popt_a.copy()
    params_up[i] += delta[i]
    params_dn = popt_a.copy()
    params_dn[i] -= delta[i]
    jacobian_a[:, i] = (logistic4pl(conc_smooth, *params_up) - logistic4pl(conc_smooth, *params_dn)) / (2 * delta[i])

pred_var_a = np.sum(jacobian_a @ pcov_a * jacobian_a, axis=1)
pred_se_a = np.sqrt(np.maximum(pred_var_a, 0))
ci_lower_a = fit_a - t_val * pred_se_a
ci_upper_a = fit_a + t_val * pred_se_a

# Extract fitted parameters
ec50_fit_a = popt_a[2]
ec50_fit_b = popt_b[2]
half_response_a = popt_a[0] + (popt_a[1] - popt_a[0]) / 2
half_response_b = popt_b[0] + (popt_b[1] - popt_b[0]) / 2

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

colors = ["#306998", "#C75233"]

ax.fill_between(conc_smooth, ci_lower_a, ci_upper_a, alpha=0.15, color=colors[0], label="95% CI (Compound A)")

ax.plot(conc_smooth, fit_a, linewidth=3, color=colors[0], label="Compound A (fit)")
ax.plot(conc_smooth, fit_b, linewidth=3, color=colors[1], label="Compound B (fit)")

ax.errorbar(
    concentrations,
    response_a,
    yerr=sem_a,
    fmt="o",
    markersize=10,
    color=colors[0],
    markeredgecolor="white",
    markeredgewidth=1.2,
    elinewidth=2,
    capsize=5,
    capthick=2,
    zorder=5,
    label="Compound A (data)",
)
ax.errorbar(
    concentrations,
    response_b,
    yerr=sem_b,
    fmt="s",
    markersize=10,
    color=colors[1],
    markeredgecolor="white",
    markeredgewidth=1.2,
    elinewidth=2,
    capsize=5,
    capthick=2,
    zorder=5,
    label="Compound B (data)",
)

# EC50 reference lines
ax.hlines(half_response_a, conc_smooth[0], ec50_fit_a, linestyles="dashed", colors=colors[0], linewidth=1.5, alpha=0.6)
ax.vlines(
    ec50_fit_a,
    ax.get_ylim()[0] if ax.get_ylim()[0] < 0 else 0,
    half_response_a,
    linestyles="dashed",
    colors=colors[0],
    linewidth=1.5,
    alpha=0.6,
)

ax.hlines(half_response_b, conc_smooth[0], ec50_fit_b, linestyles="dashed", colors=colors[1], linewidth=1.5, alpha=0.6)
ax.vlines(
    ec50_fit_b,
    ax.get_ylim()[0] if ax.get_ylim()[0] < 0 else 0,
    half_response_b,
    linestyles="dashed",
    colors=colors[1],
    linewidth=1.5,
    alpha=0.6,
)

# Asymptote lines — show only top asymptotes to reduce clutter
ax.axhline(y=popt_a[1], linestyle=":", color=colors[0], alpha=0.25, linewidth=1.0)
ax.axhline(y=popt_b[1], linestyle=":", color=colors[1], alpha=0.25, linewidth=1.0)
# Subtle bottom asymptotes with very low alpha
ax.axhline(y=popt_a[0], linestyle=":", color=colors[0], alpha=0.15, linewidth=0.8)
ax.axhline(y=popt_b[0], linestyle=":", color=colors[1], alpha=0.15, linewidth=0.8)


# EC50 annotations using annotate with arrow props
def format_ec50(val):
    if val >= 1e-6:
        return f"EC\u2085\u2080 = {val * 1e6:.1f} \u00b5M"
    return f"EC\u2085\u2080 = {val * 1e9:.0f} nM"


ax.annotate(
    format_ec50(ec50_fit_a),
    xy=(ec50_fit_a, half_response_a),
    xytext=(ec50_fit_a * 30, half_response_a + 12),
    fontsize=14,
    fontweight="bold",
    color=colors[0],
    arrowprops={"arrowstyle": "->", "color": colors[0], "lw": 1.5, "connectionstyle": "arc3,rad=-0.2"},
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": colors[0], "alpha": 0.85},
    zorder=10,
)

ax.annotate(
    format_ec50(ec50_fit_b),
    xy=(ec50_fit_b, half_response_b),
    xytext=(ec50_fit_b * 30, half_response_b - 14),
    fontsize=14,
    fontweight="bold",
    color=colors[1],
    arrowprops={"arrowstyle": "->", "color": colors[1], "lw": 1.5, "connectionstyle": "arc3,rad=0.2"},
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": colors[1], "alpha": 0.85},
    zorder=10,
)

# Hill slope annotations
ax.text(
    0.98,
    0.02,
    f"Hill slopes:  A = {popt_a[3]:.2f}  |  B = {popt_b[3]:.2f}",
    transform=ax.transAxes,
    fontsize=13,
    color="#555555",
    ha="right",
    va="bottom",
    style="italic",
)

# Style
ax.set_xscale("log")
ax.set_xlabel("Concentration (M)", fontsize=20)
ax.set_ylabel("Response (%)", fontsize=20)
ax.set_title("curve-dose-response · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)

# Legend with reordered handles — data points and fits grouped logically
handles, labels = ax.get_legend_handles_labels()
order = [3, 1, 4, 2, 0]  # A data, A fit, B data, B fit, CI
ax.legend(
    [handles[i] for i in order],
    [labels[i] for i in order],
    fontsize=14,
    loc="upper left",
    framealpha=0.9,
    edgecolor="#cccccc",
    ncol=1,
)
ax.set_ylim(-5, 110)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
