""" anyplot.ai
bar-race-animated: Animated Bar Chart Race
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-19
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_flip,
    element_blank,
    element_line,
    element_rect,
    element_text,
    facet_wrap,
    geom_col,
    geom_text,
    ggplot,
    labs,
    scale_fill_manual,
    scale_y_continuous,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

NEUTRAL = "#1A1A1A" if THEME == "light" else "#E8E8E0"

PALETTE = [
    "#009E73",  # TechCorp - bluish green
    "#C475FD",  # DataFlow - vermillion
    "#4467A3",  # CloudBase - blue
    "#BD8233",  # NetSys - reddish purple
    "#AE3030",  # CodeLab - orange
    "#2ABCCD",  # AppStream - sky blue
    "#954477",  # ByteWorks - yellow
    NEUTRAL,  # DigiCore - adaptive neutral
]

# Data - Tech companies revenue over time (billions USD)
np.random.seed(42)

companies = ["TechCorp", "DataFlow", "CloudBase", "NetSys", "CodeLab", "AppStream", "ByteWorks", "DigiCore"]

years = [2018, 2020, 2022, 2024]

base_values = {
    "TechCorp": 150,
    "DataFlow": 80,
    "CloudBase": 60,
    "NetSys": 120,
    "CodeLab": 40,
    "AppStream": 90,
    "ByteWorks": 70,
    "DigiCore": 55,
}

growth_rates = {
    "TechCorp": 1.15,
    "DataFlow": 1.35,
    "CloudBase": 1.45,
    "NetSys": 1.08,
    "CodeLab": 1.50,
    "AppStream": 1.12,
    "ByteWorks": 1.25,
    "DigiCore": 1.40,
}

data = []
for year in years:
    year_idx = years.index(year)
    for company in companies:
        value = base_values[company] * (growth_rates[company] ** year_idx)
        value += np.random.normal(0, value * 0.05)
        data.append({"company": company, "year": year, "revenue": max(10, value)})

df = pd.DataFrame(data)

df["rank"] = df.groupby("year")["revenue"].rank(ascending=False, method="first").astype(int)
df["year_label"] = df["year"].apply(lambda x: f"Year {x}")
df = df.sort_values(["year", "rank"])
df["bar_order"] = df.groupby("year")["revenue"].rank(ascending=True, method="first").astype(int)

# Rank change 2018 → 2024: positive = climbed, negative = fell
ranks = df.pivot_table(index="company", columns="year", values="rank")
rank_chg = (ranks[2018] - ranks[2024]).astype(int).to_dict()


def make_bar_label(row):
    base = f"{row['company']}  ${row['revenue']:.0f}B"
    if row["year"] == 2024:
        chg = rank_chg.get(row["company"], 0)
        if chg >= 3:
            return f"{base}  ↑{chg}"
        elif chg <= -3:
            return f"{base}  ↓{abs(chg)}"
    return base


df["bar_label"] = df.apply(make_bar_label, axis=1)

colors = {company: PALETTE[i] for i, company in enumerate(companies)}

# Plot
plot = (
    ggplot(df, aes(x="bar_order", y="revenue", fill="company"))
    + geom_col(width=0.8, show_legend=False)
    + geom_text(aes(label="bar_label"), ha="left", nudge_y=5, size=12, color=INK_SOFT)
    + coord_flip()
    + facet_wrap("~year_label", ncol=2)
    + scale_fill_manual(values=colors)
    + scale_y_continuous(expand=(0.02, 0, 0.25, 0))
    + labs(
        title="Tech Company Revenue Race · bar-race-animated · python · plotnine · anyplot.ai",
        x="",
        y="Revenue (Billions USD)",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 10),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=24, weight="bold", ha="center", margin={"b": 15}, color=INK),
        axis_title_x=element_text(size=20, margin={"t": 10}, color=INK),
        axis_title_y=element_blank(),
        axis_text_x=element_text(size=16, color=INK_SOFT),
        axis_text_y=element_blank(),
        strip_text=element_text(size=20, weight="bold", color=INK),
        strip_background=element_rect(fill=ELEVATED_BG, color=None),
        panel_border=element_blank(),
        panel_spacing=0.15,
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        plot_margin=0.02,
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300)
