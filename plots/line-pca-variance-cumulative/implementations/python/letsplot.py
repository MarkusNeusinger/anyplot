""" anyplot.ai
line-pca-variance-cumulative: Cumulative Explained Variance for PCA Component Selection
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-29
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *
from sklearn.datasets import load_wine
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


LetsPlot.setup_html()

# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "#D8D7D0" if THEME == "light" else "#303030"

BRAND = "#009E73"  # Imprint position 1 — cumulative line (first series)
ANYPLOT_AMBER = "#DDCC77"  # semantic anchor — caution, 90% threshold
MATTE_RED = "#AE3030"  # Imprint position 5 — alert, 95% threshold

# Data — PCA on Wine dataset (13 chemical features)
wine = load_wine()
X = StandardScaler().fit_transform(wine.data)
pca = PCA()
pca.fit(X)

n_components = np.arange(1, len(pca.explained_variance_ratio_) + 1)
individual_var = pca.explained_variance_ratio_ * 100
cumulative_var = np.cumsum(individual_var)

df_cumulative = pd.DataFrame(
    {"Component": n_components, "Cumulative": np.round(cumulative_var, 2), "Individual": np.round(individual_var, 2)}
)
df_individual = pd.DataFrame({"Component": n_components, "Individual": np.round(individual_var, 2)})

# Thresholds and component crossings
threshold_90, threshold_95 = 90.0, 95.0
comp_90 = int(n_components[cumulative_var >= threshold_90][0])
comp_95 = int(n_components[cumulative_var >= threshold_95][0])

# Elbow: component with max perpendicular distance from start→end chord
c1, v1 = 1, cumulative_var[0]
cn, vn = int(n_components[-1]), cumulative_var[-1]
dx, dy = cn - c1, vn - v1
perp_dist = abs(dy * n_components - dx * cumulative_var + cn * v1 - vn * c1) / np.sqrt(dx**2 + dy**2)
elbow_comp = int(n_components[np.argmax(perp_dist)])
elbow_cum = float(cumulative_var[elbow_comp - 1])

df_elbow = pd.DataFrame({"Component": [elbow_comp], "Cumulative": [elbow_cum], "label": [f"PC {elbow_comp}"]})

title = "line-pca-variance-cumulative · python · letsplot · anyplot.ai"

anyplot_chrome = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_x=element_blank(),
    panel_grid_minor=element_blank(),
    panel_grid_major_y=element_line(color=GRID, size=0.4),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=16),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=INK),
)

plot = (
    ggplot()
    # Secondary: individual variance bars (muted, behind the cumulative line)
    + geom_bar(
        data=df_individual,
        mapping=aes(x="Component", y="Individual"),
        stat="identity",
        fill=INK_MUTED,
        alpha=0.28,
        width=0.65,
    )
    # Threshold reference lines
    + geom_hline(yintercept=threshold_90, linetype="dashed", color=ANYPLOT_AMBER, size=1.0)
    + geom_hline(yintercept=threshold_95, linetype="dashed", color=MATTE_RED, size=1.0)
    + geom_vline(xintercept=comp_90, linetype="dotted", color=ANYPLOT_AMBER, size=0.8, alpha=0.65)
    + geom_vline(xintercept=comp_95, linetype="dotted", color=MATTE_RED, size=0.8, alpha=0.65)
    # Threshold labels (right-aligned near edge)
    + geom_text(
        data=pd.DataFrame({"x": [12.8], "y": [threshold_90 + 2.0], "label": ["90%"]}),
        mapping=aes(x="x", y="y", label="label"),
        color=ANYPLOT_AMBER,
        size=4,
        hjust=1,
    )
    + geom_text(
        data=pd.DataFrame({"x": [12.8], "y": [threshold_95 + 2.0], "label": ["95%"]}),
        mapping=aes(x="x", y="y", label="label"),
        color=MATTE_RED,
        size=4,
        hjust=1,
    )
    # Primary: cumulative variance line (Imprint brand green, first series)
    + geom_line(data=df_cumulative, mapping=aes(x="Component", y="Cumulative"), size=2.0, color=BRAND)
    # Points with lets-plot native tooltips (hover shows both cumulative and individual)
    + geom_point(
        data=df_cumulative,
        mapping=aes(x="Component", y="Cumulative"),
        size=5,
        color=BRAND,
        alpha=0.9,
        tooltips=layer_tooltips()
        .line("PC @Component")
        .line("Cumulative: @Cumulative%")
        .line("Individual: @Individual%"),
    )
    # Elbow annotation: hollow ring marker + label (spec: annotate elbow if detectable)
    + geom_point(
        data=df_elbow, mapping=aes(x="Component", y="Cumulative"), size=9, shape=21, color=INK, fill=ELEVATED_BG
    )
    + geom_text(
        data=df_elbow, mapping=aes(x="Component", y="Cumulative", label="label"), color=INK_SOFT, size=4, hjust=-0.25
    )
    + scale_x_continuous(breaks=list(n_components))
    + scale_y_continuous(breaks=list(range(0, 101, 10)), limits=[0, 106])
    + labs(title=title, x="Number of Principal Components", y="Explained Variance (%)")
    + theme_minimal()
    + anyplot_chrome
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
