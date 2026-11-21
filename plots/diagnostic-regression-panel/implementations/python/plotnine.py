"""anyplot.ai
diagnostic-regression-panel: Regression Diagnostic Panel (Four-Plot Display)
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 85/100 | Updated: 2026-11-21
"""

import os
import site
import sys


# 'python plotnine.py' adds this file's directory to sys.path[0], shadowing
# the installed plotnine library. Insert site-packages at the front so the
# library is found before this file. ruff recognises sys.path.insert() as a
# valid pre-import path setup and does not raise E402 for subsequent imports.
sys.path.insert(0, site.getsitepackages()[0])

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    facet_wrap,
    geom_hline,
    geom_line,
    geom_point,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    theme,
)
from scipy.stats import probplot
from statsmodels.nonparametric.smoothers_lowess import lowess


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
PANELS = ["Residuals vs Fitted", "Normal Q-Q", "Scale-Location", "Residuals vs Leverage"]
COOK_LEVELS = [0.5, 1.0]  # Cook's distance contours drawn in the leverage panel
N_LABELED = 3  # most influential observations labeled with their index in every panel

# Columns: set these to your table's column names
FITTED = "Fitted values"  # role: fitted
RESIDUALS = "Residuals"  # role: residuals
STD_RESID = "Standardized residuals"  # role: std_residuals
LEVERAGE = "Leverage"  # role: leverage
COOKS_D = "Cook's distance"  # role: cooks_d

# Data: replace this block with your own table, for example df = pd.read_csv("diagnostics.csv")
# Materials testing: tensile strength vs temperature and load, fitted by OLS.
# Three high-temperature runs are high-leverage points, two runs are response outliers.
np.random.seed(42)
temperature = np.concatenate([np.random.uniform(20, 80, 97), [180.0, 195.0, 210.0]])
load = np.random.normal(50, 10, 100)
strength = 120 - 0.3 * temperature + 0.8 * load + np.random.normal(0, 2 + 0.04 * temperature, 100)
strength[20] += 25.0
strength[55] -= 28.0

design = np.column_stack([np.ones(len(strength)), temperature, load])
beta = np.linalg.lstsq(design, strength, rcond=None)[0]
hat = design @ np.linalg.inv(design.T @ design) @ design.T
resid = strength - design @ beta
lev = np.diag(hat)
n_params = design.shape[1]
s = np.sqrt(np.sum(resid**2) / (len(strength) - n_params))
std_resid = resid / (s * np.sqrt(1 - lev))

df = pd.DataFrame(
    {
        FITTED: design @ beta,
        RESIDUALS: resid,
        STD_RESID: std_resid,
        LEVERAGE: lev,
        COOKS_D: std_resid**2 * lev / (n_params * (1 - lev)),
    }
)

# Plot: reads only df and the constants above
n = len(df)
n_params = int(round(df[LEVERAGE].sum()))  # trace of the hat matrix = number of fitted parameters
influential = set(df[COOKS_D].nlargest(N_LABELED).index)

# Normal Q-Q: each observation gets the theoretical quantile of its rank
theoretical = np.empty(n)
order = np.argsort(df[STD_RESID].to_numpy(), kind="stable")
(sorted_quantiles, _), (qq_slope, qq_intercept, _) = probplot(df[STD_RESID], dist="norm")
theoretical[order] = sorted_quantiles

sqrt_abs_std = np.sqrt(np.abs(df[STD_RESID]))
panel_xy = [
    (df[FITTED], df[RESIDUALS]),
    (pd.Series(theoretical, index=df.index), df[STD_RESID]),
    (df[FITTED], sqrt_abs_std),
    (df[LEVERAGE], df[STD_RESID]),
]
panel_cat = pd.CategoricalDtype(PANELS, ordered=True)


def on_panel(frame, name):
    return frame.assign(panel=pd.Categorical([name] * len(frame), dtype=panel_cat))


df_points = pd.concat(
    [
        on_panel(
            pd.DataFrame(
                {
                    "x_val": x,
                    "y_val": y,
                    "obs_id": df.index,
                    "influence": pd.Categorical(
                        ["high" if i in influential else "normal" for i in df.index], categories=["normal", "high"]
                    ),
                }
            ),
            name,
        )
        for name, (x, y) in zip(PANELS, panel_xy, strict=True)
    ],
    ignore_index=True,
)
df_labels = df_points[df_points["obs_id"].isin(influential)].assign(label=lambda d: d["obs_id"].astype(str))

# LOWESS smoothers: residuals vs fitted and scale-location
smooth = [lowess(panel_xy[i][1], panel_xy[i][0], frac=0.55) for i in (0, 2)]
df_lowess = pd.concat(
    [
        on_panel(pd.DataFrame({"x_val": lw[:, 0], "y_val": lw[:, 1]}), PANELS[i])
        for lw, i in zip(smooth, (0, 2), strict=True)
    ]
)

# 45-degree reference line of the Q-Q panel
qq_ends = np.array([sorted_quantiles.min(), sorted_quantiles.max()])
df_qq_ref = on_panel(pd.DataFrame({"x_val": qq_ends, "y_val": qq_slope * qq_ends + qq_intercept}), PANELS[1])

# Zero reference lines: residuals vs fitted and residuals vs leverage
df_hline = pd.concat([on_panel(pd.DataFrame({"yintercept": [0.0]}), PANELS[i]) for i in (0, 3)])

# Cook's distance contours: |standardized residual| = sqrt(D * p * (1 - h) / h), mirrored around zero
h_grid = np.linspace(1e-4, min(df[LEVERAGE].max() * 1.3, 0.995), 500)
y_limit = max(df[STD_RESID].abs().max() * 1.1, 3.5)
contours, contour_labels = [], []
for gid, (level, sign) in enumerate([(lv, sg) for lv in COOK_LEVELS for sg in (1, -1)]):
    sr = sign * np.sqrt(level * n_params * (1 - h_grid) / h_grid)
    keep = np.abs(sr) <= y_limit
    if keep.sum() > 1:
        contours.append(pd.DataFrame({"x_val": h_grid[keep], "y_val": sr[keep], "cook_group": gid}))
        # label sits just outside the curve at its outer (low-leverage) end, where the levels are far apart
        contour_labels.append(
            {"x_val": h_grid[keep][0], "y_val": sr[keep][0] + sign * 0.02 * y_limit, "label": f"D = {level:g}"}
        )
df_cook = on_panel(pd.concat(contours, ignore_index=True), PANELS[3])
df_cook_labels = on_panel(pd.DataFrame(contour_labels), PANELS[3])

# Theme
anyplot_theme = theme(
    figure_size=(8, 4.5),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_blank(),
    panel_border=element_rect(color=INK_SOFT, fill=None),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    plot_title=element_text(color=INK, size=12),
    strip_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    strip_text=element_text(color=INK, size=10),
    panel_spacing_x=0.06,
    panel_spacing_y=0.04,
    legend_position="none",
)

plot = (
    ggplot(df_points, aes(x="x_val", y="y_val"))
    + geom_hline(data=df_hline, mapping=aes(yintercept="yintercept"), color=INK_SOFT, linetype="dashed", size=0.5)
    + geom_line(data=df_lowess, mapping=aes(x="x_val", y="y_val"), color=IMPRINT_PALETTE[1], size=0.8)
    + geom_line(data=df_qq_ref, mapping=aes(x="x_val", y="y_val"), color=INK_SOFT, size=0.6, linetype="dashed")
    + geom_line(
        data=df_cook, mapping=aes(x="x_val", y="y_val", group="cook_group"), color=INK_SOFT, size=0.5, linetype="dotted"
    )
    + geom_text(data=df_cook_labels, mapping=aes(label="label"), color=INK_SOFT, size=5, ha="left", va="center")
    + geom_point(aes(color="influence"), size=1.6, alpha=0.75, stroke=0.2)
    + scale_color_manual(values={"normal": IMPRINT_PALETTE[0], "high": IMPRINT_PALETTE[1]})
    + geom_text(
        data=df_labels,
        mapping=aes(label="label"),
        va="bottom",
        ha="left",
        nudge_x=0,
        size=6,
        color=INK,
        fontweight="bold",
    )
    + facet_wrap("~panel", scales="free", ncol=2)
    + labs(title="diagnostic-regression-panel · python · plotnine · anyplot.ai", x="", y="")
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
