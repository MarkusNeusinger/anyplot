"""anyplot.ai
logistic-regression: Logistic Regression Curve Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-18
"""

import os

import numpy as np
import pandas as pd
import statsmodels.api as sm
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_line,
    geom_point,
    geom_ribbon,
    ggplot,
    labs,
    position_jitter,
    scale_color_manual,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
THRESHOLD = 0.5  # default decision threshold of a logistic classifier
CI_ALPHA = 0.05  # 95% confidence band

# Columns: set these to your table's column names
HOURS = "Monthly usage (hours)"  # role: x
RENEWED = "Renewed (0/1)"  # role: y
PROBABILITY = "Predicted probability"  # role: probability
CI_LOWER = "Lower 95% bound"  # role: ci_lower
CI_UPPER = "Upper 95% bound"  # role: ci_upper

# Data: replace this block with your own table, for example df = pd.read_csv("subscriptions.csv")
rng = np.random.default_rng(42)
np.random.seed(42)  # plotnine jitter draws from the global generator
usage = np.clip(rng.gamma(shape=4.0, scale=3.2, size=180), 0.5, None)
p_renew = 1 / (1 + np.exp(-0.2 * (usage - 11)))
df = pd.DataFrame({HOURS: usage.round(1), RENEWED: rng.binomial(1, p_renew)})

# Plot: reads only df and the constants above
observed = df.dropna(subset=[HOURS, RENEWED])
observed = observed.assign(_hit=(observed[RENEWED] > observed[RENEWED].min()).astype(int))
model = sm.Logit(observed["_hit"], sm.add_constant(observed[HOURS])).fit(disp=0)

x_curve = np.linspace(df[HOURS].min(), df[HOURS].max(), 200)
prediction = model.get_prediction(sm.add_constant(x_curve, has_constant="add"))
interval = np.clip(prediction.conf_int(alpha=CI_ALPHA), 0, 1)
curve = pd.DataFrame(
    {HOURS: x_curve, PROBABILITY: prediction.predicted, CI_LOWER: interval[:, 0], CI_UPPER: interval[:, 1]}
)

# Class labels in descending outcome order, so the first class gets palette position 1
OUTCOME = "Outcome"
labels = {1: "Renewed", 0: "Not renewed"}
points = observed.copy()
points[OUTCOME] = points["_hit"].map(labels)
classes = [labels[v] for v in sorted(points["_hit"].unique(), reverse=True)]
curve_color = IMPRINT_PALETTE[len(classes)]

anyplot_theme = theme(
    figure_size=(8, 4.5),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    axis_title=element_text(size=10, color=INK),
    axis_text=element_text(size=8, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(size=12, color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color="none"),
    legend_key=element_rect(fill=ELEVATED_BG, color="none"),
    legend_text=element_text(size=8, color=INK_SOFT),
    legend_title=element_text(size=9, color=INK),
)

plot = (
    ggplot()
    + geom_ribbon(data=curve, mapping=aes(x=HOURS, ymin=CI_LOWER, ymax=CI_UPPER), alpha=0.25, fill=curve_color)
    + geom_line(data=curve, mapping=aes(x=HOURS, y=PROBABILITY), color=curve_color, size=1.2)
    + geom_hline(yintercept=THRESHOLD, linetype="dashed", color=INK_SOFT, size=0.6, alpha=0.7)
    + geom_point(
        data=points,
        mapping=aes(x=HOURS, y="_hit", color=OUTCOME),
        size=2.5,
        alpha=0.6,
        position=position_jitter(width=0, height=0.03),
    )
    + scale_color_manual(values=IMPRINT_PALETTE, limits=classes)
    + scale_y_continuous(limits=(-0.08, 1.08), breaks=[0, 0.25, 0.5, 0.75, 1])
    + labs(title="logistic-regression · python · plotnine · anyplot.ai", y="Probability of renewal")
    + theme_minimal()
    + anyplot_theme
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
