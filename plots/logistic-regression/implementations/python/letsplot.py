""" anyplot.ai
logistic-regression: Logistic Regression Curve Plot
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-22
"""

import os
import shutil

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_line,
    geom_point,
    geom_ribbon,
    ggplot,
    ggsize,
    labs,
    scale_color_manual,
    scale_y_continuous,
    theme,
)
from lets_plot.export import ggsave
from sklearn.linear_model import LogisticRegression


LetsPlot.setup_html()

# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
# element_line has no alpha argument; lets-plot reads the alpha from an rgba() color
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
THRESHOLD = 0.5  # default decision threshold of a binary classifier
JITTER_SD = 0.03  # vertical jitter of the 0/1 outcomes, in probability units
Z_95 = 1.96  # two-sided 95 % normal quantile

# Columns: set these to your table's column names
STUDY_HOURS = "Study hours"  # role: x
OUTCOME = "Outcome (0 = fail, 1 = pass)"  # role: y
PROBABILITY = "Probability"  # role: probability
CI_LOWER = "CI lower"  # role: ci_lower
CI_UPPER = "CI upper"  # role: ci_upper
CLASS = "Class"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("exam.csv")
np.random.seed(42)
n_samples = 200
hours = np.random.uniform(0, 10, n_samples)
true_prob = 1 / (1 + np.exp(-1.5 * (hours - 5)))
passed = (np.random.random(n_samples) < true_prob).astype(int)
df = pd.DataFrame({STUDY_HOURS: hours, OUTCOME: passed})

# Plot: reads only df and the constants above
observed = df.dropna(subset=[STUDY_HOURS, OUTCOME])
X = observed[[STUDY_HOURS]].to_numpy(dtype=float)
y = observed[OUTCOME].to_numpy(dtype=int)
model = LogisticRegression().fit(X, y)
coef = model.coef_[0][0]
accuracy = model.score(X, y)

# Fitted curve with an approximate 95 % band, on a grid over the observed range
grid = np.linspace(df[STUDY_HOURS].min(), df[STUDY_HOURS].max(), 200)
prob = model.predict_proba(grid.reshape(-1, 1))[:, 1]
se = np.sqrt(prob * (1 - prob) / len(observed)) * 2
curve = pd.DataFrame(
    {
        STUDY_HOURS: grid,
        PROBABILITY: prob,
        CI_LOWER: np.clip(prob - Z_95 * se, 0, 1),
        CI_UPPER: np.clip(prob + Z_95 * se, 0, 1),
    }
)

# Observations: outcomes jittered along y only
rng = np.random.default_rng(7)
points = pd.DataFrame(
    {
        STUDY_HOURS: observed[STUDY_HOURS].to_numpy(),
        PROBABILITY: y + rng.normal(0, JITTER_SD, len(observed)),
        CLASS: np.where(y == 1, "Pass", "Fail"),
    }
)

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=GRID, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=14),
    axis_text=element_text(color=INK_SOFT, size=12),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(color=INK, size=16),
    plot_subtitle=element_text(color=INK_SOFT, size=12),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=12),
    legend_title=element_text(color=INK, size=13),
)

plot = (
    ggplot()
    + geom_ribbon(
        aes(x=STUDY_HOURS, ymin=CI_LOWER, ymax=CI_UPPER), data=curve, fill=IMPRINT_PALETTE[0], alpha=0.18, size=0
    )
    + geom_hline(yintercept=THRESHOLD, linetype="dashed", color=INK_SOFT, size=0.6, alpha=0.7)
    + geom_point(aes(x=STUDY_HOURS, y=PROBABILITY, color=CLASS), data=points, size=3, alpha=0.6)
    + geom_line(aes(x=STUDY_HOURS, y=PROBABILITY), data=curve, color=IMPRINT_PALETTE[0], size=1.5)
    + scale_color_manual(values=[IMPRINT_PALETTE[1], IMPRINT_PALETTE[0]], breaks=["Fail", "Pass"])
    + scale_y_continuous(limits=[-0.1, 1.1])
    + labs(
        x=STUDY_HOURS,
        y=PROBABILITY,
        title="logistic-regression · python · letsplot · anyplot.ai",
        subtitle=f"Coefficient: {coef:.2f} | Accuracy: {accuracy:.1%}",
    )
    + anyplot_theme
    + ggsize(800, 450)
)

# Save as PNG and HTML with theme suffix
ggsave(plot, f"plot-{THEME}.png", scale=4)
ggsave(plot, f"plot-{THEME}.html")

# Move files from lets-plot-images subfolder to current directory
if os.path.exists("lets-plot-images"):
    for filename in [f"plot-{THEME}.png", f"plot-{THEME}.html"]:
        src = os.path.join("lets-plot-images", filename)
        if os.path.exists(src):
            shutil.move(src, filename)
