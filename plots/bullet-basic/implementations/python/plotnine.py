"""anyplot.ai
bullet-basic: Basic Bullet Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-29
"""

import os

import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_rect,
    geom_segment,
    geom_text,
    geom_tile,
    ggplot,
    guides,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme-adaptive chrome tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — brand green is always first series
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]  # #009E73 — actual value bar

# Grayscale bands: darker = worse performance zone (theme-adaptive for readability)
if THEME == "light":
    band_colors = {"Poor": "#686868", "Satisfactory": "#9E9E9E", "Good": "#C8C8C8"}
else:
    band_colors = {"Poor": "#383838", "Satisfactory": "#555555", "Good": "#727272"}

# Constants
BAND_NAMES = ["Poor", "Satisfactory", "Good"]  # qualitative bands, worst to best
RANGE_HEIGHT = 0.68  # band height in row units
ACTUAL_HEIGHT = 0.28  # measure bar height in row units

# Columns: set these to your table's column names
LABEL = "Metric"  # role: label
ACTUAL = "Actual"  # role: actual
TARGET = "Target"  # role: target
POOR_LIMIT = "Poor limit"  # role: ranges
SATISFACTORY_LIMIT = "Satisfactory limit"  # role: ranges
GOOD_LIMIT = "Good limit"  # role: ranges

# Data: replace this block with your own table, for example df = pd.read_csv("kpis.csv")
# Four business KPIs with mixed above/below-target performance
df = pd.DataFrame(
    {
        LABEL: ["Revenue ($K)", "Profit (%)", "New Orders", "Satisfaction"],
        ACTUAL: [275, 22, 1050, 4.5],
        TARGET: [250, 26, 1100, 4.2],
        POOR_LIMIT: [150, 15, 600, 2.5],
        SATISFACTORY_LIMIT: [225, 22.5, 900, 3.5],
        GOOD_LIMIT: [300, 30, 1200, 5.0],
    }
)

# Plot: reads only df and the constants above
# Every metric is normalized to 0-100 (share of its top range) so one x-axis aligns all bullets
n = len(df)
limits = df[[POOR_LIMIT, SATISFACTORY_LIMIT, GOOD_LIMIT]]
top = limits.iloc[:, -1]
bounds = pd.concat([pd.Series(0.0, index=df.index), limits.div(top, axis=0) * 100], axis=1)
bounds.columns = range(len(bounds.columns))
y_pos = pd.Series(range(n - 1, -1, -1), index=df.index)  # first metric at the top

df_tiles = pd.concat(
    [
        pd.DataFrame(
            {"y": y_pos, "x": (bounds[j] + bounds[j + 1]) / 2, "width": bounds[j + 1] - bounds[j], "band": name}
        )
        for j, name in enumerate(BAND_NAMES)
    ],
    ignore_index=True,
)

df_actual = pd.DataFrame(
    {
        "xmin": 0.0,
        "xmax": df[ACTUAL] / top * 100,
        "ymin": y_pos - ACTUAL_HEIGHT / 2,
        "ymax": y_pos + ACTUAL_HEIGHT / 2,
        "label_y": y_pos + RANGE_HEIGHT / 2 + 0.04,
        "actual": df[ACTUAL].map(lambda v: f"{v:g}"),
    }
)

df_target = pd.DataFrame(
    {"target": df[TARGET] / top * 100, "seg_ymin": y_pos - RANGE_HEIGHT / 2.2, "seg_ymax": y_pos + RANGE_HEIGHT / 2.2}
)

# Zone labels sit below the bottom bullet, centered on the typical band
zone_x = [(bounds[j].median() + bounds[j + 1].median()) / 2 for j in range(len(BAND_NAMES))]
zone_y = y_pos.min() - 0.5

plot = (
    ggplot()
    # Qualitative range bands
    + geom_tile(df_tiles, aes(x="x", y="y", width="width", fill="band"), height=RANGE_HEIGHT, color="none")
    + scale_fill_manual(values=band_colors, limits=BAND_NAMES[::-1])
    + guides(fill=False)
    # Actual value bar
    + geom_rect(df_actual, aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"), fill=BRAND, color="none")
    # Target marker — thin contrasting line perpendicular to the bar
    + geom_segment(df_target, aes(x="target", xend="target", y="seg_ymin", yend="seg_ymax"), color=INK, size=2.0)
    # Actual value labels (geom_text size in mm; ~3.5 ≈ 10pt at 400dpi)
    + geom_text(
        df_actual,
        aes(x="xmax", y="label_y", label="actual"),
        ha="right",
        va="bottom",
        size=5.5,
        color=BRAND,
        fontweight="bold",
    )
    # Band zone labels below the bottom metric
    + annotate("text", x=zone_x, y=zone_y, label=BAND_NAMES, size=6.5, color=INK_MUTED, va="top")
    # Scales
    + scale_x_continuous(limits=(0, 100), breaks=[0, 25, 50, 75, 100], expand=(0, 0.02))
    + scale_y_continuous(breaks=list(range(n)), labels=df[LABEL].tolist()[::-1], expand=(0.08, 0.08))
    + labs(title="bullet-basic · python · plotnine · anyplot.ai", x="Performance (%)", y="")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_title=element_text(size=12, ha="center", weight="bold", color=INK),
        axis_title_x=element_text(size=10, color=INK),
        axis_title_y=element_blank(),
        axis_text_x=element_text(size=8, color=INK_SOFT),
        axis_text_y=element_text(size=9, ha="right", color=INK_SOFT),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(color=INK, size=0.3, alpha=0.15),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color="none"),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
