"""pyplots.ai
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

# Build DataFrame using vectorized concat
df = pd.concat(
    [
        pd.DataFrame({"concentration": concentrations, "response": response_a, "sem": sem_a, "compound": "Imatinib"}),
        pd.DataFrame({"concentration": concentrations, "response": response_b, "sem": sem_b, "compound": "Erlotinib"}),
    ],
    ignore_index=True,
)

# Fit 4PL models
palette = sns.color_palette(["#306998", "#D4763A"])
palette_dict = {"Imatinib": "#306998", "Erlotinib": "#D4763A"}
fit_params = {}
fit_cov = {}

for compound in ["Imatinib", "Erlotinib"]:
    mask = df["compound"] == compound
    x_data = df.loc[mask, "concentration"].values
    y_data = df.loc[mask, "response"].values
    popt, pcov = curve_fit(logistic4pl, x_data, y_data, p0=[5, 90, 1e-6, 1.0], maxfev=10000)
    fit_params[compound] = popt
    fit_cov[compound] = pcov

x_fit = np.logspace(-9.5, -3.5, 200)

# Generate bootstrap samples for seaborn's native CI band
n_boot = 100
boot_frames = []
for compound in ["Imatinib", "Erlotinib"]:
    popt = fit_params[compound]
    pcov = fit_cov[compound]
    param_samples = np.random.multivariate_normal(popt, pcov, size=n_boot)
    for k in range(n_boot):
        y_boot = logistic4pl(x_fit, *param_samples[k])
        boot_frames.append(
            pd.DataFrame({"concentration": x_fit, "response": y_boot, "compound": compound, "boot_id": k})
        )
df_boot = pd.concat(boot_frames, ignore_index=True)

# Plot
sns.set_theme(style="ticks", context="talk", font_scale=1.1, palette=palette)
fig, ax = plt.subplots(figsize=(16, 9))

# Fitted curves with native seaborn CI bands via bootstrap samples
sns.lineplot(
    data=df_boot[df_boot["compound"] == "Imatinib"],
    x="concentration",
    y="response",
    color=palette_dict["Imatinib"],
    linewidth=3,
    errorbar=("pi", 95),
    n_boot=0,
    estimator="mean",
    ax=ax,
    zorder=4,
    label="_nolegend_",
)
sns.lineplot(
    data=df_boot[df_boot["compound"] == "Erlotinib"],
    x="concentration",
    y="response",
    color=palette_dict["Erlotinib"],
    linewidth=3,
    errorbar=None,
    estimator="mean",
    ax=ax,
    zorder=4,
    label="_nolegend_",
)

# Data points via seaborn scatterplot with style mapping
sns.scatterplot(
    data=df,
    x="concentration",
    y="response",
    hue="compound",
    style="compound",
    markers={"Imatinib": "o", "Erlotinib": "s"},
    palette=palette_dict,
    s=180,
    edgecolor="white",
    linewidth=1.5,
    zorder=5,
    ax=ax,
    legend=True,
)

# Error bars (seaborn scatterplot doesn't support yerr natively)
for compound in ["Imatinib", "Erlotinib"]:
    sub = df[df["compound"] == compound]
    ax.errorbar(
        sub["concentration"],
        sub["response"],
        yerr=sub["sem"],
        fmt="none",
        ecolor=palette_dict[compound],
        capsize=5,
        capthick=2,
        elinewidth=2,
        alpha=0.7,
        zorder=4,
    )

# EC50 reference lines
for compound in ["Imatinib", "Erlotinib"]:
    popt = fit_params[compound]
    ec50_val, half_resp = popt[2], popt[0] + (popt[1] - popt[0]) / 2
    ax.hlines(
        half_resp,
        x_fit[0],
        ec50_val,
        colors=palette_dict[compound],
        linestyles="dashed",
        linewidth=1.5,
        alpha=0.6,
        zorder=3,
    )
    ax.vlines(
        ec50_val, -5, half_resp, colors=palette_dict[compound], linestyles="dashed", linewidth=1.5, alpha=0.6, zorder=3
    )

# Asymptote lines
for compound, style in [("Imatinib", (5, 5)), ("Erlotinib", (2, 4))]:
    popt = fit_params[compound]
    ax.axhline(popt[0], color=palette_dict[compound], linestyle=(0, style), linewidth=1, alpha=0.35, zorder=1)
    ax.axhline(popt[1], color=palette_dict[compound], linestyle=(0, style), linewidth=1, alpha=0.35, zorder=1)

# Style
ax.set_xscale("log")
ax.set_xlabel("Concentration (M)", fontsize=20)
ax.set_ylabel("Response (%)", fontsize=20)
ax.set_title("curve-dose-response · seaborn · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
sns.despine(ax=ax)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
ax.set_ylim(-5, 110)

# Custom legend
custom_handles = [
    Line2D([0], [0], color=palette_dict["Imatinib"], linewidth=3, label="Imatinib (fit)"),
    Line2D([0], [0], color=palette_dict["Erlotinib"], linewidth=3, label="Erlotinib (fit)"),
    Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor=palette_dict["Imatinib"],
        markersize=12,
        markeredgecolor="white",
        label="Imatinib (data)",
    ),
    Line2D(
        [0],
        [0],
        marker="s",
        color="w",
        markerfacecolor=palette_dict["Erlotinib"],
        markersize=12,
        markeredgecolor="white",
        label="Erlotinib (data)",
    ),
    Patch(facecolor=palette_dict["Imatinib"], alpha=0.3, label="95% CI (Imatinib)"),
]
ax.legend(handles=custom_handles, fontsize=14, frameon=False, loc="upper left")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
