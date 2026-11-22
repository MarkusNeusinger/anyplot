"""anyplot.ai
pdp-basic: Partial Dependence Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-15
"""

import os

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_ribbon,
    geom_segment,
    ggplot,
    labs,
    theme,
    theme_minimal,
)
from sklearn.datasets import make_regression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.inspection import partial_dependence


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
CI_Z = 1.96  # band covers mean ± 1.96 standard deviations across the ICE curves

# Columns: set these to your table's column names
FEATURE = "Room Size (standardized)"  # role: feature_values
PD = "Partial Dependence (avg. prediction)"  # role: partial_dependence
CI_LOW = "Lower bound"  # role: confidence_interval
CI_HIGH = "Upper bound"  # role: extra
OBSERVED = "Observed room size"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("pdp.csv")
X, y = make_regression(n_samples=500, n_features=5, noise=10, random_state=42)
model = GradientBoostingRegressor(n_estimators=100, max_depth=3, random_state=42).fit(X, y)
room_size = 1  # column of X used as the feature
ice = partial_dependence(model, X, features=[room_size], kind="individual", grid_resolution=80)
ice_curves = ice["individual"][0]
grid = ice["grid_values"][0]
mean_curve = ice_curves.mean(axis=0)
spread = ice_curves.std(axis=0)
df = pd.DataFrame(
    {
        FEATURE: grid,
        PD: mean_curve,
        CI_LOW: mean_curve - CI_Z * spread,
        CI_HIGH: mean_curve + CI_Z * spread,
        OBSERVED: X[: len(grid), room_size],
    }
)

# Plot: reads only df and the constants above
rug_height = (df[CI_HIGH].max() - df[CI_LOW].min()) * 0.03
rug_floor = df[CI_LOW].min() - rug_height
rug = pd.DataFrame({OBSERVED: df[OBSERVED], "start": rug_floor, "end": df[CI_LOW].min()})

plot = (
    ggplot(df, aes(x=FEATURE, y=PD))
    + geom_ribbon(
        aes(ymin=CI_LOW, ymax=CI_HIGH), alpha=0.15, fill=IMPRINT_PALETTE[0], color=IMPRINT_PALETTE[0], size=0.25
    )
    + geom_line(color=IMPRINT_PALETTE[0], size=1.0)
    + geom_segment(
        data=rug,
        mapping=aes(x=OBSERVED, xend=OBSERVED, y="start", yend="end"),
        color=IMPRINT_PALETTE[1],
        alpha=0.6,
        size=0.4,
    )
    + labs(title="pdp-basic · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.15, alpha=0.10),
        panel_grid_minor=element_blank(),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.25),
        plot_title=element_text(size=12, weight="bold", color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.25),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
