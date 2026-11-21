"""anyplot.ai
point-basic: Point Estimate Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
"""

import os

import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
NULL_VALUE = 0  # the no-effect value the reference line marks

# Columns: set these to your table's column names
GROUP = "Treatment group"  # role: category
ESTIMATE = "Effect size"  # role: estimate
LOWER = "Lower (95% CI)"  # role: lower_bound
UPPER = "Upper (95% CI)"  # role: upper_bound

# Data: replace this block with your own table, for example df = pd.read_csv("effects.csv")
estimates = [4.2, 5.8, 3.1, 2.5, 1.8]
half_widths = [0.9, 1.1, 0.7, 0.8, 0.6]
df = pd.DataFrame(
    {
        GROUP: ["Treatment A", "Treatment B", "Treatment C", "Control", "Placebo"],
        ESTIMATE: estimates,
        LOWER: [e - w for e, w in zip(estimates, half_widths, strict=True)],
        UPPER: [e + w for e, w in zip(estimates, half_widths, strict=True)],
    }
)

# Plot: horizontal point estimates with capped confidence intervals
plot = (
    ggplot(df, aes(x=GROUP))
    + geom_hline(yintercept=NULL_VALUE, linetype="dashed", color=INK_SOFT, size=0.5, alpha=0.6)
    + geom_errorbar(aes(ymin=LOWER, ymax=UPPER), color=IMPRINT_PALETTE[0], width=0.25, size=1.0)
    + geom_point(aes(y=ESTIMATE), color=IMPRINT_PALETTE[0], fill=PAGE_BG, shape=21, size=6, stroke=1.5)
    + labs(y="Effect size (95% CI)", x=GROUP, title="point-basic · python · letsplot · anyplot.ai")
    + coord_flip()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_x=element_line(color=RULE, size=0.3),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_blank(),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=16, color=INK),
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
