""" anyplot.ai
bar-heart-rate-zones: Time in Heart Rate Zones Bar Chart
Library: plotnine 0.15.7 | Python 3.13.13
Quality: 88/100 | Created: 2026-06-14
"""

import os

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_bar,
    geom_text,
    ggplot,
    labs,
    scale_alpha_manual,
    scale_fill_manual,
    scale_y_continuous,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "#1A1A171E" if THEME == "light" else "#F0EFE81E"

# Heart rate zone colors — semantic exception to Imprint canonical order:
# Z1–Z5 carry strong fitness conventions (grey/blue/green/orange/red),
# mapped to the nearest Imprint palette members.
# Z1 uses fixed #6B6A63 (not theme-adaptive INK_MUTED) so data colors
# stay identical across light and dark renders.
ZONE_COLORS = ["#6B6A63", "#4467A3", "#009E73", "#BD8233", "#AE3030"]

# Data — 75-minute endurance run with threshold intervals
zones = ["Z1\nRecovery", "Z2\nEndurance", "Z3\nAerobic", "Z4\nThreshold", "Z5\nMaximum"]
minutes = [12.0, 38.0, 14.0, 9.0, 2.0]

df = pd.DataFrame({"zone": zones, "minutes": minutes})
df["zone"] = pd.Categorical(df["zone"], categories=zones, ordered=True)
df["duration_label"] = df["minutes"].apply(lambda m: f"{int(m)} min")
# Z2 (Endurance) dominates at 51% — map emphasis aesthetic to guide reader focus
df["emphasis"] = ["secondary", "primary", "secondary", "secondary", "secondary"]

title = "bar-heart-rate-zones · python · plotnine · anyplot.ai"
caption = "HR bounds: Z1 < 120 | Z2: 120–139 | Z3: 140–154 | Z4: 155–169 | Z5: ≥ 170 bpm"

plot = (
    ggplot(df, aes(x="zone", y="minutes"))
    + geom_bar(aes(fill="zone", alpha="emphasis"), stat="identity", width=0.65, show_legend=False)
    + geom_text(aes(label="duration_label"), va="bottom", nudge_y=0.8, size=4.0, color=INK)
    + scale_fill_manual(values=dict(zip(zones, ZONE_COLORS, strict=True)))
    + scale_alpha_manual(values={"primary": 1.0, "secondary": 0.7})
    + scale_y_continuous(limits=(0, 45), expand=(0, 0), breaks=[0, 10, 20, 30, 40])
    + labs(title=title, caption=caption, x=None, y="Duration (minutes)")
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_y=element_line(color=GRID, size=0.3),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_border=element_blank(),
        axis_line_x=element_line(color=INK_SOFT, size=0.5),
        axis_line_y=element_blank(),
        axis_ticks=element_blank(),
        axis_title_x=element_blank(),
        axis_title_y=element_text(color=INK, size=10),
        axis_text_x=element_text(color=INK_SOFT, size=8),
        axis_text_y=element_text(color=INK_SOFT, size=8),
        plot_title=element_text(color=INK, size=12, ha="center"),
        plot_caption=element_text(color=INK_MUTED, size=8, ha="right"),
        legend_position="none",
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
