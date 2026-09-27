"""anyplot.ai
bubble-basic: Basic Bubble Chart
Library: letsplot 4.11.0 | Python 3.13.15
Quality: 92/100 | Updated: 2026-09-27
"""

import os

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
    geom_point,
    geom_smooth,
    geom_vline,
    ggplot,
    ggsave,
    ggsize,
    ggtb,
    guide_legend,
    guides,
    labs,
    layer_tooltips,
    scale_color_manual,
    scale_size_area,
    scale_x_continuous,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette — 8 hues, theme-independent, hybrid-v3 sort
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data - sports analytics: team payroll vs. win rate, bubble size = average attendance
np.random.seed(42)

conferences = ["Eastern", "Western"]
win_pct_offset = {"Eastern": 0.0, "Western": 5.0}
n_per_conference = 35

rows = []
for conference in conferences:
    payroll_millions = np.random.uniform(90, 190, n_per_conference)
    win_pct = np.clip(
        18 + win_pct_offset[conference] + 0.28 * (payroll_millions - 90) + np.random.normal(0, 9, n_per_conference),
        15,
        78,
    )
    attendance_thousands = np.clip(np.random.normal(28, 7, n_per_conference), 12, 45)
    for payroll, win, attendance in zip(payroll_millions, win_pct, attendance_thousands, strict=True):
        rows.append({"payroll": payroll, "win_pct": win, "attendance": attendance, "conference": conference})

df = pd.DataFrame(rows)
avg_payroll = df["payroll"].mean()
avg_win_pct = df["win_pct"].mean()

# Plot
plot = (
    ggplot(df, aes(x="payroll", y="win_pct", size="attendance", color="conference"))
    + geom_hline(yintercept=avg_win_pct, linetype="dotted", color=INK_SOFT, alpha=0.4, size=0.6, tooltips="none")
    + geom_vline(xintercept=avg_payroll, linetype="dotted", color=INK_SOFT, alpha=0.4, size=0.6, tooltips="none")
    + geom_smooth(
        aes(x="payroll", y="win_pct"),
        method="lm",
        se=False,
        color=INK_SOFT,
        linetype="dashed",
        size=0.8,
        alpha=0.6,
        inherit_aes=False,
        show_legend=False,
        tooltips="none",
    )
    + geom_point(
        alpha=0.32,
        tooltips=layer_tooltips()
        .format("payroll", "${.0f}M")
        .format("win_pct", "{.1f}%")
        .format("attendance", "{.1f}K")
        .line("@conference")
        .line("Payroll|@payroll")
        .line("Win Rate|@win_pct")
        .line("Avg. Attendance|@attendance"),
    )
    + scale_size_area(max_size=13, name="Avg. Attendance (K)", breaks=[15, 25, 35, 45])
    + scale_color_manual(values=IMPRINT_PALETTE[:2], name="Conference")
    + scale_x_continuous(expand=[0.02, 5])
    + guides(
        color=guide_legend(nrow=1, override_aes={"size": 7}),
        size=guide_legend(nrow=1, override_aes={"color": IMPRINT_PALETTE[0], "alpha": 0.32}),
    )
    + labs(x="Team Payroll (Million USD)", y="Win Rate (%)", title="bubble-basic · python · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        # color must match fill explicitly: an unset color on panel_background
        # renders a visible default border once a legend is present, even
        # with panel_border=element_blank() (lets-plot 4.11.0 quirk).
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_border=element_blank(),
        axis_title=element_text(size=13, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        plot_title=element_text(size=18, color=INK),
        plot_margin=[30, 20, 20, 20],
        legend_title=element_text(size=10, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        # color must match fill: legend frames are removed per the
        # decoration-removal checklist (no visible box border).
        legend_background=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
        panel_grid_major=element_line(size=0.3, color=RULE),
        panel_grid_minor=element_blank(),
        legend_position="bottom",
        legend_box="horizontal",
        legend_spacing=20,
    )
    + ggsize(800, 450)
)

# Save: static PNG without the interactive toolbar, HTML with letsplot's
# distinctive pan/zoom toolbar (ggtb) layered on top for the interactive export
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot + ggtb(), f"plot-{THEME}.html", path=".")
