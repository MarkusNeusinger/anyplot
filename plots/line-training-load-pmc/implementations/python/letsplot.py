"""anyplot.ai
line-training-load-pmc: Training Load Performance Management Chart
Library: letsplot 4.10.1 | Python 3.13.13
Quality: pending | Created: 2026-06-13
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
GRID_MINOR = "rgba(26,26,23,0.05)" if THEME == "light" else "rgba(240,239,232,0.05)"

# Imprint categorical palette — first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
COLOR_CTL = IMPRINT_PALETTE[0]  # green — Fitness (first series, always)
COLOR_ATL = IMPRINT_PALETTE[1]  # lavender — Fatigue
COLOR_TSB_POS = IMPRINT_PALETTE[2]  # blue — positive form / fresh
COLOR_TSB_NEG = IMPRINT_PALETTE[4]  # matte red — negative form / fatigued (semantic)

# Constants
K_CTL = 2 / (42 + 1)  # chronic load: 42-day exponential average
K_ATL = 2 / (7 + 1)  # acute load: 7-day exponential average

# Columns: set these to your table's column names
DATE = "Date"  # role: date
TSS = "Daily TSS"  # role: tss
CTL = "Fitness (CTL)"  # role: ctl
ATL = "Fatigue (ATL)"  # role: atl
TSB = "Form (TSB)"  # role: tsb

# Data: replace this block with your own table, for example df = pd.read_csv("training.csv")
np.random.seed(42)
n_days = 180
dates = pd.date_range("2024-01-01", periods=n_days)

# Four-week blocks (3 build + 1 recovery), load ramps through month 4, tapers month 5
tss_list = []
for i in range(n_days):
    week_in_block = (i // 7) % 4
    day_of_week = i % 7
    month = min(i // 30, 5)
    base = [55, 65, 75, 85, 90, 60][month]
    if week_in_block == 3:
        base *= 0.55
    if day_of_week == 0:
        tss_i = max(0.0, np.random.normal(15, 8))
    elif day_of_week == 3:
        tss_i = max(0.0, np.random.normal(base * 0.50, 10))
    elif day_of_week in [1, 4, 6]:
        tss_i = max(0.0, np.random.normal(base * 1.35, 18))
    else:
        tss_i = max(0.0, np.random.normal(base * 0.75, 12))
    tss_list.append(round(tss_i, 1))

tss = np.array(tss_list)
ctl = np.zeros(n_days)
atl = np.zeros(n_days)
ctl[0] = atl[0] = tss[0]
for i in range(1, n_days):
    ctl[i] = tss[i] * K_CTL + ctl[i - 1] * (1 - K_CTL)
    atl[i] = tss[i] * K_ATL + atl[i - 1] * (1 - K_ATL)

# TSB (form) = previous-day CTL minus previous-day ATL
tsb = np.zeros(n_days)
tsb[1:] = ctl[:-1] - atl[:-1]

df = pd.DataFrame({DATE: dates, TSS: tss, CTL: ctl, ATL: atl, TSB: tsb})

# Plot: reads only df and the constants above
label_pos = f"Positive {TSB}"
label_neg = f"Negative {TSB}"
df_form = df.assign(
    zero=0.0,
    tsb_pos=df[TSB].clip(lower=0.0),
    tsb_neg=df[TSB].clip(upper=0.0),
    pos_label=label_pos,
    neg_label=label_neg,
    tss_label=TSS,
)

# Long format for CTL/ATL drives the color legend
df_lines = df.melt(id_vars=[DATE], value_vars=[CTL, ATL], var_name="metric", value_name="value")

# Title — 55 chars < 67 baseline, no font scaling needed
title_str = "line-training-load-pmc · python · letsplot · anyplot.ai"

# Shared theme (applied to both panels)
base_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=GRID, size=0.3),
    panel_grid_minor=element_line(color=GRID_MINOR, size=0.2),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT),
    axis_ticks=element_blank(),
    panel_border=element_blank(),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_blank(),
)

# Main panel: TSB ribbon (two-toned) + CTL/ATL lines + zero reference
plot_main = (
    ggplot()
    + geom_ribbon(data=df_form, mapping=aes(x=DATE, ymin="zero", ymax="tsb_pos", fill="pos_label"), alpha=0.45, size=0)
    + geom_ribbon(data=df_form, mapping=aes(x=DATE, ymin="tsb_neg", ymax="zero", fill="neg_label"), alpha=0.45, size=0)
    + geom_hline(yintercept=0, color=INK_SOFT, size=0.5, linetype="dashed")
    + geom_line(data=df_lines, mapping=aes(x=DATE, y="value", color="metric"), size=1.5)
    + scale_color_manual(values={CTL: COLOR_CTL, ATL: COLOR_ATL})
    + scale_fill_manual(values={label_pos: COLOR_TSB_POS, label_neg: COLOR_TSB_NEG})
    + scale_x_datetime(format="%b")
    + scale_y_continuous(limits=[df[TSB].min() * 1.15, df[[CTL, ATL]].max().max() * 1.3])
    + labs(title=title_str, x="", y=f"Training load / form ({CTL[-4:-1]}, {ATL[-4:-1]}, {TSB[-4:-1]})")
    + base_theme
    + theme(
        plot_title=element_text(color=INK, size=16),
        axis_text_x=element_blank(),
        axis_ticks_x=element_blank(),
        legend_position=[0.01, 0.99],
        legend_justification=[0, 1],
        legend_direction="horizontal",
    )
)

# TSS panel: daily training stress scores as bars
plot_tss = (
    ggplot(df_form, aes(x=DATE, y=TSS))
    + geom_bar(stat="identity", mapping=aes(fill="tss_label"), color=INK_MUTED, alpha=0.65, size=0)
    + scale_fill_manual(values={TSS: INK_MUTED})
    + scale_x_datetime(format="%b")
    + scale_y_continuous(limits=[0, df[TSS].max() * 1.4])
    + labs(x=f"Month ({df[DATE].dt.year.iloc[0]})", y=TSS)
    + base_theme
    + theme(
        plot_title=element_blank(),
        legend_position=[0.01, 0.99],
        legend_justification=[0, 1],
        legend_direction="horizontal",
    )
)

# Combine panels; the page color on the composite avoids white edges
combined = (
    gggrid([plot_main, plot_tss], ncol=1, heights=[3, 1.2])
    + ggsize(800, 450)
    + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))
)

# Save PNG and HTML for both themes
ggsave(combined, f"plot-{THEME}.png", scale=4, path=".")
ggsave(combined, f"plot-{THEME}.html", path=".")
