""" pyplots.ai
curve-dose-response: Pharmacological Dose-Response Curve
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-18
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from scipy.optimize import curve_fit
from scipy.stats import t as t_dist


# Data
np.random.seed(42)

concentrations = np.logspace(-9, -4, 8)

bottom_a, top_a, ec50_a, hill_a = 5.0, 95.0, 3e-7, 1.2
bottom_b, top_b, ec50_b, hill_b = 10.0, 80.0, 5e-6, 0.9


def logistic4pl(conc, bottom, top, ec50, hill):
    with np.errstate(invalid="ignore", divide="ignore"):
        ratio = np.where(conc > 0, (ec50 / conc) ** hill, np.inf)
    return bottom + (top - bottom) / (1 + ratio)


response_a_true = logistic4pl(concentrations, bottom_a, top_a, ec50_a, hill_a)
response_b_true = logistic4pl(concentrations, bottom_b, top_b, ec50_b, hill_b)

sem_a = np.random.uniform(2, 5, len(concentrations))
sem_b = np.random.uniform(2, 5, len(concentrations))

response_a = response_a_true + np.random.normal(0, 2, len(concentrations))
response_b = response_b_true + np.random.normal(0, 2, len(concentrations))

# Build DataFrames for seaborn
records = []
for i in range(len(concentrations)):
    records.append(
        {"concentration": concentrations[i], "response": response_a[i], "sem": sem_a[i], "compound": "Imatinib"}
    )
    records.append(
        {"concentration": concentrations[i], "response": response_b[i], "sem": sem_b[i], "compound": "Erlotinib"}
    )
df = pd.DataFrame(records)

# Fit 4PL models
palette = {"Imatinib": "#306998", "Erlotinib": "#D4763A"}
fit_params = {}
fit_cov = {}

for compound in ["Imatinib", "Erlotinib"]:
    mask = df["compound"] == compound
    x_data = df.loc[mask, "concentration"].values
    y_data = df.loc[mask, "response"].values
    p0 = [5, 90, 1e-6, 1.0]
    popt, pcov = curve_fit(logistic4pl, x_data, y_data, p0=p0, maxfev=10000)
    fit_params[compound] = popt
    fit_cov[compound] = pcov

x_fit = np.logspace(-9.5, -3.5, 300)

# Build fitted curve DataFrame for seaborn lineplot
fit_records = []
for compound in ["Imatinib", "Erlotinib"]:
    popt = fit_params[compound]
    y_fit = logistic4pl(x_fit, *popt)
    for xi, yi in zip(x_fit, y_fit, strict=False):
        fit_records.append({"concentration": xi, "response": yi, "compound": compound})
df_fit = pd.DataFrame(fit_records)

# Plot
sns.set_style("ticks")
sns.set_context("talk", font_scale=1.1)
fig, ax = plt.subplots(figsize=(16, 9))

# Fitted curves via seaborn lineplot
sns.lineplot(
    data=df_fit,
    x="concentration",
    y="response",
    hue="compound",
    palette=palette,
    linewidth=3,
    legend=False,
    ax=ax,
    zorder=4,
)

# Data points via seaborn scatterplot
sns.scatterplot(
    data=df,
    x="concentration",
    y="response",
    hue="compound",
    palette=palette,
    s=120,
    edgecolor="white",
    linewidth=1.5,
    zorder=5,
    ax=ax,
    legend=True,
)

# Error bars (matplotlib needed for yerr support)
for compound in ["Imatinib", "Erlotinib"]:
    sub = df[df["compound"] == compound]
    ax.errorbar(
        sub["concentration"],
        sub["response"],
        yerr=sub["sem"],
        fmt="none",
        ecolor=palette[compound],
        capsize=5,
        capthick=2,
        elinewidth=2,
        alpha=0.7,
        zorder=4,
    )

# EC50 reference lines
for compound in ["Imatinib", "Erlotinib"]:
    popt = fit_params[compound]
    ec50_val = popt[2]
    half_response = popt[0] + (popt[1] - popt[0]) / 2
    ax.hlines(
        half_response,
        x_fit[0],
        ec50_val,
        colors=palette[compound],
        linestyles="dashed",
        linewidth=1.5,
        alpha=0.6,
        zorder=3,
    )
    ax.vlines(
        ec50_val, -5, half_response, colors=palette[compound], linestyles="dashed", linewidth=1.5, alpha=0.6, zorder=3
    )

# 95% Confidence band for Imatinib
popt_a = fit_params["Imatinib"]
pcov_a = fit_cov["Imatinib"]
n_data = len(concentrations)
n_params = len(popt_a)
dof = max(n_data - n_params, 1)
t_val = t_dist.ppf(0.975, dof)

jacobian = np.zeros((len(x_fit), n_params))
delta = 1e-8
for j in range(n_params):
    params_up = popt_a.copy()
    params_up[j] += delta
    params_down = popt_a.copy()
    params_down[j] -= delta
    jacobian[:, j] = (logistic4pl(x_fit, *params_up) - logistic4pl(x_fit, *params_down)) / (2 * delta)

pred_var = np.array([jacobian[i] @ pcov_a @ jacobian[i] for i in range(len(x_fit))])
pred_se = np.sqrt(np.maximum(pred_var, 0))
y_fit_a = logistic4pl(x_fit, *popt_a)

ax.fill_between(
    x_fit,
    y_fit_a - t_val * pred_se,
    y_fit_a + t_val * pred_se,
    color=palette["Imatinib"],
    alpha=0.15,
    zorder=2,
    label="95% CI (Imatinib)",
)

# Asymptote lines
for compound, style in [("Imatinib", (5, 5)), ("Erlotinib", (2, 4))]:
    popt = fit_params[compound]
    ax.axhline(popt[0], color=palette[compound], linestyle=(0, style), linewidth=1, alpha=0.35, zorder=1)
    ax.axhline(popt[1], color=palette[compound], linestyle=(0, style), linewidth=1, alpha=0.35, zorder=1)

# Style
ax.set_xscale("log")
ax.set_xlabel("Concentration (M)", fontsize=20)
ax.set_ylabel("Response (%)", fontsize=20)
ax.set_title("curve-dose-response · seaborn · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
sns.despine(ax=ax)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
ax.set_ylim(-5, 110)

# Update legend with fit lines and CI
handles, labels = ax.get_legend_handles_labels()
custom_handles = [
    Line2D([0], [0], color=palette["Imatinib"], linewidth=3, label="Imatinib (fit)"),
    Line2D([0], [0], color=palette["Erlotinib"], linewidth=3, label="Erlotinib (fit)"),
    Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor=palette["Imatinib"],
        markersize=10,
        markeredgecolor="white",
        label="Imatinib (data)",
    ),
    Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor=palette["Erlotinib"],
        markersize=10,
        markeredgecolor="white",
        label="Erlotinib (data)",
    ),
    Patch(facecolor=palette["Imatinib"], alpha=0.15, label="95% CI (Imatinib)"),
]
ax.legend(handles=custom_handles, fontsize=14, frameon=False, loc="upper left")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
