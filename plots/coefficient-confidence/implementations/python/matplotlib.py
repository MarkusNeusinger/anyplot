""" anyplot.ai
coefficient-confidence: Coefficient Plot with Confidence Intervals
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: brand green marks significant coefficients; the muted anchor marks the rest
BRAND = "#009E73"
ANYPLOT_MUTED = INK_MUTED

# Columns: set these to your table's column names
VARIABLE = "Predictor"  # role: variable
COEFFICIENT = "Coefficient Estimate (Standardized)"  # role: coefficient
CI_LOWER = "95% CI lower"  # role: ci_lower
CI_UPPER = "95% CI upper"  # role: ci_upper
SIGNIFICANT = "Significant"  # role: significant

# Data: replace this block with your own table, for example df = pd.read_csv("coefficients.csv")
variables = [
    "Square Footage",
    "Number of Bedrooms",
    "Number of Bathrooms",
    "Lot Size (acres)",
    "Year Built",
    "Distance to City Center",
    "School Rating",
    "Crime Rate Index",
    "Garage Spaces",
    "Has Pool",
]
coefficients = np.array([0.45, 0.12, 0.28, 0.18, 0.08, -0.32, 0.25, -0.15, 0.10, 0.05])
std_errors = np.array([0.08, 0.09, 0.07, 0.06, 0.05, 0.10, 0.06, 0.08, 0.07, 0.04])
ci_lower = coefficients - 1.96 * std_errors
ci_upper = coefficients + 1.96 * std_errors
df = pd.DataFrame(
    {
        VARIABLE: variables,
        COEFFICIENT: coefficients,
        CI_LOWER: ci_lower,
        CI_UPPER: ci_upper,
        SIGNIFICANT: (ci_lower > 0) | (ci_upper < 0),
    }
)

# Plot: reads only df and the constants above
table = df.sort_values(COEFFICIENT).reset_index(drop=True)
excludes_zero = (table[CI_LOWER] > 0) | (table[CI_UPPER] < 0)
significant = table[SIGNIFICANT].astype("boolean").fillna(excludes_zero).astype(bool)
y_pos = np.arange(len(table))

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Vertical reference line at zero: solid neutral ink, distinct from the faint grid
ax.axvline(0, color=INK, linewidth=1.2, zorder=2)

for is_sig, color, marker in ((True, BRAND, "o"), (False, ANYPLOT_MUTED, "s")):
    rows = table[significant == is_sig]
    ax.errorbar(
        rows[COEFFICIENT],
        y_pos[significant.to_numpy() == is_sig],
        xerr=[(rows[COEFFICIENT] - rows[CI_LOWER]).clip(lower=0), (rows[CI_UPPER] - rows[COEFFICIENT]).clip(lower=0)],
        fmt=marker,
        color=color,
        markersize=7,
        markeredgewidth=1,
        markeredgecolor=PAGE_BG,
        capsize=4,
        capthick=1.5,
        elinewidth=1.5,
        zorder=3,
    )

# Style
title = "coefficient-confidence · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)
ax.set_yticks(y_pos, table[VARIABLE])
ax.set_ylim(-0.6, len(table) - 0.4)
ax.set_xlabel(COEFFICIENT, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT, length=0)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.spines["bottom"].set_color(INK_SOFT)
ax.xaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

legend_handles = [
    Line2D(
        [0],
        [0],
        marker="o",
        linestyle="none",
        markerfacecolor=BRAND,
        markeredgecolor=PAGE_BG,
        markersize=7,
        label="Significant (95% CI excludes 0)",
    ),
    Line2D(
        [0],
        [0],
        marker="s",
        linestyle="none",
        markerfacecolor=ANYPLOT_MUTED,
        markeredgecolor=PAGE_BG,
        markersize=7,
        label="Not significant",
    ),
]
leg = ax.legend(handles=legend_handles, loc="lower right", fontsize=8)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
