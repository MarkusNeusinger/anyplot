"""anyplot.ai
scatter-regression-linear: Scatter Plot with Linear Regression
Library: pygal 3.1.0 | Python 3.13.13
Quality: 82/100 | Updated: 2026-08-05
"""

import os

import numpy as np
import pygal
from pygal.style import Style
from scipy import stats


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"  # Imprint 'muted' anchor: confidence-band fill

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Data - advertising spend vs revenue
np.random.seed(42)
n_points = 90
x = np.random.uniform(5, 60, n_points)  # ad spend, $K
y = 35 + 4.6 * x + np.random.normal(0, 18, n_points)  # revenue, $K

# Linear regression + 95% confidence band
slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
r_squared = r_value**2

x_line = np.linspace(x.min(), x.max(), 100)
y_line = slope * x_line + intercept

n = len(x)
x_mean = x.mean()
residual_std = np.sqrt(np.sum((y - (slope * x + intercept)) ** 2) / (n - 2))
t_val = stats.t.ppf(0.975, n - 2)
se_line = residual_std * np.sqrt(1 / n + (x_line - x_mean) ** 2 / np.sum((x - x_mean) ** 2))
ci_upper = y_line + t_val * se_line
ci_lower = y_line - t_val * se_line

equation = f"y = {slope:.2f}x + {intercept:.1f}"

# pygal has no free-text annotation API, so the R² the spec asks to display
# "prominently" is surfaced in the title itself - the most prominent element
# pygal offers - and the fit equation is folded into the regression line's
# legend label.
title = (
    f"Advertising Spend vs. Revenue (R² = {r_squared:.3f}) · scatter-regression-linear · python · pygal · anyplot.ai"
)
# Scale the title font linearly off the 67-char mandated-title baseline so the
# longer descriptive prefix never overflows the canvas (see plot-generator.md).
title_font_size = round(66 * min(1.0, 67 / len(title)))

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(IMPRINT[0], INK_MUTED, IMPRINT[1]),
    title_font_size=title_font_size,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=38,
    dot_opacity=0.65,  # spec: scatter points at moderate transparency (~0.6-0.7)
    # pygal derives every line's rendered stroke-width from this single style
    # token (per-series `stroke_style={"width": ...}` only styles the series'
    # <g> wrapper, which the line path's own class overrides) - set it bold
    # enough that the regression line reads as clearly thicker than the dots.
    stroke_width=6,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title="Advertising Spend ($K)",
    y_title="Revenue ($K)",
    show_legend=True,
    legend_box_size=28,
    dots_size=14,
    stroke=False,
    show_x_guides=True,
    show_y_guides=True,
    truncate_legend=-1,
    margin_bottom=40,
)

# Scatter points
chart.add("Data Points", [{"value": (float(xi), float(yi))} for xi, yi in zip(x, y, strict=True)])

# 95% CI band - muted neutral fill, sits behind the regression line
ci_band = [(float(x_line[i]), float(ci_upper[i])) for i in range(0, len(x_line), 3)]
ci_band += [(float(x_line[i]), float(ci_lower[i])) for i in range(len(x_line) - 1, -1, -3)]
ci_band.append(ci_band[0])
chart.add("95% CI Band", ci_band, stroke=True, fill=True, show_dots=False)

# Regression line - solid stroke in a contrasting color, equation in the label
chart.add(
    f"Regression Line ({equation})",
    [(float(xi), float(yi)) for xi, yi in zip(x_line, y_line, strict=True)],
    stroke=True,
    show_dots=False,
)

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
