""" anyplot.ai
diagnostic-regression-panel: Regression Diagnostic Panel (Four-Plot Display)
Library: pygal 3.1.3 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-21
"""

import os
import sys


# Remove this script's directory from sys.path so "pygal" resolves to the installed package
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _this_dir]

import cairosvg
import numpy as np
import pandas as pd
import pygal
from pygal.style import Style
from scipy import stats
from statsmodels.nonparametric.smoothers_lowess import lowess


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
COOK_LEVELS = [0.5, 1.0]  # Cook's distance contours drawn in the leverage panel
N_LABELED = 3  # most influential observations that get an index label
N_PARAMS = 3  # intercept + two predictors of the fitted model

# Columns: set these to your table's column names
FITTED = "Fitted values"  # role: fitted
RESIDUALS = "Residuals"  # role: residuals
STD_RESIDUALS = "Standardized Residuals"  # role: std_residuals
LEVERAGE = "Leverage"  # role: leverage
COOKS_D = "Cook's distance"  # role: cooks_d

# Data: replace this block with your own table, for example df = pd.read_csv("model_diagnostics.csv")
rng = np.random.default_rng(42)
n_obs = 120
x1 = rng.normal(50, 15, n_obs)
x2 = rng.normal(30, 10, n_obs)
y = 2.5 + 0.8 * x1 + 1.2 * x2 + rng.normal(0, np.abs(x1) * 0.12, n_obs)
design = np.column_stack([np.ones(n_obs), x1, x2])
coef = np.linalg.lstsq(design, y, rcond=None)[0]
resid = y - design @ coef
hat = np.einsum("ij,ji->i", design, np.linalg.solve(design.T @ design, design.T))
std_resid = resid / np.sqrt(np.sum(resid**2) / (n_obs - N_PARAMS) * (1 - hat))
df = pd.DataFrame(
    {
        FITTED: design @ coef,
        RESIDUALS: resid,
        STD_RESIDUALS: std_resid,
        LEVERAGE: hat,
        COOKS_D: std_resid**2 * hat / (N_PARAMS * (1 - hat)),
    }
)

# Plot
fitted = df[FITTED].to_numpy()
residuals = df[RESIDUALS].to_numpy()
std_res = df[STD_RESIDUALS].to_numpy()
leverage = df[LEVERAGE].to_numpy()
sqrt_abs_res = np.sqrt(np.abs(std_res))
n = len(df)

sorted_std_res = np.sort(std_res)
theoretical_q = stats.norm.ppf((np.arange(n) + 0.5) / n)
lowess_res = lowess(residuals, fitted, frac=0.4, return_sorted=True)
lowess_scale = lowess(sqrt_abs_res, fitted, frac=0.4, return_sorted=True)

# Most influential observations by Cook's distance, labeled with their observation index
influential = df[COOKS_D].nlargest(N_LABELED).index.tolist()

# Panels of 1600x850 under a 100 px figure title give the 3200x1800 canvas
W, H = 1600, 850
HEADER_H = 1800 - 2 * H

POINT = IMPRINT_PALETTE[0]
SMOOTH = IMPRINT_PALETTE[4]
REFERENCE = INK_MUTED


def make_style(colors, title_size=40):
    return Style(
        background=PAGE_BG,
        plot_background=PAGE_BG,
        foreground=INK,
        foreground_strong=INK,
        foreground_subtle=INK_MUTED,
        colors=tuple(colors),
        title_font_size=title_size,
        label_font_size=32,
        major_label_font_size=28,
        legend_font_size=26,
        value_font_size=30,
        value_colors=tuple([INK] * len(colors)),
        stroke_width=3.5,
    )


def line_xy(xs, ys):
    return [(float(a), float(b)) for a, b in zip(xs, ys, strict=True)]


def panel(title, x_title, y_title, xs, ys, lines, extra_labels=None):
    """One XY panel: all points, labeled influential points, then (name, points, color) lines."""
    colors = [POINT, POINT] + [c for _, _, c in lines]
    labels = {(round(float(xs[i]), 9), round(float(ys[i]), 9)): str(i) for i in influential}
    labels.update(extra_labels or {})
    chart = pygal.XY(
        style=make_style(colors),
        width=W,
        height=H,
        title=title,
        x_title=x_title,
        y_title=y_title,
        show_legend=False,
        print_values=True,
        print_values_position="top",
        formatter=lambda v: labels.get((round(float(v[0]), 9), round(float(v[1]), 9)), ""),
        stroke=False,
        dots_size=5,
        show_x_guides=False,
        show_y_guides=True,
        margin=20,
    )
    chart.add("Observations", line_xy(xs, ys))
    chart.add("Influential", line_xy(xs[influential], ys[influential]), dots_size=8)
    for name, pts, _ in lines:
        chart.add(name, pts, stroke=True, dots_size=0)
    return chart


# Panel 1: Residuals vs Fitted
chart1 = panel(
    "Residuals vs Fitted",
    FITTED,
    RESIDUALS,
    fitted,
    residuals,
    [
        ("Zero", line_xy([fitted.min(), fitted.max()], [0, 0]), REFERENCE),
        ("LOWESS", line_xy(lowess_res[:, 0], lowess_res[:, 1]), SMOOTH),
    ],
)

# Panel 2: Normal Q-Q (influential points sit at their sorted position)
ref_lo = float(min(theoretical_q.min(), sorted_std_res.min()))
ref_hi = float(max(theoretical_q.max(), sorted_std_res.max()))
rank = np.argsort(np.argsort(std_res))
chart2 = panel(
    "Normal Q-Q",
    "Theoretical Quantiles",
    STD_RESIDUALS,
    theoretical_q[rank],
    std_res,
    [("45° line", line_xy([ref_lo, ref_hi], [ref_lo, ref_hi]), REFERENCE)],
)

# Panel 3: Scale-Location
chart3 = panel(
    "Scale-Location",
    FITTED,
    "√|Standardized Residuals|",
    fitted,
    sqrt_abs_res,
    [("LOWESS", line_xy(lowess_scale[:, 0], lowess_scale[:, 1]), SMOOTH)],
)

# Panel 4: Residuals vs Leverage with Cook's distance contours (mirrored, one line per level)
h_grid = np.linspace(leverage.min() * 0.5, leverage.max() * 2.2, 300)
y_clip = np.abs(std_res).max() * 1.6
cook_colors = [IMPRINT_PALETTE[3], IMPRINT_PALETTE[2]]
contours = []
contour_labels = {}
for lvl, color in zip(COOK_LEVELS, cook_colors, strict=False):
    bound = np.sqrt(lvl * N_PARAMS * (1 - h_grid) / h_grid)
    keep = bound <= y_clip
    upper = line_xy(h_grid[keep], bound[keep])
    lower = line_xy(h_grid[keep][::-1], -bound[keep][::-1])
    if not upper:
        continue
    contours.append((f"Cook's D = {lvl:g}", upper, color))
    contours.append((f"Cook's D = {lvl:g} (lower)", lower, color))
    contour_labels[(round(upper[0][0], 9), round(upper[0][1], 9))] = f"Cook's D = {lvl:g}"
chart4 = panel("Residuals vs Leverage", LEVERAGE, STD_RESIDUALS, leverage, std_res, contours, contour_labels)

charts = [chart1, chart2, chart3, chart4]

# Figure title band, rendered by pygal so it shares the panel typeface
FIGURE_TITLE = "diagnostic-regression-panel · python · pygal · anyplot.ai"
header = pygal.XY(
    style=make_style([POINT], title_size=52),
    width=2 * W,
    height=HEADER_H,
    title=FIGURE_TITLE,
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    margin=0,
    margin_top=10,
    margin_bottom=0,
)
header.add("", [(0.0, 0.0)], dots_size=0)

# Interactive HTML: four SVGs in a 2x2 grid under the figure title
svg_parts = [c.render().decode("utf-8") for c in charts]
cells = "\n  ".join(f'<div class="cell">{svg}</div>' for svg in svg_parts)
html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{FIGURE_TITLE}</title>
<style>
  body {{ margin: 0; background: {PAGE_BG}; font-family: sans-serif; }}
  h1 {{ text-align: center; color: {INK}; font-size: 28px; margin: 20px 0 10px; font-weight: 500; }}
  .grid {{ display: grid; grid-template-columns: 50% 50%; width: 100%; }}
  .cell svg {{ width: 100%; height: auto; display: block; }}
</style>
</head>
<body>
<h1>{FIGURE_TITLE}</h1>
<div class="grid">
  {cells}
</div>
</body>
</html>"""
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html)


# Save PNG: nest the header and the four panel SVGs in one 3200x1800 SVG and rasterize it
def nested(chart, x, y, width, height):
    body = chart.render().decode("utf-8").split("?>", 1)[-1]
    return f'<svg x="{x}" y="{y}" width="{width}" height="{height}" viewBox="0 0 {width} {height}">{body}</svg>'


parts = [nested(header, 0, 0, 2 * W, HEADER_H)]
parts += [nested(c, (k % 2) * W, HEADER_H + (k // 2) * H, W, H) for k, c in enumerate(charts)]
composite = (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{2 * W}" height="1800" viewBox="0 0 {2 * W} 1800">'
    f'<rect width="100%" height="100%" fill="{PAGE_BG}"/>' + "".join(parts) + "</svg>"
)
cairosvg.svg2png(bytestring=composite.encode("utf-8"), write_to=f"plot-{THEME}.png")
