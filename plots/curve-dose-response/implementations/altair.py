"""pyplots.ai
curve-dose-response: Pharmacological Dose-Response Curve
Library: altair | Python 3.13
Quality: pending | Created: 2026-03-18
"""

import altair as alt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import t as t_dist


# Data
np.random.seed(42)

concentrations = np.logspace(-9, -4, 10)


def logistic_4pl(x, bottom, top, ec50, hill):
    return bottom + (top - bottom) / (1 + (ec50 / x) ** hill)


compound_params = {
    "Compound A": {"bottom": 5, "top": 95, "ec50": 1e-7, "hill": 1.2},
    "Compound B": {"bottom": 8, "top": 88, "ec50": 3e-6, "hill": 1.8},
}

rows = []
for name, params in compound_params.items():
    true_response = logistic_4pl(concentrations, params["bottom"], params["top"], params["ec50"], params["hill"])
    noise = np.random.normal(0, 3, size=(5, len(concentrations)))
    replicates = true_response + noise
    means = replicates.mean(axis=0)
    sems = replicates.std(axis=0, ddof=1) / np.sqrt(5)
    for c, m, s in zip(concentrations, means, sems, strict=True):
        rows.append(
            {
                "concentration": c,
                "log_conc": np.log10(c),
                "response": m,
                "sem": s,
                "response_upper": m + s,
                "response_lower": m - s,
                "compound": name,
            }
        )

df = pd.DataFrame(rows)

# Fit 4PL curves and generate smooth fit lines
fit_rows = []
ref_rows = []
ci_rows = []

for name, group in df.groupby("compound"):
    xdata = group["concentration"].values
    ydata = group["response"].values
    params_init = compound_params[name]
    p0 = [params_init["bottom"], params_init["top"], params_init["ec50"], params_init["hill"]]

    popt, pcov = curve_fit(logistic_4pl, xdata, ydata, p0=p0, maxfev=10000)
    bottom_fit, top_fit, ec50_fit, hill_fit = popt

    x_smooth = np.logspace(-9.5, -3.5, 200)
    y_smooth = logistic_4pl(x_smooth, *popt)

    for xs, ys in zip(x_smooth, y_smooth, strict=True):
        fit_rows.append({"log_conc": np.log10(xs), "response": ys, "compound": name})

    # 95% CI via delta method
    n = len(xdata)
    dof = n - len(popt)
    t_val = t_dist.ppf(0.975, dof)

    jacobian = np.zeros((len(x_smooth), 4))
    for i, xs in enumerate(x_smooth):
        ratio = (ec50_fit / xs) ** hill_fit
        denom = 1 + ratio
        jacobian[i, 0] = 1 - 1 / denom
        jacobian[i, 1] = 1 / denom
        jacobian[i, 2] = -(top_fit - bottom_fit) * hill_fit * ratio / (ec50_fit * denom**2)
        jacobian[i, 3] = -(top_fit - bottom_fit) * ratio * np.log(ec50_fit / xs) / denom**2

    pred_var = np.array([j @ pcov @ j for j in jacobian])
    pred_se = np.sqrt(np.maximum(pred_var, 0))
    ci_upper = logistic_4pl(x_smooth, *popt) + t_val * pred_se
    ci_lower = logistic_4pl(x_smooth, *popt) - t_val * pred_se

    for xs, cu, cl in zip(x_smooth, ci_upper, ci_lower, strict=True):
        ci_rows.append({"log_conc": np.log10(xs), "ci_upper": cu, "ci_lower": cl, "compound": name})

    # EC50 reference lines
    half_response = (bottom_fit + top_fit) / 2
    ref_rows.append(
        {
            "compound": name,
            "ec50_log": np.log10(ec50_fit),
            "half_response": half_response,
            "bottom_fit": bottom_fit,
            "top_fit": top_fit,
        }
    )

df_fit = pd.DataFrame(fit_rows)
df_ci = pd.DataFrame(ci_rows)
df_ref = pd.DataFrame(ref_rows)

# Plot
color_scale = alt.Scale(domain=["Compound A", "Compound B"], range=["#306998", "#E8792B"])

base_x = alt.X("log_conc:Q", title="log₁₀ Concentration (M)", scale=alt.Scale(domain=[-9.5, -3.5]))
base_y = alt.Y("response:Q", title="Response (%)", scale=alt.Scale(domain=[-5, 110]))

# Confidence bands
ci_band = (
    alt.Chart(df_ci)
    .mark_area(opacity=0.15)
    .encode(
        x=alt.X("log_conc:Q", title=""),
        y=alt.Y("ci_lower:Q", title=""),
        y2="ci_upper:Q",
        color=alt.Color("compound:N", scale=color_scale, legend=None),
    )
)

# Fitted curves
fitted_lines = (
    alt.Chart(df_fit)
    .mark_line(strokeWidth=3)
    .encode(
        x=alt.X("log_conc:Q", title=""), y=base_y, color=alt.Color("compound:N", scale=color_scale, title="Compound")
    )
)

# Data points with error bars
error_bars = (
    alt.Chart(df)
    .mark_rule(strokeWidth=2)
    .encode(
        x=alt.X("log_conc:Q", title=""),
        y=alt.Y("response_lower:Q", title=""),
        y2="response_upper:Q",
        color=alt.Color("compound:N", scale=color_scale, legend=None),
    )
)

data_points = (
    alt.Chart(df)
    .mark_point(size=180, filled=True, stroke="white", strokeWidth=1.5)
    .encode(
        x=base_x,
        y=base_y,
        color=alt.Color("compound:N", scale=color_scale, legend=None),
        tooltip=[
            alt.Tooltip("compound:N", title="Compound"),
            alt.Tooltip("log_conc:Q", title="log₁₀ [C]", format=".1f"),
            alt.Tooltip("response:Q", title="Response (%)", format=".1f"),
        ],
    )
)

# EC50 reference lines (horizontal + vertical dashed)
ec50_hlines = (
    alt.Chart(df_ref)
    .mark_rule(strokeDash=[8, 6], strokeWidth=1.5, opacity=0.6)
    .encode(y=alt.Y("half_response:Q", title=""), color=alt.Color("compound:N", scale=color_scale, legend=None))
)

ec50_vlines = (
    alt.Chart(df_ref)
    .mark_rule(strokeDash=[8, 6], strokeWidth=1.5, opacity=0.6)
    .encode(x=alt.X("ec50_log:Q", title=""), color=alt.Color("compound:N", scale=color_scale, legend=None))
)

# Asymptote lines (top and bottom)
asymptote_top = (
    alt.Chart(df_ref)
    .mark_rule(strokeDash=[4, 4], strokeWidth=1, opacity=0.35)
    .encode(y=alt.Y("top_fit:Q", title=""), color=alt.Color("compound:N", scale=color_scale, legend=None))
)

asymptote_bottom = (
    alt.Chart(df_ref)
    .mark_rule(strokeDash=[4, 4], strokeWidth=1, opacity=0.35)
    .encode(y=alt.Y("bottom_fit:Q", title=""), color=alt.Color("compound:N", scale=color_scale, legend=None))
)

# Combine all layers
chart = (
    (ci_band + asymptote_top + asymptote_bottom + ec50_hlines + ec50_vlines + fitted_lines + error_bars + data_points)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("curve-dose-response · altair · pyplots.ai", fontSize=28, anchor="start"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.15)
    .configure_legend(titleFontSize=20, labelFontSize=18, symbolSize=200, orient="top-right")
    .configure_view(strokeWidth=0)
    .interactive()
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
