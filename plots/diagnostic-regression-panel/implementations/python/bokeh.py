"""anyplot.ai
diagnostic-regression-panel: Regression Diagnostic Panel (Four-Plot Display)
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-11-21
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.layouts import column, gridplot
from bokeh.models import ColumnDataSource, Div, LabelSet, Range1d, Span
from bokeh.plotting import figure, output_file, save
from scipy.stats import probplot
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from statsmodels.nonparametric.smoothers_lowess import lowess


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: points, smoothers/reference lines, Cook's distance contours
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
COOK_LEVELS = [0.5, 1.0]  # Cook's distance contours the spec asks for
N_LABELS = 3  # most influential observations labelled in every panel
LOWESS_FRAC = 0.5

# Columns: set these to your table's column names
FITTED = "Fitted values"  # role: fitted
RESIDUALS = "Residuals"  # role: residuals
STD_RESIDUALS = "Standardized residuals"  # role: std_residuals
LEVERAGE = "Leverage"  # role: leverage
COOKS_D = "Cook's distance"  # role: cooks_d

# Data: replace this block with your own table, for example df = pd.read_csv("diagnostics.csv")
# Drug-response study: response ~ log-dose + body-mass index + age, fitted by OLS
np.random.seed(42)
n = 200
X = np.column_stack([np.random.normal(0, 1, n) for _ in range(3)])  # standardised log-dose, BMI, age
X[0] = [3.0, 2.5, -2.0]  # high-leverage patient
X[1] = [-2.8, -2.2, 2.5]  # moderate-leverage patient
response = 50 + X @ np.array([8.0, -5.0, 3.0]) + np.random.normal(0, 4.0, n)
response[0] += 14.0  # large residual at high leverage -> influential
response[1] -= 11.0  # moderate residual at moderate leverage
response[70] += 10.0  # residual outlier at low leverage
design = np.column_stack([np.ones(n), X])
hat = design @ np.linalg.inv(design.T @ design) @ design.T
fitted = hat @ response
resid = response - fitted
lev = np.diag(hat)
n_par = design.shape[1]
std_resid = resid / np.sqrt(resid @ resid / (n - n_par) * (1 - lev))
df = pd.DataFrame(
    {
        FITTED: fitted,
        RESIDUALS: resid,
        STD_RESIDUALS: std_resid,
        LEVERAGE: lev,
        COOKS_D: std_resid**2 * lev / (n_par * (1 - lev)),
    }
)

# Plot: reads only df and the constants above
n_params = int(round(df[LEVERAGE].sum()))  # trace of the hat matrix = number of model parameters
sqrt_abs = np.sqrt(df[STD_RESIDUALS].abs())
SQRT_ABS = f"√|{STD_RESIDUALS}|"
df[SQRT_ABS] = sqrt_abs

# Q-Q: theoretical normal quantile of every observation
order = np.argsort(df[STD_RESIDUALS].to_numpy())
(theory, sample), (qq_slope, qq_intercept, _) = probplot(df[STD_RESIDUALS], dist="norm")
THEORY = "Theoretical quantiles"
df[THEORY] = np.nan
df.iloc[order, df.columns.get_loc(THEORY)] = theory

lowess_resid = lowess(df[RESIDUALS], df[FITTED], frac=LOWESS_FRAC)
lowess_scale = lowess(df[SQRT_ABS], df[FITTED], frac=LOWESS_FRAC)

top = df.nlargest(N_LABELS, COOKS_D).index
df["obs"] = df.index.astype(str)
source = ColumnDataSource(df)
labels = ColumnDataSource(df.loc[top])

W, H = 3200, 1800
TITLE_H = 100
PW, PH = W // 2, (H - TITLE_H) // 2


def panel(title, x, y, x_label, y_label):
    p = figure(
        width=PW,
        height=PH,
        title=title,
        x_axis_label=x_label,
        y_axis_label=y_label,
        background_fill_color=PAGE_BG,
        border_fill_color=PAGE_BG,
        outline_line_color=None,
        toolbar_location=None,
        min_border_left=130,
        min_border_bottom=100,
        min_border_top=30,
        min_border_right=40,
    )
    p.title.text_font_size = "30pt"
    p.title.text_font_style = "bold"
    p.title.text_color = INK
    for axis in (p.xaxis, p.yaxis):
        axis.axis_label_text_font_size = "24pt"
        axis.axis_label_text_font_style = "normal"
        axis.major_label_text_font_size = "20pt"
        axis.axis_label_text_color = INK
        axis.major_label_text_color = INK_SOFT
        axis.axis_line_color = INK_SOFT
        axis.major_tick_line_color = INK_SOFT
        axis.minor_tick_line_color = None
    for grid in (p.xgrid, p.ygrid):
        grid.grid_line_color = INK
        grid.grid_line_alpha = 0.10
    p.scatter(x, y, source=source, color=IMPRINT_PALETTE[0], size=10, alpha=0.65, line_color=PAGE_BG, line_width=0.5)
    return p


def label_top(p, x, y):
    p.add_layout(
        LabelSet(x=x, y=y, text="obs", source=labels, text_font_size="20pt", text_color=INK, x_offset=8, y_offset=8)
    )


def zero_line():
    return Span(location=0, dimension="width", line_color=INK_SOFT, line_dash="dashed", line_width=2)


# Panel 1: Residuals vs Fitted
p1 = panel("Residuals vs Fitted", FITTED, RESIDUALS, FITTED, RESIDUALS)
p1.add_layout(zero_line())
p1.line(lowess_resid[:, 0], lowess_resid[:, 1], color=IMPRINT_PALETTE[1], line_width=4)
label_top(p1, FITTED, RESIDUALS)

# Panel 2: Normal Q-Q
p2 = panel("Normal Q-Q", THEORY, STD_RESIDUALS, THEORY, STD_RESIDUALS)
qq_x = np.array([theory.min(), theory.max()])
p2.line(qq_x, qq_slope * qq_x + qq_intercept, color=IMPRINT_PALETTE[1], line_width=3, line_dash="dashed")
label_top(p2, THEORY, STD_RESIDUALS)

# Panel 3: Scale-Location
p3 = panel("Scale-Location", FITTED, SQRT_ABS, FITTED, SQRT_ABS)
p3.line(lowess_scale[:, 0], lowess_scale[:, 1], color=IMPRINT_PALETTE[1], line_width=4)
label_top(p3, FITTED, SQRT_ABS)

# Panel 4: Residuals vs Leverage with Cook's distance contours
p4 = panel("Residuals vs Leverage", LEVERAGE, STD_RESIDUALS, LEVERAGE, STD_RESIDUALS)
lev_hi = min(df[LEVERAGE].max() * 1.3, 0.99)
cook_edge = np.sqrt(max(COOK_LEVELS) * n_params * (1 - lev_hi) / lev_hi)  # highest contour at the right edge
y_lim = max(np.percentile(df[STD_RESIDUALS].abs(), 96), df.loc[top, STD_RESIDUALS].abs().max(), cook_edge) * 1.08
p4.y_range = Range1d(-y_lim, y_lim)
p4.add_layout(zero_line())
lev_grid = np.linspace(1e-4, lev_hi, 400)
for level, dash in zip(COOK_LEVELS, ["dashed", "dotdash"], strict=True):
    contour = np.sqrt(level * n_params * (1 - lev_grid) / lev_grid)
    keep = contour <= y_lim * 1.05
    p4.line(
        lev_grid[keep],
        contour[keep],
        color=IMPRINT_PALETTE[2],
        line_width=3,
        line_dash=dash,
        legend_label=f"{COOKS_D} = {level:g}",
    )
    p4.line(lev_grid[keep], -contour[keep], color=IMPRINT_PALETTE[2], line_width=3, line_dash=dash)
label_top(p4, LEVERAGE, STD_RESIDUALS)
p4.legend.location = "top_left"
p4.legend.background_fill_color = ELEVATED_BG
p4.legend.border_line_color = INK_SOFT
p4.legend.label_text_color = INK
p4.legend.label_text_font_size = "20pt"

# Assemble with the shared figure title
grid = gridplot([[p1, p2], [p3, p4]], merge_tools=False, toolbar_location=None)
title_div = Div(
    text=(
        f'<div style="font-family: sans-serif; font-size: 56px; font-weight: 600; color: {INK};'
        f' background-color: {PAGE_BG}; padding: 22px 32px 0 32px; margin: 0;">'
        "diagnostic-regression-panel · python · bokeh · anyplot.ai</div>"
    ),
    width=W,
    height=TITLE_H,
)
output_file(f"plot-{THEME}.html")
save(column(title_div, grid, spacing=0))

opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.execute_script(
    f"document.body.style.backgroundColor='{PAGE_BG}';"
    "document.body.style.margin='0';"
    f"document.documentElement.style.backgroundColor='{PAGE_BG}';"
)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
