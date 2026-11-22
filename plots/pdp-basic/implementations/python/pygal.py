"""anyplot.ai
pdp-basic: Partial Dependence Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-15
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style
from sklearn.datasets import make_regression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.inspection import partial_dependence


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
CI_Z = 1.96  # 95 % interval
RUG_SIZE = 40  # observed training values shown as rug

# Columns: set these to your table's column names
FEATURE = "Feature value (standardized)"  # role: feature_values
PD = "Partial dependence"  # role: partial_dependence
CI_LOWER = "95% CI lower"  # role: confidence_interval
CI_UPPER = "95% CI upper"  # role: extra
OBSERVED = "Observed feature value"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("pdp.csv")
np.random.seed(42)
X, y = make_regression(n_samples=500, n_features=5, noise=10, random_state=42)
model = GradientBoostingRegressor(n_estimators=50, max_depth=3, random_state=42)
model.fit(X, y)
average = partial_dependence(model, X, features=[0], kind="average", grid_resolution=100)
individual = partial_dependence(model, X, features=[0], kind="individual", grid_resolution=100)
pd_values = average["average"][0]
spread = np.std(individual["individual"][0], axis=0) / np.sqrt(len(X))
rug_values = np.sort(X[np.random.choice(len(X), size=RUG_SIZE, replace=False), 0])
df = pd.DataFrame(
    {
        FEATURE: average["grid_values"][0],
        PD: pd_values,
        CI_LOWER: pd_values - CI_Z * spread,
        CI_UPPER: pd_values + CI_Z * spread,
        OBSERVED: np.pad(rug_values, (0, len(pd_values) - len(rug_values)), constant_values=np.nan),
    }
)

# Plot
title = "pdp-basic · python · pygal · anyplot.ai"
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=6,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title=FEATURE,
    y_title=PD,
    show_legend=True,
    legend_at_bottom=True,
    show_dots=True,
    show_x_guides=True,
    show_y_guides=True,
    margin_bottom=60,
)

grid = df[[FEATURE, PD, CI_LOWER, CI_UPPER]].dropna()
chart.add(PD, list(zip(grid[FEATURE], grid[PD], strict=True)), stroke_style={"width": 8}, show_dots=False)
chart.add(
    CI_UPPER,
    list(zip(grid[FEATURE], grid[CI_UPPER], strict=True)),
    stroke_style={"width": 3, "dasharray": "14,8"},
    show_dots=False,
)
chart.add(
    CI_LOWER,
    list(zip(grid[FEATURE], grid[CI_LOWER], strict=True)),
    stroke_style={"width": 3, "dasharray": "14,8"},
    show_dots=False,
)

# Rug: observed training values, placed just below the lowest curve
rug_x = df[OBSERVED].dropna()
rug_y = grid[CI_LOWER].min() - 0.08 * (grid[CI_UPPER].max() - grid[CI_LOWER].min())
chart.add("Training data (rug)", [(x, rug_y) for x in rug_x], stroke=False, dots_size=7)

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
