"""pyplots.ai
histogram-epidemic: Epidemic Curve (Epi Curve)
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-05
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
scale_factor = max_daily * 0.9 / max_cumulative

df_cumulative = pd.DataFrame({"onset_date": dates, "scaled_cumulative": cumulative * scale_factor})

# Intervention dates
lockdown_date = pd.Timestamp("2024-03-15")
vaccination_date = pd.Timestamp("2024-04-05")

# Annotation data for intervention labels
df_annotations = pd.DataFrame(
    {
        "onset_date": [lockdown_date, vaccination_date],
        "y_pos": [max_daily * 0.92, max_daily * 0.82],
        "label": ["Lockdown\nStart", "Vaccination\nCampaign"],
    }
)

# Colors
color_confirmed = "#306998"
color_probable = "#B07430"
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
        color="#222222",
        size=1.5,
        alpha=0.7,
        inherit_aes=False,
        tooltips="none",
    )
    + geom_vline(xintercept=lockdown_date.timestamp() * 1000, color="#CC4444", size=1.2, linetype="dashed")
    + geom_vline(xintercept=vaccination_date.timestamp() * 1000, color="#44AA44", size=1.2, linetype="dashed")
    + geom_text(
        data=df_annotations,
        mapping=aes(x="onset_date", y="y_pos", label="label"),
        color="#333333",
        size=11,
        fontface="bold",
        hjust=0,
        nudge_x=50000000,
        inherit_aes=False,
    )
    + scale_fill_manual(
        values={"Confirmed": color_confirmed, "Probable": color_probable, "Suspect": color_suspect},
        name="Case Classification",
    )
    + scale_x_datetime(name="Date of Symptom Onset", format="%b %d")
    + scale_y_continuous(name="Daily New Cases", format="d")
    + labs(
        title="histogram-epidemic · letsplot · pyplots.ai",
        subtitle="Foodborne outbreak epi curve — daily cases by classification with cumulative trend",
        caption="Black line = cumulative cases (scaled)",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        plot_subtitle=element_text(size=16, color="#666666"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=16, face="bold"),
        legend_text=element_text(size=14),
        plot_caption=element_text(size=14, color="#666666"),
        legend_position=[0.88, 0.55],
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
