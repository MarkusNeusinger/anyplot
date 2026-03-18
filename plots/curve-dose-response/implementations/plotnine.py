""" pyplots.ai
curve-dose-response: Pharmacological Dose-Response Curve
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-18
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_text,
    geom_errorbar,
    geom_hline,
    geom_line,
    geom_point,
    geom_ribbon,
    geom_segment,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_x_log10,
    theme,
    theme_minimal,
)
from scipy.optimize import curve_fit


# Data
np.random.seed(42)

concentrations = np.logspace(-9, -4, 8)


def logistic_4pl(x, bottom, top, ec50, hill):
    return bottom + (top - bottom) / (1 + (ec50 / x) ** hill)


compound_a_true = {"bottom": 5, "top": 95, "ec50": 1e-7, "hill": 1.2}
compound_b_true = {"bottom": 10, "top": 85, "ec50": 5e-7, "hill": 0.9}

rows = []
for conc in concentrations:
    resp_a = logistic_4pl(conc, **compound_a_true) + np.random.normal(0, 3)
    resp_b = logistic_4pl(conc, **compound_b_true) + np.random.normal(0, 3.5)
    sem_a = np.random.uniform(1.5, 4.0)
    sem_b = np.random.uniform(2.0, 4.5)
    rows.append({"concentration": conc, "response": resp_a, "response_sem": sem_a, "compound": "Compound A"})
    rows.append({"concentration": conc, "response": resp_b, "response_sem": sem_b, "compound": "Compound B"})

df = pd.DataFrame(rows)

# Fit 4PL curves
fit_params = {}
for compound in ["Compound A", "Compound B"]:
    subset = df[df["compound"] == compound]
    popt, pcov = curve_fit(
        logistic_4pl, subset["concentration"].values, subset["response"].values, p0=[5, 90, 1e-6, 1.0], maxfev=10000
    )
    fit_params[compound] = {"popt": popt, "pcov": pcov}

# Generate smooth fitted curves
conc_smooth = np.logspace(-9.5, -3.5, 200)
fit_rows = []
for compound, params in fit_params.items():
    popt = params["popt"]
    pcov = params["pcov"]
    fitted = logistic_4pl(conc_smooth, *popt)

    # Confidence interval via delta method (numerical Jacobian)
    jacobian = np.zeros((len(conc_smooth), 4))
    eps = 1e-8
    for i in range(4):
        popt_up = popt.copy()
        popt_up[i] += eps
        popt_dn = popt.copy()
        popt_dn[i] -= eps
        jacobian[:, i] = (logistic_4pl(conc_smooth, *popt_up) - logistic_4pl(conc_smooth, *popt_dn)) / (2 * eps)
    variance = np.sum(jacobian @ pcov * jacobian, axis=1)
    se = np.sqrt(np.maximum(variance, 0))

    for j, c in enumerate(conc_smooth):
        fit_rows.append(
            {
                "concentration": c,
                "fitted": fitted[j],
                "ci_lower": fitted[j] - 1.96 * se[j],
                "ci_upper": fitted[j] + 1.96 * se[j],
                "compound": compound,
            }
        )

df_fit = pd.DataFrame(fit_rows)

# EC50 reference data
colors = {"Compound A": "#306998", "Compound B": "#E0652B"}
ec50_rows = []
for compound, params in fit_params.items():
    popt = params["popt"]
    bottom, top, ec50, hill = popt
    half_response = bottom + (top - bottom) / 2
    ec50_rows.append({"compound": compound, "ec50": ec50, "half_response": half_response, "bottom": bottom, "top": top})

df_ec50 = pd.DataFrame(ec50_rows)

# Plot
plot = (
    ggplot()
    + geom_ribbon(aes(x="concentration", ymin="ci_lower", ymax="ci_upper", fill="compound"), data=df_fit, alpha=0.15)
    + geom_line(aes(x="concentration", y="fitted", color="compound"), data=df_fit, size=1.5)
    + geom_errorbar(
        aes(x="concentration", ymin="response - response_sem", ymax="response + response_sem", color="compound"),
        data=df,
        width=0.08,
        size=0.7,
    )
    + geom_point(aes(x="concentration", y="response", color="compound"), data=df, size=4, fill="white", stroke=0.8)
)

# EC50 reference lines
for _, row in df_ec50.iterrows():
    col = colors[row["compound"]]
    plot = (
        plot
        + geom_segment(
            aes(x="ec50", xend="ec50", y=0, yend="half_response"),
            data=pd.DataFrame([row]),
            linetype="dashed",
            color=col,
            size=0.6,
            alpha=0.6,
        )
        + geom_segment(
            aes(x=1e-10, xend="ec50", y="half_response", yend="half_response"),
            data=pd.DataFrame([row]),
            linetype="dashed",
            color=col,
            size=0.6,
            alpha=0.6,
        )
    )

# Top/bottom asymptote lines
for _, row in df_ec50.iterrows():
    col = colors[row["compound"]]
    plot = (
        plot
        + geom_hline(yintercept=row["top"], linetype="dotted", color=col, size=0.5, alpha=0.35)
        + geom_hline(yintercept=row["bottom"], linetype="dotted", color=col, size=0.5, alpha=0.35)
    )

# Style
plot = (
    plot
    + scale_x_log10(labels=lambda lst: [f"1e{int(np.log10(v))}" if v > 0 else "0" for v in lst])
    + scale_color_manual(values=colors)
    + scale_fill_manual(values=colors)
    + labs(
        x="Concentration (M)",
        y="Response (%)",
        title="curve-dose-response · plotnine · pyplots.ai",
        color="Compound",
        fill="Compound",
    )
    + guides(fill=guide_legend(title="Compound"))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24, weight="bold"),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position=(0.8, 0.25),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#dddddd", size=0.5, alpha=0.3),
        axis_line=element_line(color="#333333", size=0.5),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
