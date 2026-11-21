"""anyplot.ai
diagnostic-regression-panel: Regression Diagnostic Panel (Four-Plot Display)
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *
from scipy import stats
from statsmodels.nonparametric.smoothers_lowess import lowess


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID_COLOR = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]
SMOOTHER = IMPRINT_PALETTE[1]
REFERENCE = IMPRINT_PALETTE[2]
CONTOUR = IMPRINT_PALETTE[3]

TITLE = "diagnostic-regression-panel · python · letsplot · anyplot.ai"

# Constants
N_PARAMS = 3  # intercept + two predictors of the fitted linear model
COOK_LEVELS = [0.5, 1.0]  # Cook's distance contours named by the spec
N_LABELED = 3  # most influential observations labeled in every panel

# Columns
FITTED = "Fitted log(Salary)"  # role: fitted
RESIDUALS = "Residuals"  # role: residuals
STD_RESIDUALS = "Standardized Residuals"  # role: std_residuals
LEVERAGE = "Leverage (Hat Value)"  # role: leverage
COOKS_D = "Cook's Distance"  # role: cooks_d

# Data: replace this block with your own table, for example df = pd.read_csv("model_diagnostics.csv")
# Salary regression with heteroscedastic noise and three injected influential observations
np.random.seed(42)
n_obs = 150
x1 = np.random.normal(0, 1, n_obs)  # years of experience (standardised)
x2 = np.random.uniform(-2, 2, n_obs)  # education index
noise = np.random.normal(0, 0.8 + 0.4 * np.abs(x1), n_obs)
y = 3.0 + 2.0 * x1 - 1.2 * x2 + noise  # log(Salary / median)
x1[[0, 1, 2]] = [4.0, -3.8, 4.5]
x2[[0, 1, 2]] = [-3.0, 2.8, -2.5]
y[[0, 1, 2]] = [16.0, -11.0, 19.0]

design = np.column_stack([np.ones(n_obs), x1, x2])
xtx_inv = np.linalg.inv(design.T @ design)
fit_values = design @ (xtx_inv @ design.T @ y)
resid = y - fit_values
mse = np.sum(resid**2) / (n_obs - N_PARAMS)
hat = np.diag(design @ xtx_inv @ design.T)
std_resid = resid / np.sqrt(mse * (1 - hat))
cooks = (std_resid**2 * hat) / (N_PARAMS * (1 - hat))

df = pd.DataFrame({FITTED: fit_values, RESIDUALS: resid, STD_RESIDUALS: std_resid, LEVERAGE: hat, COOKS_D: cooks})

# Plot
top = np.argsort(df[COOKS_D].to_numpy())[-N_LABELED:][::-1]
n = len(df)
labels = pd.DataFrame({"idx": [str(i) for i in top]})


def y_span(col, frame=df):
    return frame[col].max() - frame[col].min()


anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_border=element_blank(),
    panel_grid_major=element_line(color=GRID_COLOR, size=0.5),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=12, face="bold"),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=8),
    legend_title=element_text(color=INK, size=9),
)

# Panel 1: Residuals vs Fitted
lw1 = lowess(df[RESIDUALS], df[FITTED], frac=0.4, return_sorted=True)
smooth1 = pd.DataFrame({FITTED: lw1[:, 0], RESIDUALS: lw1[:, 1]})
lab1 = df.iloc[top].assign(label=labels["idx"].to_numpy())

p1 = (
    ggplot(df, aes(FITTED, RESIDUALS))
    + geom_hline(yintercept=0, color=INK_SOFT, size=0.5, linetype="dashed")
    + geom_point(color=BRAND, size=1.5, alpha=0.65)
    + geom_line(data=smooth1, mapping=aes(FITTED, RESIDUALS), color=SMOOTHER, size=0.8)
    + geom_text(
        data=lab1, mapping=aes(FITTED, RESIDUALS, label="label"), color=INK, size=4, nudge_y=0.03 * y_span(RESIDUALS)
    )
    + labs(title="Residuals vs Fitted")
    + anyplot_theme
    + ggsize(800, 450)
)

# Panel 2: Normal Q-Q
order = np.argsort(df[STD_RESIDUALS].to_numpy())
sorted_std = df[STD_RESIDUALS].to_numpy()[order]
theoretical = stats.norm.ppf(np.linspace(0.5 / n, 1 - 0.5 / n, n))
qq = pd.DataFrame({"Theoretical Quantiles": theoretical, STD_RESIDUALS: sorted_std})

q25, q75 = np.percentile(sorted_std, [25, 75])
t25, t75 = stats.norm.ppf([0.25, 0.75])
qq_slope = (q75 - q25) / (t75 - t25)
qq_intercept = q25 - qq_slope * t25
t_range = np.linspace(theoretical.min() * 1.1, theoretical.max() * 1.1, 80)
qq_ref = pd.DataFrame({"Theoretical Quantiles": t_range, STD_RESIDUALS: qq_intercept + qq_slope * t_range})

# Label the most extreme points, staggered so the neighbours in the upper tail stay apart
extreme = np.argsort(np.abs(sorted_std))[-N_LABELED:]
extreme = extreme[np.argsort(theoretical[extreme])]
qq_span = y_span(STD_RESIDUALS)
qq_labels = pd.DataFrame(
    {
        "Theoretical Quantiles": theoretical[extreme] + np.array([-0.50, 0.20, 0.20]),
        STD_RESIDUALS: sorted_std[extreme] + qq_span * np.array([0.0, 0.03, -0.025]),
        "label": [str(order[k]) for k in extreme],
    }
)

p2 = (
    ggplot(qq, aes("Theoretical Quantiles", STD_RESIDUALS))
    + geom_line(data=qq_ref, mapping=aes("Theoretical Quantiles", STD_RESIDUALS), color=REFERENCE, size=0.8)
    + geom_point(color=BRAND, size=1.5, alpha=0.65)
    + geom_text(data=qq_labels, mapping=aes("Theoretical Quantiles", STD_RESIDUALS, label="label"), color=INK, size=4)
    + labs(title="Normal Q-Q")
    + anyplot_theme
    + ggsize(800, 450)
)

# Panel 3: Scale-Location
SQRT_ABS = f"√|{STD_RESIDUALS}|"
df3 = pd.DataFrame({FITTED: df[FITTED], SQRT_ABS: np.sqrt(np.abs(df[STD_RESIDUALS]))})
lw3 = lowess(df3[SQRT_ABS], df3[FITTED], frac=0.4, return_sorted=True)
smooth3 = pd.DataFrame({FITTED: lw3[:, 0], SQRT_ABS: lw3[:, 1]})
lab3 = df3.iloc[top].assign(label=labels["idx"].to_numpy())

p3 = (
    ggplot(df3, aes(FITTED, SQRT_ABS))
    + geom_point(color=BRAND, size=1.5, alpha=0.65)
    + geom_line(data=smooth3, mapping=aes(FITTED, SQRT_ABS), color=SMOOTHER, size=0.8)
    + geom_text(
        data=lab3, mapping=aes(FITTED, SQRT_ABS, label="label"), color=INK, size=4, nudge_y=0.03 * y_span(SQRT_ABS, df3)
    )
    + labs(title="Scale-Location")
    + anyplot_theme
    + ggsize(800, 450)
)

# Panel 4: Residuals vs Leverage with Cook's distance contours
h_seq = np.linspace(0.001, df[LEVERAGE].max() * 1.25, 400)
std_lim = df[STD_RESIDUALS].abs().max() * 1.15
contour_rows = []
for level in COOK_LEVELS:
    r_vals = np.sqrt(level * N_PARAMS * (1 - h_seq) / h_seq)
    keep = r_vals <= std_lim
    for sign, tag in [(1, "pos"), (-1, "neg")]:
        contour_rows.append(
            pd.DataFrame({LEVERAGE: h_seq[keep], STD_RESIDUALS: sign * r_vals[keep], "grp": f"D={level}_{tag}"})
        )
contours = pd.concat(contour_rows, ignore_index=True)
lab4 = df.iloc[top].assign(label=labels["idx"].to_numpy())

p4 = (
    ggplot(df, aes(LEVERAGE, STD_RESIDUALS))
    + geom_hline(yintercept=0, color=INK_SOFT, size=0.5, linetype="dashed")
    + geom_line(
        data=contours, mapping=aes(LEVERAGE, STD_RESIDUALS, group="grp"), color=CONTOUR, size=0.6, linetype="dashed"
    )
    + geom_point(color=BRAND, size=1.5, alpha=0.65)
    + geom_text(
        data=lab4,
        mapping=aes(LEVERAGE, STD_RESIDUALS, label="label"),
        color=INK,
        size=4,
        nudge_y=0.03 * y_span(STD_RESIDUALS),
    )
    + labs(title="Residuals vs Leverage")
    + anyplot_theme
    + ggsize(800, 450)
)

# Assemble the 2x2 panel under one shared figure title
panel = (
    gggrid([p1, p2, p3, p4], ncol=2)
    + labs(title=TITLE)
    + ggsize(800, 450)
    + theme(plot_title=element_text(color=INK, size=12, face="bold"))
)

ggsave(panel, f"plot-{THEME}.png", path=".", scale=4)
ggsave(panel, f"plot-{THEME}.html", path=".")
