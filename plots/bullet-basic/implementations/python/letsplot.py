"""anyplot.ai
bullet-basic: Basic Bullet Chart
Library: letsplot 4.10.1 | Python 3.13.13
Quality: pending | Updated: 2026-05-29
"""
# ruff: noqa: F405

import os
import shutil

import pandas as pd
from lets_plot import *  # noqa: F403, F405


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: the single measure-bar color is position 1
BRAND = "#009E73"

# Grayscale qualitative bands (Stephen Few): darker = poorer on the light page, flipped on the dark page
BAND_COLORS = (
    {"Poor": "#585858", "Satisfactory": "#989898", "Good": "#D0D0D0"}
    if THEME == "light"
    else {"Poor": "#707068", "Satisfactory": "#565650", "Good": "#3C3C38"}
)

# Columns: set these to your table's column names
METRIC = "Metric"  # role: label
ACTUAL = "Actual"  # role: actual
TARGET = "Target"  # role: target
POOR = "Poor limit"  # role: extra
SATISFACTORY = "Satisfactory limit"  # role: extra
GOOD = "Good limit"  # role: ranges
RANGES = [POOR, SATISFACTORY, GOOD]

# Data: replace this block with your own table, for example df = pd.read_csv("kpis.csv")
df = pd.DataFrame(
    {
        METRIC: ["Revenue ($K)", "Profit Margin (%)", "Satisfaction (1-5)", "New Customers"],
        ACTUAL: [275, 38, 3.8, 42],
        TARGET: [300, 42, 4.5, 40],
        POOR: [100, 20, 2.5, 15],
        SATISFACTORY: [200, 35, 3.5, 30],
        GOOD: [350, 50, 5.0, 50],
    }
)

# Plot: reads only df and the constants above
# Every metric is rescaled to its top band (= 100) so all bullets share one linear axis
top = df[GOOD]
n = len(df)
y_center = pd.Series(range(n - 1, -1, -1), dtype=float)  # first row on top
band_h, bar_h, marker_h = 0.40, 0.16, 0.34

df_bands = pd.concat(
    [
        pd.DataFrame(
            {
                "xmin": 0.0,
                "xmax": df[limit] / top * 100,
                "ymin": y_center - band_h,
                "ymax": y_center + band_h,
                "band": name,
            }
        )
        for limit, name in zip(
            reversed(RANGES), reversed(list(BAND_COLORS)), strict=True
        )  # widest band first, narrower on top
    ]
)

df_bars = pd.DataFrame(
    {
        "xmin": 0.0,
        "xmax": df[ACTUAL] / top * 100,
        "ymin": y_center - bar_h,
        "ymax": y_center + bar_h,
        "metric": df[METRIC],
        "actual_val": df[ACTUAL].map(lambda v: f"{v:g}"),
        "target_val": df[TARGET].map(lambda v: f"{v:g}"),
        "achievement": (df[ACTUAL] / df[TARGET] * 100).map(lambda v: f"{v:.0f}%"),
    }
)

df_target = pd.DataFrame({"x": df[TARGET] / top * 100, "ymin": y_center - marker_h, "ymax": y_center + marker_h})

# Value label just past the end of whichever is longer, the bar or the target marker
df_label = pd.DataFrame(
    {
        "x": pd.concat([df_bars["xmax"], df_target["x"]], axis=1).max(axis=1) + 2,
        "y": y_center,
        "label": df[ACTUAL].map(lambda v: f"{v:g}"),
    }
)

plot = (
    ggplot()
    + geom_rect(
        data=df_bands,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="band"),
        size=0,
        show_legend=False,
    )
    + geom_rect(
        data=df_bars,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        fill=BRAND,
        size=0,
        tooltips=(
            layer_tooltips()
            .line("@{metric}")
            .line("Actual|@{actual_val}")
            .line("Target|@{target_val}")
            .line("Achievement|@{achievement}")
        ),
    )
    + geom_segment(data=df_target, mapping=aes(x="x", y="ymin", xend="x", yend="ymax"), size=2.5, color=INK)
    + geom_text(data=df_label, mapping=aes(x="x", y="y", label="label"), size=4, hjust=0, fontface="bold", color=INK)
    + scale_fill_manual(values=BAND_COLORS)
    + scale_x_continuous(name="Performance (% of top band)", limits=[0, 112], expand=[0, 0])
    + scale_y_continuous(breaks=list(y_center), labels=list(df[METRIC]), limits=[-0.6, n - 0.4], expand=[0, 0])
    + labs(
        title="bullet-basic · python · letsplot · anyplot.ai",
        subtitle="Q4 2024 Dashboard — Actual vs. Target Performance",
        y="",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=16, face="bold", color=INK),
        plot_subtitle=element_text(size=11, color=INK_SOFT),
        axis_title_x=element_text(size=12, color=INK),
        axis_title_y=element_blank(),
        axis_text_x=element_text(size=10, color=INK_SOFT),
        axis_text_y=element_text(size=10, face="bold", color=INK),
        legend_position="none",
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(size=0.3, color=INK_SOFT),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
    )
    + ggsize(800, 450)
)

# Save: scale=4 yields 3200x1800 px
ggsave(plot, f"plot-{THEME}.png", scale=4)
ggsave(plot, f"plot-{THEME}.html")

# Move from the lets-plot-images subfolder if ggsave placed the files there
for fname in [f"plot-{THEME}.png", f"plot-{THEME}.html"]:
    src = os.path.join("lets-plot-images", fname)
    if os.path.exists(src):
        shutil.move(src, fname)
if os.path.exists("lets-plot-images"):
    shutil.rmtree("lets-plot-images")
