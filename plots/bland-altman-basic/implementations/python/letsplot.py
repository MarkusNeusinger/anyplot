""" anyplot.ai
bland-altman-basic: Bland-Altman Agreement Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-07
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
BRAND = "#009E73"  # Position 1 - first categorical series
SECONDARY = "#C475FD"  # Position 2
ACCENT = "#4467A3"  # Position 3

# Data: Simulated blood pressure readings from two sphygmomanometers
np.random.seed(42)
n = 80

# True systolic BP values (realistic range: 100-160 mmHg)
true_bp = np.random.normal(125, 15, n)

# Method 1: Reference standard (small measurement error)
method1 = true_bp + np.random.normal(0, 3, n)

# Method 2: New device (slight positive bias + slightly larger error)
method2 = true_bp + np.random.normal(2, 4, n)

# Bland-Altman calculations
mean_values = (method1 + method2) / 2
diff_values = method1 - method2

mean_diff = np.mean(diff_values)
std_diff = np.std(diff_values, ddof=1)
upper_loa = mean_diff + 1.96 * std_diff
lower_loa = mean_diff - 1.96 * std_diff

# Create DataFrame
df = pd.DataFrame({"mean": mean_values, "diff": diff_values})

# Annotation data - position labels at the left side with offset from line
annot_x = df["mean"].min() + 2
y_offset = 0.8
annot_df = pd.DataFrame(
    {
        "x": [annot_x, annot_x, annot_x],
        "y": [mean_diff + y_offset, upper_loa + y_offset, lower_loa - y_offset],
        "label": [
            f"Mean Bias: {mean_diff:.2f} mmHg",
            f"+1.96 SD: {upper_loa:.2f} mmHg",
            f"-1.96 SD: {lower_loa:.2f} mmHg",
        ],
        "line_type": ["bias", "loa", "loa"],
    }
)

# Build plot with theme-adaptive styling
plot = (
    ggplot()
    + geom_point(aes(x="mean", y="diff"), data=df, color=BRAND, size=6, alpha=0.7, stroke=0.5)
    + geom_hline(yintercept=mean_diff, color=BRAND, size=1.5)
    + geom_hline(yintercept=upper_loa, color=SECONDARY, size=1.2, linetype="dashed")
    + geom_hline(yintercept=lower_loa, color=SECONDARY, size=1.2, linetype="dashed")
    + geom_label(
        aes(x="x", y="y", label="label"),
        data=annot_df[annot_df["line_type"] == "bias"],
        size=12,
        color=BRAND,
        fill=ELEVATED_BG,
        hjust=0,
        label_padding=0.3,
    )
    + geom_label(
        aes(x="x", y="y", label="label"),
        data=annot_df[annot_df["line_type"] == "loa"],
        size=12,
        color=SECONDARY,
        fill=ELEVATED_BG,
        hjust=0,
        label_padding=0.3,
    )
    + labs(
        x="Mean of Two Methods (mmHg)",
        y="Difference (Method 1 - Method 2) (mmHg)",
        title="bland-altman-basic · letsplot · anyplot.ai",
    )
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, linetype="solid"),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=24, color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
    )
)

# Save PNG and HTML with theme-suffixed filenames
ggsave(plot, f"plot-{THEME}.png", scale=3, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
