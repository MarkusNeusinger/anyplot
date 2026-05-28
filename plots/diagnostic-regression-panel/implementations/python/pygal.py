""" anyplot.ai
diagnostic-regression-panel: Regression Diagnostic Panel (Four-Plot Display)
Library: pygal 3.1.0 | Python 3.13.13
Quality: 80/100 | Created: 2026-05-13
"""

import os
import sys


# Remove this script's directory from sys.path so "pygal" resolves to the installed package
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _this_dir]

import io

import cairosvg
import numpy as np
import pygal
from PIL import Image
from pygal.style import Style
from scipy import stats
from statsmodels.nonparametric.smoothers_lowess import lowess


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Data — two-predictor regression with mild heteroscedasticity
np.random.seed(42)
n = 120
x1 = np.random.normal(50, 15, n)
x2 = np.random.normal(30, 10, n)
noise = np.random.normal(0, np.abs(x1) * 0.12, n)
y = 2.5 + 0.8 * x1 + 1.2 * x2 + noise

X_mat = np.column_stack([np.ones(n), x1, x2])
beta = np.linalg.lstsq(X_mat, y, rcond=None)[0]
fitted = X_mat @ beta
residuals = y - fitted

H_hat = X_mat @ np.linalg.inv(X_mat.T @ X_mat) @ X_mat.T
leverage = np.diag(H_hat)
p_params = 3
mse = np.sum(residuals**2) / (n - p_params)
std_residuals = residuals / np.sqrt(mse * (1 - leverage))
sqrt_abs_std_res = np.sqrt(np.abs(std_residuals))
cooks_d = (std_residuals**2 * leverage) / (p_params * (1 - leverage))

# Q-Q theoretical quantiles
sorted_std_res = np.sort(std_residuals)
probs = np.linspace(0.5 / n, 1 - 0.5 / n, n)
theoretical_q = stats.norm.ppf(probs)

# LOWESS smoothers
lowess_res_fit = lowess(residuals, fitted, frac=0.4, return_sorted=True)
lowess_scale = lowess(sqrt_abs_std_res, fitted, frac=0.4, return_sorted=True)

# Cook's distance contour prep
h_range = np.linspace(1e-4, float(np.max(leverage)) * 1.3, 400)
y_clip = float(np.max(np.abs(std_residuals))) * 1.4
cook_levels = [0.5, 1.0]


def make_style():
    return Style(
        background=PAGE_BG,
        plot_background=PAGE_BG,
        foreground=INK,
        foreground_strong=INK,
        foreground_subtle=INK_MUTED,
        colors=IMPRINT,
        title_font_size=26,
        label_font_size=18,
        major_label_font_size=16,
        legend_font_size=14,
        value_font_size=12,
        stroke_width=2.5,
    )


W, H_SUB = 2400, 1350

# Chart 1: Residuals vs Fitted
chart1 = pygal.XY(
    style=make_style(),
    width=W,
    height=H_SUB,
    title="Residuals vs Fitted",
    x_title="Fitted values",
    y_title="Residuals",
    show_legend=False,
    dots_size=2.5,
    stroke=False,
)
chart1.add("Residuals", [(float(f), float(r)) for f, r in zip(fitted, residuals, strict=True)])
chart1.add("Zero", [(float(fitted.min()), 0.0), (float(fitted.max()), 0.0)], stroke=True, dots_size=0)
chart1.add("LOWESS", [(float(row[0]), float(row[1])) for row in lowess_res_fit], stroke=True, dots_size=0)

# Chart 2: Normal Q-Q
chart2 = pygal.XY(
    style=make_style(),
    width=W,
    height=H_SUB,
    title="Normal Q-Q",
    x_title="Theoretical Quantiles",
    y_title="Standardized Residuals",
    show_legend=False,
    dots_size=2.5,
    stroke=False,
)
chart2.add("Q-Q", [(float(t), float(s)) for t, s in zip(theoretical_q, sorted_std_res, strict=True)])
ref_lo = float(min(theoretical_q.min(), sorted_std_res.min()))
ref_hi = float(max(theoretical_q.max(), sorted_std_res.max()))
chart2.add("45° line", [(ref_lo, ref_lo), (ref_hi, ref_hi)], stroke=True, dots_size=0)

# Chart 3: Scale-Location
chart3 = pygal.XY(
    style=make_style(),
    width=W,
    height=H_SUB,
    title="Scale-Location",
    x_title="Fitted values",
    y_title="√|Standardized Residuals|",
    show_legend=False,
    dots_size=2.5,
    stroke=False,
)
chart3.add("Scale-Loc", [(float(f), float(s)) for f, s in zip(fitted, sqrt_abs_std_res, strict=True)])
chart3.add("LOWESS", [(float(row[0]), float(row[1])) for row in lowess_scale], stroke=True, dots_size=0)

# Chart 4: Residuals vs Leverage
chart4 = pygal.XY(
    style=make_style(),
    width=W,
    height=H_SUB,
    title="Residuals vs Leverage",
    x_title="Leverage",
    y_title="Standardized Residuals",
    show_legend=False,
    dots_size=2.5,
    stroke=False,
)
chart4.add("Residuals", [(float(lv), float(sr)) for lv, sr in zip(leverage, std_residuals, strict=True)])
for lvl in cook_levels:
    upper = [
        (float(h), float(np.sqrt(lvl * p_params * (1 - h) / h)))
        for h in h_range
        if np.sqrt(lvl * p_params * (1 - h) / h) <= y_clip
    ]
    lower = [
        (float(h), -float(np.sqrt(lvl * p_params * (1 - h) / h)))
        for h in h_range
        if np.sqrt(lvl * p_params * (1 - h) / h) <= y_clip
    ]
    if upper:
        chart4.add(f"Cook {lvl}+", upper, stroke=True, dots_size=0)
    if lower:
        chart4.add(f"Cook {lvl}-", lower, stroke=True, dots_size=0)

# Save HTML — four SVGs in a 2x2 grid
charts = [chart1, chart2, chart3, chart4]
svg_parts = []
for c in charts:
    raw = c.render()
    svg_parts.append(raw.decode("utf-8") if isinstance(raw, bytes) else raw)

html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>diagnostic-regression-panel · pygal · anyplot.ai</title>
<style>
  body {{ margin: 0; background: {PAGE_BG}; font-family: sans-serif; }}
  h1 {{ text-align: center; color: {INK}; font-size: 28px; margin: 20px 0 10px; font-weight: 500; }}
  .grid {{ display: grid; grid-template-columns: 50% 50%; width: 100%; }}
  .cell svg {{ width: 100%; height: auto; display: block; }}
</style>
</head>
<body>
<h1>diagnostic-regression-panel · pygal · anyplot.ai</h1>
<div class="grid">
  <div class="cell">{svg_parts[0]}</div>
  <div class="cell">{svg_parts[1]}</div>
  <div class="cell">{svg_parts[2]}</div>
  <div class="cell">{svg_parts[3]}</div>
</div>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html)


# Save PNG — render each chart and combine into 2x2 grid
def chart_to_pil(chart):
    svg_bytes = chart.render()
    png_bytes = cairosvg.svg2png(bytestring=svg_bytes, output_width=W, output_height=H_SUB)
    return Image.open(io.BytesIO(png_bytes)).convert("RGB")


imgs = [chart_to_pil(c) for c in charts]
combined = Image.new("RGB", (W * 2, H_SUB * 2))
combined.paste(imgs[0], (0, 0))
combined.paste(imgs[1], (W, 0))
combined.paste(imgs[2], (0, H_SUB))
combined.paste(imgs[3], (W, H_SUB))
combined.save(f"plot-{THEME}.png")
