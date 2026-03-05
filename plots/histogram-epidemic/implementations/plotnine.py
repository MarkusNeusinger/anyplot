""" pyplots.ai
histogram-epidemic: Epidemic Curve (Epi Curve)
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-05
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_col,
    geom_line,
    geom_text,
    geom_vline,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_date,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data
np.random.seed(42)

start_date = pd.Timestamp("2024-01-15")
dates = pd.date_range(start_date, periods=90, freq="D")

# Simulate a point-source outbreak with propagated secondary wave
days = np.arange(90)
confirmed_rate = (
    45 * np.exp(-0.5 * ((days - 18) / 5) ** 2) + 25 * np.exp(-0.5 * ((days - 55) / 10) ** 2) + np.random.poisson(2, 90)
)
probable_rate = (
    15 * np.exp(-0.5 * ((days - 20) / 6) ** 2) + 10 * np.exp(-0.5 * ((days - 57) / 11) ** 2) + np.random.poisson(1, 90)
)
suspect_rate = (
    8 * np.exp(-0.5 * ((days - 22) / 7) ** 2) + 5 * np.exp(-0.5 * ((days - 60) / 12) ** 2) + np.random.poisson(1, 90)
)

confirmed = np.maximum(confirmed_rate.astype(int), 0)
probable = np.maximum(probable_rate.astype(int), 0)
suspect = np.maximum(suspect_rate.astype(int), 0)

# Stacked bar data (long format)
df = pd.DataFrame(
    {
        "onset_date": np.tile(dates, 3),
        "case_count": np.concatenate([confirmed, probable, suspect]),
        "case_type": ["Confirmed"] * 90 + ["Probable"] * 90 + ["Suspect"] * 90,
    }
)
df["case_type"] = pd.Categorical(df["case_type"], categories=["Suspect", "Probable", "Confirmed"], ordered=True)

# Cumulative case count line overlay (aggregated daily totals)
daily_totals = df.groupby("onset_date")["case_count"].sum().reset_index()
daily_totals["cumulative"] = daily_totals["case_count"].cumsum()

# Intervention dates
lockdown_date = pd.Timestamp("2024-02-10")
vaccination_date = pd.Timestamp("2024-03-01")

interventions = pd.DataFrame(
    {"date": [lockdown_date, vaccination_date], "label": ["Lockdown", "Vaccination\ncampaign"]}
)

# Compute scale factor for secondary axis (cumulative on right y-axis)
max_daily = daily_totals["case_count"].max()
max_cumul = daily_totals["cumulative"].max()
scale_factor = max_daily / max_cumul
daily_totals["cumulative_scaled"] = daily_totals["cumulative"] * scale_factor

# Plot
plot = (
    ggplot(df, aes(x="onset_date", y="case_count"))
    + geom_col(aes(fill="case_type"), width=0.85)
    + geom_line(
        data=daily_totals, mapping=aes(x="onset_date", y="cumulative_scaled"), color="#8B0000", size=1.2, alpha=0.85
    )
    + geom_vline(
        data=interventions, mapping=aes(xintercept="date"), linetype="dashed", color="#444444", size=0.6, alpha=0.7
    )
    + geom_text(
        data=interventions,
        mapping=aes(x="date", label="label"),
        y=max_daily * 0.88,
        ha="left",
        nudge_x=1.5,
        size=10,
        color="#444444",
        fontstyle="italic",
    )
    + annotate(
        "text",
        x=dates[-1],
        y=daily_totals["cumulative_scaled"].iloc[-1],
        label="Cumulative\ncases →",
        ha="right",
        va="bottom",
        size=10,
        color="#8B0000",
        fontstyle="italic",
        fontweight="bold",
    )
    + annotate(
        "segment",
        x=dates[-8],
        xend=dates[-2],
        y=daily_totals["cumulative_scaled"].iloc[-8],
        yend=daily_totals["cumulative_scaled"].iloc[-2],
        color="#8B0000",
        size=0.5,
        alpha=0.4,
    )
    + scale_fill_manual(values={"Confirmed": "#306998", "Probable": "#E8963E", "Suspect": "#C0C0C0"})
    + scale_x_date(date_breaks="2 weeks", date_labels="%b %d")
    + scale_y_continuous(expand=(0, 0, 0.08, 0))
    + labs(
        x="Date of Symptom Onset",
        y="Number of New Cases",
        fill="Case Classification",
        title="histogram-epidemic \u00b7 plotnine \u00b7 pyplots.ai",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, family="sans-serif"),
        axis_title=element_text(size=20, weight="bold"),
        axis_text=element_text(size=16),
        axis_text_x=element_text(rotation=45, ha="right"),
        plot_title=element_text(size=24, weight="bold"),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18, weight="bold"),
        legend_position="top",
        legend_background=element_rect(fill="white", alpha=0.8),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.3),
        axis_line_x=element_line(color="#333333", size=0.5),
        axis_line_y=element_line(color="#333333", size=0.5),
        plot_background=element_rect(fill="#FAFAFA", color="none"),
        panel_background=element_rect(fill="#FAFAFA", color="none"),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
