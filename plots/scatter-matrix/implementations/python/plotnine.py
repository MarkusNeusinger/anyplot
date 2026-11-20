"""anyplot.ai
scatter-matrix: Scatter Plot Matrix
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-11-20
"""

import os

import numpy as np
import pandas as pd
from mizani.breaks import breaks_extended
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    facet_grid,
    geom_line,
    geom_point,
    geom_ribbon,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from scipy.stats import gaussian_kde


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
ALCOHOL = "Alcohol (% vol)"  # role: extra
MALIC = "Malic acid (g/L)"  # role: extra
FLAVANOIDS = "Flavanoids (mg/g)"  # role: extra
COLOR = "Color intensity"  # role: extra
CULTIVAR = "Cultivar"  # role: extra
VARIABLES = [ALCOHOL, MALIC, FLAVANOIDS, COLOR]  # role: variables

# Data: replace this block with your own table, for example df = pd.read_csv("wine.csv")
rng = np.random.default_rng(42)
cultivars = {
    # name: (alcohol, malic acid, flavanoids, color intensity) as (mean, sd) pairs
    "Barolo": ((13.7, 0.45), (2.0, 0.7), (2.98, 0.4), (5.5, 1.2)),
    "Grignolino": ((12.3, 0.5), (1.9, 1.0), (2.08, 0.7), (3.1, 0.9)),
    "Barbera": ((13.1, 0.5), (3.3, 1.1), (0.78, 0.3), (7.4, 2.3)),
}
frames = []
for name, params in cultivars.items():
    cols = {var: rng.normal(mean, sd, 60) for var, (mean, sd) in zip(VARIABLES, params, strict=True)}
    frames.append(pd.DataFrame({CULTIVAR: name, **cols}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
groups = df[CULTIVAR].unique().tolist()

# Long form: every ordered variable pair is one facet cell (row = y variable, column = x variable)
pairs = pd.concat(
    [
        pd.DataFrame({"x": df[vx], "y": df[vy], "var_x": vx, "var_y": vy, CULTIVAR: df[CULTIVAR]})
        for vy in VARIABLES
        for vx in VARIABLES
        if vx != vy
    ],
    ignore_index=True,
)

# Diagonal: one KDE per variable and group, drawn in the cell's y range
curves = []
for var in VARIABLES:
    grid = np.linspace(df[var].min(), df[var].max(), 200)
    lo, span = df[var].min(), df[var].max() - df[var].min()
    dens = {g: gaussian_kde(df.loc[df[CULTIVAR] == g, var].dropna())(grid) for g in groups}
    peak = max(d.max() for d in dens.values())
    for g, d in dens.items():
        curves.append(
            pd.DataFrame(
                {"x": grid, "y": lo + span * 0.9 * d / peak, "base": lo, "var_x": var, "var_y": var, CULTIVAR: g}
            )
        )
diag = pd.concat(curves, ignore_index=True)

for frame in (pairs, diag):
    frame["var_x"] = pd.Categorical(frame["var_x"], categories=VARIABLES, ordered=True)
    frame["var_y"] = pd.Categorical(frame["var_y"], categories=VARIABLES, ordered=True)
    frame[CULTIVAR] = pd.Categorical(frame[CULTIVAR], categories=groups, ordered=True)

anyplot_theme = theme(
    figure_size=(6, 6),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.2, alpha=0.10),
    panel_grid_minor=element_blank(),
    panel_border=element_rect(color=INK_SOFT, fill=None, size=0.4),
    axis_title=element_blank(),
    axis_text=element_text(size=7, color=INK_SOFT),
    axis_ticks=element_line(color=INK_SOFT, size=0.3),
    plot_title=element_text(size=11, weight="bold", ha="center", color=INK),
    strip_text_x=element_text(size=8, weight="bold", color=INK),
    strip_text_y=element_text(size=8, weight="bold", angle=0, color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.4),
    legend_key=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
    legend_text=element_text(size=8, color=INK_SOFT),
    legend_title=element_text(size=9, color=INK),
    legend_position="bottom",
    panel_spacing=0.06,
)

plot = (
    ggplot(pairs, aes(x="x", y="y", color=CULTIVAR, fill=CULTIVAR))
    + geom_point(size=0.9, alpha=0.6, stroke=0)
    + geom_ribbon(aes(x="x", ymin="base", ymax="y"), data=diag, alpha=0.35, size=0)
    + geom_line(aes(x="x", y="y"), data=diag, size=0.5)
    + facet_grid("var_y ~ var_x", scales="free")
    + scale_x_continuous(breaks=breaks_extended(n=3))
    + scale_y_continuous(breaks=breaks_extended(n=3))
    + scale_color_manual(values=IMPRINT_PALETTE, limits=groups)
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=groups)
    + labs(title="scatter-matrix · python · plotnine · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in", verbose=False)
