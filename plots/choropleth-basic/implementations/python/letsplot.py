""" anyplot.ai
choropleth-basic: Choropleth Map with Regional Coloring
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 79/100 | Updated: 2026-05-15
"""

import os

import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave
from lets_plot.geo_data import geocode_countries


LetsPlot.setup_html()  # noqa: F405

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data: GDP per capita by European countries (in thousands USD)
data = {
    "country": [
        "Germany",
        "France",
        "Italy",
        "Spain",
        "Poland",
        "Netherlands",
        "Belgium",
        "Sweden",
        "Austria",
        "Switzerland",
        "Norway",
        "Denmark",
        "Finland",
        "Ireland",
        "Portugal",
        "Czech Republic",
        "Greece",
        "Hungary",
        "Romania",
        "Bulgaria",
        "Slovakia",
        "Croatia",
        "Slovenia",
        "Lithuania",
        "Latvia",
        "Estonia",
        "Luxembourg",
    ],
    "gdp_per_capita": [
        48.7,
        42.3,
        34.5,
        30.1,
        17.8,
        57.0,
        51.2,
        55.7,
        53.3,
        92.4,
        89.2,
        67.8,
        53.2,
        100.2,
        24.5,
        27.0,
        20.2,
        18.8,
        15.1,
        13.9,
        21.3,
        18.5,
        28.4,
        24.0,
        21.8,
        28.3,
        126.4,
    ],
}
df = pd.DataFrame(data)

# Get country boundaries
countries = geocode_countries(df["country"].tolist()).get_boundaries()
df_geo = countries.merge(df, left_on="found name", right_on="country", how="left")

# Create choropleth map with European focus
plot = (
    ggplot()  # noqa: F405
    + geom_map(  # noqa: F405
        aes(fill="gdp_per_capita"),  # noqa: F405
        data=df,
        map=df_geo,
        map_join=["country", "found name"],
        color=INK_SOFT,
        size=0.6,
        alpha=0.95,
    )
    + scale_fill_viridis(name="GDP per Capita\n(thousands USD)", na_value="#E0E0E0")  # noqa: F405
    + labs(title="choropleth-basic · letsplot · anyplot.ai")  # noqa: F405
    + coord_cartesian(xlim=[-12, 32], ylim=[35, 71])  # noqa: F405
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=24, color=INK),  # noqa: F405
        legend_title=element_text(size=18, color=INK),  # noqa: F405
        legend_text=element_text(size=18, color=INK_SOFT),  # noqa: F405
        legend_position=[0.82, 0.25],
        axis_title=element_blank(),  # noqa: F405
        axis_text=element_blank(),  # noqa: F405
        axis_ticks=element_blank(),  # noqa: F405
        panel_grid=element_blank(),  # noqa: F405
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),  # noqa: F405
    )
)

# Save as PNG (scale 3x for 4800 × 2700 px)
export_ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)

# Save interactive HTML
export_ggsave(plot, f"plot-{THEME}.html", path=".")
