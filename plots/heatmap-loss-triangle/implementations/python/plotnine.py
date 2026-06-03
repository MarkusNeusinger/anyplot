import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_text,
    geom_tile,
    ggplot,
    labs,
    scale_alpha_manual,
    scale_color_identity,
    scale_fill_gradient,
    scale_x_continuous,
    scale_y_reverse,
    theme,
    theme_minimal,
)


# Imprint palette — theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Actuarial loss development triangle data
np.random.seed(42)
accident_years = list(range(2015, 2025))
development_periods = list(range(1, 11))
n_years = len(accident_years)
n_periods = len(development_periods)

# 2019 is a catastrophe year with ~50% higher initial claims
base_claims = np.array([3200, 3450, 3100, 3600, 5200, 3500, 3900, 4100, 3700, 4200])
dev_factors = np.array([2.50, 1.60, 1.30, 1.15, 1.08, 1.05, 1.03, 1.02, 1.01])

cumulative = np.zeros((n_years, n_periods))
for i in range(n_years):
    cumulative[i, 0] = base_claims[i] + np.random.normal(0, 100)
    for j in range(1, n_periods):
        noise = 1 + np.random.normal(0, 0.02)
        cumulative[i, j] = cumulative[i, j - 1] * dev_factors[j - 1] * noise
cumulative = np.round(cumulative, 0).astype(int)

rows = []
for i, ay in enumerate(accident_years):
    for j, dp in enumerate(development_periods):
        is_projected = (i + j) >= n_years
        rows.append(
            {
                "accident_year": ay,
                "development_period": dp,
                "cumulative_amount": cumulative[i, j],
                "is_projected": is_projected,
            }
        )

df = pd.DataFrame(rows)
df["label"] = df["cumulative_amount"].apply(lambda v: f"{v:,}")
df["region"] = df["is_projected"].map({False: "Actual", True: "Projected"})

# Theme-adaptive text color for cell annotations
amount_thresh = df["cumulative_amount"].quantile(0.45)
light_ink = "#FAF8F1" if THEME == "light" else "#F0EFE8"
df["text_color"] = df["cumulative_amount"].apply(lambda v: light_ink if v > amount_thresh else INK)

# Development factors row positioned below main triangle
dev_factor_y = max(accident_years) + 1.3
df_dev = pd.DataFrame(
    {
        "development_period": [j + 1.5 for j in range(len(dev_factors))],
        "accident_year": dev_factor_y,
        "label": [f"{f:.2f}" for f in dev_factors],
        "cumulative_amount": 0.0,
        "region": "Actual",
    }
)

plot = (
    ggplot(df, aes(x="development_period", y="accident_year"))
    + geom_tile(aes(fill="cumulative_amount", alpha="region"), color=PAGE_BG, size=0.8)
    + geom_text(aes(label="label", color="text_color"), size=3.0)
    + geom_text(
        aes(x="development_period", y="accident_year", label="label"),
        data=df_dev,
        size=3.0,
        color="#009E73",
        fontweight="bold",
        inherit_aes=False,
    )
    # Imprint sequential: brand green (low magnitude) → blue (high magnitude)
    + scale_fill_gradient(low="#009E73", high="#4467A3", name="Cumulative\nAmount")
    + scale_alpha_manual(values={"Actual": 1.0, "Projected": 0.35}, name="Region")
    + scale_color_identity()
    + scale_x_continuous(breaks=development_periods, labels=[str(d) for d in development_periods], expand=(0, 0.5))
    + scale_y_reverse(
        breaks=accident_years + [dev_factor_y],
        labels=[str(y) for y in accident_years] + ["Dev Factor"],
        expand=(0, 0.2, 0, 1.0),
    )
    + labs(
        x="Development Period (Years)",
        y="Accident Year",
        title="heatmap-loss-triangle · plotnine · anyplot.ai",
        subtitle="Cumulative Paid Claims — Actual vs Projected  ·  Development Factors shown below",
    )
    + theme_minimal()
    + theme(
        figure_size=(6, 6),
        plot_title=element_text(size=12, ha="center", weight="bold", color=INK),
        plot_subtitle=element_text(size=9, ha="center", color=INK_SOFT),
        plot_margin=0.02,
        axis_title=element_text(size=10, color=INK),
        axis_text_x=element_text(size=8, color=INK_SOFT),
        axis_text_y=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=8, weight="bold", color=INK),
        legend_text=element_text(size=7, color=INK_SOFT),
        legend_position="right",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_box_margin=0,
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in")
