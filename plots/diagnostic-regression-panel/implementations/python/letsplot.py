"""anyplot.ai
diagnostic-regression-panel: Regression Diagnostic Panel (Four-Plot Display)
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Created: 2026-05-13
"""

import os

import numpy as np
import pandas as pd
import statsmodels.api as sm
from lets_plot import *
from scipy import stats
from statsmodels.nonparametric.smoothers_lowess import lowess


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID_COLOR = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: points, smoothers, reference lines and contours take positions 1-4
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]
SMOOTHER = IMPRINT_PALETTE[1]
REFERENCE = IMPRINT_PALETTE[2]
CONTOUR = IMPRINT_PALETTE[3]

# Constants
COOKS_LEVELS = [0.5, 1.0]  # the contour levels R's plot(lm) draws
N_LABELLED = 3  # most influential observations labelled in every panel

# Columns: set these to your table's column names
FITTED = "Fitted log(Salary)"  # role: fitted
RESIDUALS = "Residuals"  # role: residuals
STD_RES = "Standardized Residuals"  # role: std_residuals
LEVERAGE = "Leverage (Hat Value)"  # role: leverage
COOKS_D = "Cook's distance"  # role: cooks_d

# Data: replace this block with your own diagnostics table, one row per observation
np.random.seed(42)
n = 150
# x1: years of experience (standardised), x2: education index
x1 = np.random.normal(0, 1, n)
x2 = np.random.uniform(-2, 2, n)
noise = np.random.normal(0, 0.8 + 0.4 * np.abs(x1), n)
y = 3.0 + 2.0 * x1 - 1.2 * x2 + noise  # log(Salary / median)

# Inject influential outliers (extreme experience / education combinations)
x1[[0, 1, 2]] = [4.0, -3.8, 4.5]
x2[[0, 1, 2]] = [-3.0, 2.8, -2.5]
y[[0, 1, 2]] = [16.0, -11.0, 19.0]

fit = sm.OLS(y, sm.add_constant(np.column_stack([x1, x2]))).fit()
influence = fit.get_influence()
df = pd.DataFrame(
    {
        FITTED: fit.fittedvalues,
        RESIDUALS: fit.resid,
        STD_RES: influence.resid_studentized_internal,
        LEVERAGE: influence.hat_matrix_diag,
        COOKS_D: influence.cooks_distance[0],
    }
)

# Plot
n_obs = len(df)
# Cook's D = r^2 h / (p (1 - h)) holds for every row, so the parameter count follows from the table
h_col, r_col, d_col = df[LEVERAGE], df[STD_RES], df[COOKS_D]
n_params = (r_col**2 * h_col / (d_col * (1 - h_col))).replace([np.inf, -np.inf], np.nan).median()
top = df[COOKS_D].nlargest(N_LABELLED).index
labels = pd.DataFrame({"obs": [str(i) for i in top]})

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_border=element_blank(),
    panel_grid_major=element_line(color=GRID_COLOR, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=9),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=12),
)


def panel(frame, x, y_col, title, xlabel, ylabel):
    """One diagnostic panel: the shared point styling, a panel title and theme."""
    return (
        ggplot(frame, aes(x=x, y=y_col))
        + geom_point(color=BRAND, size=2, alpha=0.65)
        + labs(x=xlabel, y=ylabel, title=title)
        + anyplot_theme
    )


def label_layer(frame, x, y_col, dx=0.0, dy=0.0):
    """Observation index beside each of the most influential points."""
    pts = frame.loc[top].assign(obs=labels["obs"].to_numpy())
    pts[x] = pts[x] + dx
    pts[y_col] = pts[y_col] + dy
    return geom_text(data=pts, mapping=aes(x=x, y=y_col, label="obs"), color=INK, size=4.5, fontface="bold")


def span(col):
    return df[col].max() - df[col].min()


# Panel 1: Residuals vs Fitted
lw1 = lowess(df[RESIDUALS], df[FITTED], frac=0.4, return_sorted=True)
smooth1 = pd.DataFrame({FITTED: lw1[:, 0], RESIDUALS: lw1[:, 1]})
p1 = (
    panel(df, FITTED, RESIDUALS, "Residuals vs Fitted", FITTED, RESIDUALS)
    + geom_hline(yintercept=0, color=INK_SOFT, size=0.5, linetype="dashed")
    + geom_line(data=smooth1, mapping=aes(x=FITTED, y=RESIDUALS), color=SMOOTHER, size=1.0)
    + label_layer(df, FITTED, RESIDUALS, dx=-0.04 * span(FITTED))
    + scale_y_continuous(expand=[0.08, 0])
)

# Panel 2: Normal Q-Q (each observation at the quantile of its rank)
qq = df.assign(theoretical=stats.norm.ppf((df[STD_RES].rank() - 0.5) / n_obs))
q25, q75 = np.percentile(qq[STD_RES], [25, 75])
t25, t75 = stats.norm.ppf([0.25, 0.75])
slope = (q75 - q25) / (t75 - t25)
t_range = np.linspace(qq["theoretical"].min() * 1.1, qq["theoretical"].max() * 1.1, 80)
ref_line = pd.DataFrame({"theoretical": t_range, STD_RES: q25 + slope * (t_range - t25)})
p2 = (
    panel(qq, "theoretical", STD_RES, "Normal Q-Q", "Theoretical Quantiles", STD_RES)
    + geom_line(data=ref_line, mapping=aes(x="theoretical", y=STD_RES), color=REFERENCE, size=1.0)
    + label_layer(qq, "theoretical", STD_RES, dx=-0.09 * (qq["theoretical"].max() - qq["theoretical"].min()), dy=0.3)
    + scale_y_continuous(expand=[0.08, 0])
)

# Panel 3: Scale-Location
scale_loc = df.assign(sqrt_abs=np.sqrt(df[STD_RES].abs()))
SQRT_ABS = f"√|{STD_RES}|"
scale_loc = scale_loc.rename(columns={"sqrt_abs": SQRT_ABS})
lw3 = lowess(scale_loc[SQRT_ABS], scale_loc[FITTED], frac=0.4, return_sorted=True)
smooth3 = pd.DataFrame({FITTED: lw3[:, 0], SQRT_ABS: lw3[:, 1]})
p3 = (
    panel(scale_loc, FITTED, SQRT_ABS, "Scale-Location", FITTED, SQRT_ABS)
    + geom_line(data=smooth3, mapping=aes(x=FITTED, y=SQRT_ABS), color=SMOOTHER, size=1.0)
    + label_layer(scale_loc, FITTED, SQRT_ABS, dx=-0.04 * span(FITTED))
    + scale_y_continuous(expand=[0.08, 0])
)

# Panel 4: Residuals vs Leverage with Cook's distance contours
std_lim = df[STD_RES].abs().max() * 1.15
# Run the leverage axis far enough that the outermost contour comes inside the residual limits
h_reach = max(COOKS_LEVELS) * n_params / (std_lim**2 + max(COOKS_LEVELS) * n_params)
h_seq = np.linspace(df[LEVERAGE].min() * 0.5, max(df[LEVERAGE].max() * 1.15, h_reach * 1.08), 400)
contour_rows = []
end_labels = []
for level in COOKS_LEVELS:
    r_vals = np.sqrt(level * n_params * (1 - h_seq) / h_seq)
    keep = r_vals <= std_lim
    if not keep.any():
        continue
    name = f"D = {level:g}"
    for sign in (1, -1):
        contour_rows.append(pd.DataFrame({LEVERAGE: h_seq[keep], STD_RES: sign * r_vals[keep], "grp": f"{name}{sign}"}))
        end_labels.append({LEVERAGE: h_seq[keep][-1], STD_RES: sign * r_vals[keep][-1], "name": name})
contours = pd.concat(contour_rows, ignore_index=True)
end_labels = pd.DataFrame(end_labels)
end_labels[STD_RES] = end_labels[STD_RES] - np.sign(end_labels[STD_RES]) * 0.08 * std_lim
p4 = (
    panel(df, LEVERAGE, STD_RES, "Residuals vs Leverage", LEVERAGE, STD_RES)
    + geom_hline(yintercept=0, color=INK_SOFT, size=0.5, linetype="dashed")
    + geom_line(
        data=contours, mapping=aes(x=LEVERAGE, y=STD_RES, group="grp"), color=CONTOUR, size=0.8, linetype="dashed"
    )
    + geom_text(
        data=end_labels,
        mapping=aes(x=LEVERAGE, y=STD_RES, label="name"),
        color=CONTOUR,
        size=4,
        hjust=1,
        fontface="bold",
    )
    + label_layer(df, LEVERAGE, STD_RES, dx=-0.05 * span(LEVERAGE))
    + scale_y_continuous(limits=[-std_lim, std_lim])
)

# Assemble the 2x2 grid under one shared title; the grid paints the page colour
figure = (
    gggrid([p1, p2, p3, p4], ncol=2)
    + ggtitle("diagnostic-regression-panel · python · letsplot · anyplot.ai")
    + ggsize(800, 450)
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(color=INK, size=14, face="bold"),
    )
)

ggsave(figure, f"plot-{THEME}.png", path=".", scale=4)
ggsave(figure, f"plot-{THEME}.html", path=".")
