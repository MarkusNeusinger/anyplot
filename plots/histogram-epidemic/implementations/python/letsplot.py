""" pyplots.ai
histogram-epidemic: Epidemic Curve (Epi Curve)
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-05
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_bar,
    geom_line,
    geom_rect,
    geom_text,
    geom_vline,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_manual,
    scale_x_datetime,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data — simulated foodborne outbreak with point-source shape
np.random.seed(42)

outbreak_start = pd.Timestamp("2024-03-01")
n_days = 45
dates = pd.date_range(outbreak_start, periods=n_days, freq="D")

# Point-source outbreak: sharp rise, gradual decline (log-normal shape)
days = np.arange(n_days)
confirmed_rate = 120 * np.exp(-0.5 * ((np.log(days + 1) - np.log(12)) / 0.45) ** 2)
probable_rate = 35 * np.exp(-0.5 * ((np.log(days + 1) - np.log(14)) / 0.5) ** 2)
suspect_rate = 15 * np.exp(-0.5 * ((np.log(days + 1) - np.log(10)) / 0.55) ** 2)

confirmed_counts = np.random.poisson(np.maximum(confirmed_rate, 0.1)).astype(int)
probable_counts = np.random.poisson(np.maximum(probable_rate, 0.1)).astype(int)
suspect_counts = np.random.poisson(np.maximum(suspect_rate, 0.1)).astype(int)

df = pd.DataFrame(
    {
        "onset_date": np.tile(dates, 3),
        "case_count": np.concatenate([confirmed_counts, probable_counts, suspect_counts]),
        "case_type": ["Confirmed"] * n_days + ["Probable"] * n_days + ["Suspect"] * n_days,
    }
)

# Cumulative case counts for overlay line (scaled to share y-axis)
daily_total = confirmed_counts + probable_counts + suspect_counts
cumulative = np.cumsum(daily_total)
max_daily = int(daily_total.max())
max_cumulative = int(cumulative[-1])
scale_factor = max_daily * 0.90 / max_cumulative

df_cumulative = pd.DataFrame({"onset_date": dates, "scaled_cumulative": cumulative * scale_factor})

# Secondary y-axis label for cumulative line
cumul_label_y = cumulative[-1] * scale_factor
df_cumul_label = pd.DataFrame(
    {"onset_date": [dates[-3]], "y_pos": [cumul_label_y * 0.92], "label": [f"{max_cumulative:,}\ncumulative"]}
)

# Intervention dates — epoch milliseconds for lets-plot datetime axis
lockdown_date = pd.Timestamp("2024-03-15")
vaccination_date = pd.Timestamp("2024-04-05")
lockdown_ms = lockdown_date.timestamp() * 1000
vaccination_ms = vaccination_date.timestamp() * 1000

# Background highlight rectangles behind annotation labels
label_width_ms = 5.5 * 86400 * 1000
df_lockdown_bg = pd.DataFrame(
    {
        "xmin": [lockdown_ms + 30000000],
        "xmax": [lockdown_ms + 30000000 + label_width_ms],
        "ymin": [max_daily * 0.87],
        "ymax": [max_daily * 0.97],
    }
)
df_vacc_bg = pd.DataFrame(
    {
        "xmin": [vaccination_ms - 8 * 86400 * 1000],
        "xmax": [vaccination_ms - 8 * 86400 * 1000 + 7 * 86400 * 1000],
        "ymin": [max_daily * 0.77],
        "ymax": [max_daily * 0.87],
    }
)

# Annotation data for intervention labels
df_ann_lockdown = pd.DataFrame(
    {"onset_date": [lockdown_date], "y_pos": [max_daily * 0.92], "label": ["Lockdown Start"]}
)
df_ann_vacc = pd.DataFrame(
    {"onset_date": [vaccination_date], "y_pos": [max_daily * 0.82], "label": ["Vaccination Campaign"]}
)

# Weekly x-axis breaks
weekly_dates = pd.date_range(outbreak_start, periods=7, freq="7D")
weekly_ms = [d.timestamp() * 1000 for d in weekly_dates]

# Colors
color_confirmed = "#306998"
color_probable = "#C07830"
color_suspect = "#8B8B8B"

# Plot
plot = (
    ggplot(df, aes(x="onset_date", y="case_count", fill="case_type"))
    + geom_bar(
        stat="identity",
        position="stack",
        width=0.8,
        tooltips=layer_tooltips().format("case_count", "d").line("@|case_type").line("Cases|@case_count"),
    )
    + geom_line(
        data=df_cumulative,
        mapping=aes(x="onset_date", y="scaled_cumulative"),
        color="#333333",
        size=1.8,
        alpha=0.75,
        inherit_aes=False,
        tooltips="none",
    )
    + geom_vline(xintercept=lockdown_ms, color="#CC3333", size=1.3, linetype="dashed")
    + geom_vline(xintercept=vaccination_ms, color="#339933", size=1.3, linetype="dashed")
    # Subtle background rectangles behind labels
    + geom_rect(
        data=df_lockdown_bg,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        fill="white",
        alpha=0.85,
        inherit_aes=False,
        color="#CCCCCC",
        size=0.3,
    )
    + geom_rect(
        data=df_vacc_bg,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        fill="white",
        alpha=0.85,
        inherit_aes=False,
        color="#CCCCCC",
        size=0.3,
    )
    + geom_text(
        data=df_ann_lockdown,
        mapping=aes(x="onset_date", y="y_pos", label="label"),
        color="#333333",
        size=11,
        fontface="bold",
        hjust=0,
        nudge_x=80000000,
        inherit_aes=False,
    )
    + geom_text(
        data=df_ann_vacc,
        mapping=aes(x="onset_date", y="y_pos", label="label"),
        color="#333333",
        size=11,
        fontface="bold",
        hjust=1,
        nudge_x=-80000000,
        inherit_aes=False,
    )
    # Cumulative line endpoint label (secondary y-axis context)
    + geom_text(
        data=df_cumul_label,
        mapping=aes(x="onset_date", y="y_pos", label="label"),
        color="#333333",
        size=9,
        fontface="italic",
        hjust=1,
        inherit_aes=False,
    )
    + scale_fill_manual(
        values={"Confirmed": color_confirmed, "Probable": color_probable, "Suspect": color_suspect},
        name="Case Classification",
    )
    + scale_x_datetime(name="Date of Symptom Onset", format="%b %d", breaks=weekly_ms)
    + scale_y_continuous(name="Daily New Cases", format="d")
    + labs(
        title="histogram-epidemic · letsplot · pyplots.ai",
        subtitle="Foodborne outbreak epi curve — daily cases by classification with cumulative trend",
        caption=f"Dark line = cumulative cases (scaled)  ·  {max_cumulative:,} total cases",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        plot_subtitle=element_text(size=16, color="#555555"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=16, face="bold"),
        legend_text=element_text(size=14),
        plot_caption=element_text(size=16, color="#555555", hjust=0.5),
        legend_position=[0.82, 0.88],
        legend_background=element_rect(fill="white", color="#DDDDDD", size=0.5),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.5),
        plot_background=element_rect(fill="white", color="white"),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
