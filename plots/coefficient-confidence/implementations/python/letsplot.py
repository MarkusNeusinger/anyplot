""" anyplot.ai
coefficient-confidence: Coefficient Plot with Confidence Intervals
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-22
"""

import os

import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
NEUTRAL = "#1A1A1A" if THEME == "light" else "#E8E8E0"  # non-significant

# Constants
SIG_LABEL = "Significant (CI excludes 0)"
NOT_SIG_LABEL = "Not significant"

# Columns: set these to your table's column names
VARIABLE = "Predictor variable"  # role: variable
COEFFICIENT = "Coefficient estimate"  # role: coefficient
CI_LOWER = "CI lower (95%)"  # role: ci_lower
CI_UPPER = "CI upper (95%)"  # role: ci_upper
SIGNIFICANT = "Significant"  # role: significant

# Data: replace this block with your own table, for example df = pd.read_csv("coefficients.csv")
variables = [
    "Square Footage",
    "Number of Bedrooms",
    "Number of Bathrooms",
    "Lot Size (acres)",
    "Age of Home (years)",
    "Distance to Downtown",
    "School District Rating",
    "Garage Spaces",
    "Has Pool",
    "Has Fireplace",
    "Renovated Recently",
    "Crime Rate Index",
]
coefficients = [0.45, 0.12, 0.28, 0.18, -0.15, -0.22, 0.35, 0.08, 0.14, 0.05, 0.20, -0.32]
std_errors = [0.08, 0.09, 0.07, 0.06, 0.04, 0.05, 0.06, 0.07, 0.10, 0.08, 0.09, 0.07]

df = pd.DataFrame({VARIABLE: variables, COEFFICIENT: coefficients})
df[CI_LOWER] = df[COEFFICIENT] - 1.96 * pd.Series(std_errors)
df[CI_UPPER] = df[COEFFICIENT] + 1.96 * pd.Series(std_errors)
df[SIGNIFICANT] = (df[CI_LOWER] > 0) | (df[CI_UPPER] < 0)

# Plot: reads only df and the constants above
table = df.sort_values(COEFFICIENT, ascending=True).reset_index(drop=True)
table[VARIABLE] = pd.Categorical(table[VARIABLE], categories=table[VARIABLE].tolist(), ordered=True)
table["Significance"] = pd.Categorical(
    table[SIGNIFICANT].map({True: SIG_LABEL, False: NOT_SIG_LABEL}), categories=[SIG_LABEL, NOT_SIG_LABEL], ordered=True
)

plot = (
    ggplot(table, aes(x=VARIABLE, y=COEFFICIENT))
    # Vertical reference line at zero (null hypothesis), drawn before the points
    + geom_hline(yintercept=0, color=INK, size=0.9, linetype="dashed")
    # Point range: estimate with its confidence interval
    + geom_pointrange(aes(ymin=CI_LOWER, ymax=CI_UPPER, color="Significance"), size=1.2, fatten=3.5)
    + coord_flip()
    + scale_color_manual(values=[IMPRINT_PALETTE[0], NEUTRAL], name="")
    + labs(y=COEFFICIENT, x=VARIABLE, title="coefficient-confidence · python · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_x=element_line(color=GRID, size=0.3),
        panel_grid_minor_x=element_blank(),
        panel_grid_major_y=element_blank(),
        panel_grid_minor_y=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=16, face="bold", color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="bottom",
    )
    + ggsize(800, 450)
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
