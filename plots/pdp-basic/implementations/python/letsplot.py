""" anyplot.ai
pdp-basic: Partial Dependence Plot
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 78/100 | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *
from sklearn.datasets import make_regression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.inspection import partial_dependence


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "#DDDACF" if THEME == "light" else "#34342F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BAND_LOW, BAND_HIGH = 0.10, 0.90  # the uncertainty band spans the 10th to the 90th percentile of the ICE curves
PD_NAME = "Partial dependence (average)"
RUG_NAME = "Observed values"

# Columns: set these to your table's column names
FEATURE = "Temperature (standardized)"  # role: feature_values
OBSERVED = "Observed temperature (standardized)"  # role: extra
OBSERVATION = "Observation"  # role: extra
ICE = "Predicted outcome"  # role: ice_curves
PARTIAL_DEPENDENCE = "Partial dependence (predicted outcome)"  # role: partial_dependence

# Data: replace this block with your own table, one row per observation and grid value,
# for example df = pd.read_csv("ice_curves.csv")
X, y = make_regression(n_samples=500, n_features=5, noise=20, random_state=42)
model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
model.fit(X, y)

rng = np.random.default_rng(42)
sample = rng.choice(len(X), size=100, replace=False)
pdp_result = partial_dependence(model, X[sample], features=[0], kind="both", grid_resolution=80)
grid = pdp_result["grid_values"][0]
ice_curves = pdp_result["individual"][0]

df = pd.DataFrame(
    {
        OBSERVATION: np.repeat(np.arange(len(sample)), len(grid)),
        FEATURE: np.tile(grid, len(sample)),
        ICE: ice_curves.ravel(),
        OBSERVED: np.repeat(X[sample, 0], len(grid)),
    }
)

# Plot: reads only df and the constants above
by_feature = df.groupby(FEATURE, sort=True)[ICE]
curve = pd.DataFrame(
    {
        PARTIAL_DEPENDENCE: by_feature.mean(),
        "lower": by_feature.quantile(BAND_LOW),
        "upper": by_feature.quantile(BAND_HIGH),
    }
).reset_index()

# Rug: short ticks along the bottom edge at the observed feature values
rug = df.drop_duplicates(OBSERVATION)[[OBSERVED]].copy()
low = df[ICE].min()
rug_height = (df[ICE].max() - low) * 0.04
rug["y_start"] = low
rug["y_end"] = low + rug_height

band_name = f"{int(BAND_LOW * 100)}-{int(BAND_HIGH * 100)}th percentile band"
curve["Band"] = band_name
curve["Element"] = PD_NAME
rug["Element"] = RUG_NAME

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=GRID, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT, size=0.3),
    plot_title=element_text(color=INK, size=16, face="bold"),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=INK, size=10),
    legend_position="top",
    legend_direction="horizontal",
)

plot = (
    ggplot()
    + geom_ribbon(aes(x=FEATURE, ymin="lower", ymax="upper", fill="Band"), data=curve, alpha=0.3, size=0)
    + geom_line(aes(x=FEATURE, y=PARTIAL_DEPENDENCE, color="Element"), data=curve, size=1.6)
    + geom_segment(
        aes(x=OBSERVED, y="y_start", xend=OBSERVED, yend="y_end", color="Element"), data=rug, alpha=0.7, size=0.5
    )
    + scale_color_manual(values={PD_NAME: IMPRINT_PALETTE[0], RUG_NAME: INK_SOFT}, name="")
    + scale_fill_manual(values={band_name: IMPRINT_PALETTE[1]}, name="")
    + labs(x=FEATURE, y=PARTIAL_DEPENDENCE, title="pdp-basic · python · letsplot · anyplot.ai")
    + anyplot_theme
    + ggsize(800, 450)
)

ggsave(plot, f"plot-{THEME}.png", scale=4, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
