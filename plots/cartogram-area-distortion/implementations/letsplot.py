""" pyplots.ai
cartogram-area-distortion: Cartogram with Area Distortion by Data Value
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 81/100 | Created: 2026-03-13
"""

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_cartesian,
    element_blank,
    element_rect,
    element_text,
    geom_point,
    geom_polygon,
    geom_segment,
    geom_text,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_viridis,
    scale_size,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()

# Data: European countries with population (millions) and GDP per capita (thousands USD)
# Population drives the area distortion; GDP per capita provides color encoding
countries_data = {
    "country": [
        "Germany",
        "France",
        "United Kingdom",
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
    ],
    "population": [
        83.2,
        67.8,
        67.0,
        59.0,
        47.4,
        37.7,
        17.5,
        11.6,
        10.4,
        9.1,
        8.8,
        5.4,
        5.9,
        5.5,
        5.1,
        10.3,
        10.8,
        10.4,
        9.7,
        19.0,
    ],
    "gdp_per_capita": [
        48.7,
        42.3,
        46.1,
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
    ],
    "lon": [
        10.4,
        2.2,
        -1.2,
        12.6,
        -3.7,
        19.1,
        5.3,
        4.4,
        15.0,
        14.6,
        8.2,
        8.5,
        9.5,
        25.7,
        -8.2,
        -8.2,
        15.5,
        23.7,
        19.5,
        25.0,
    ],
    "lat": [
        51.2,
        46.2,
        52.5,
        41.9,
        40.5,
        51.9,
        52.1,
        50.5,
        60.1,
        47.5,
        46.8,
        60.5,
        56.3,
        61.9,
        53.4,
        39.4,
        49.8,
        39.1,
        47.2,
        45.9,
    ],
    "abbr": [
        "DE",
        "FR",
        "UK",
        "IT",
        "ES",
        "PL",
        "NL",
        "BE",
        "SE",
        "AT",
        "CH",
        "NO",
        "DK",
        "FI",
        "IE",
        "PT",
        "CZ",
        "GR",
        "HU",
        "RO",
    ],
}
df = pd.DataFrame(countries_data)

# Mark "small but wealthy" nations for storytelling emphasis
df["highlight"] = (df["population"] < 15) & (df["gdp_per_capita"] > 50)

# Simplified European outline for geographic context (original region reference)
europe_outline = pd.DataFrame(
    {
        "lon": [-12, -10, -5, 0, 5, 10, 15, 20, 25, 30, 32, 30, 28, 25, 28, 32, 30, 25, 20, 15, 10, 5, 0, -5, -10, -12],
        "lat": [43, 36, 36, 38, 37, 36, 36, 35, 36, 38, 42, 45, 45, 50, 55, 60, 65, 70, 68, 62, 58, 52, 50, 48, 44, 43],
        "group": ["outline"] * 26,
    }
)

# Connector lines from highlighted small-wealthy nations to annotation area
highlight_df = df[df["highlight"]].copy()
annotation_data = pd.DataFrame(
    {
        "x": highlight_df["lon"].values,
        "y": highlight_df["lat"].values,
        "xend": [highlight_df["lon"].values[i] + 1.5 for i in range(len(highlight_df))],
        "yend": [highlight_df["lat"].values[i] + 1.8 for i in range(len(highlight_df))],
    }
)

# Build layered plot
plot = (
    ggplot()
    # Faint European coastline outline for geographic reference
    + geom_polygon(
        aes(x="lon", y="lat", group="group"), data=europe_outline, fill="#F0F0F0", color="#C8C8C8", size=0.5, alpha=0.5
    )
    # Cartogram bubbles: area proportional to population, color shows GDP per capita
    + geom_point(
        aes(x="lon", y="lat", size="population", fill="gdp_per_capita"),
        data=df[~df["highlight"]],
        shape=21,
        color="#888888",
        stroke=0.6,
        alpha=0.75,
        tooltips=layer_tooltips()
        .title("@country")
        .line("Population|@population M")
        .line("GDP/capita|$@gdp_per_capita K"),
    )
    # Highlighted small-but-wealthy nations with stronger stroke
    + geom_point(
        aes(x="lon", y="lat", size="population", fill="gdp_per_capita"),
        data=df[df["highlight"]],
        shape=21,
        color="#1A1A1A",
        stroke=1.5,
        alpha=0.95,
        tooltips=layer_tooltips()
        .title("@country")
        .line("Population|@population M")
        .line("GDP/capita|$@gdp_per_capita K"),
    )
    # Small star markers on highlighted countries for visual emphasis
    + geom_point(aes(x="lon", y="lat"), data=highlight_df, shape=8, size=3, color="#1A1A1A")
    + scale_size(range=[12, 30], name="Population\n(millions)", breaks=[5, 20, 40, 80])
    + scale_fill_viridis(option="viridis", name="GDP per Capita\n(thousands USD)")
    # Labels for large countries (population > 30M) - bold, prominent
    + geom_text(
        aes(x="lon", y="lat", label="abbr"), data=df[df["population"] > 30], size=12, color="#1A1A1A", fontface="bold"
    )
    # Labels for medium countries (10-30M)
    + geom_text(
        aes(x="lon", y="lat", label="abbr"),
        data=df[(df["population"] > 10) & (df["population"] <= 30)],
        size=9,
        color="#222222",
    )
    # Labels for small countries (<=10M)
    + geom_text(aes(x="lon", y="lat", label="abbr"), data=df[df["population"] <= 10], size=7, color="#333333")
    # Storytelling annotation: highlight the insight
    + geom_text(
        aes(x="x", y="y"),
        data=pd.DataFrame({"x": [-13.5], "y": [64.5]}),
        label="Small nations,\nhighest GDP/capita",
        size=10,
        color="#2A2A2A",
        fontface="italic",
        hjust=0,
    )
    + geom_text(
        aes(x="x", y="y"),
        data=pd.DataFrame({"x": [-13.5], "y": [62.0]}),
        label="IE  CH  NO  SE  DK  AT  NL  BE  FI",
        size=8,
        color="#555555",
        hjust=0,
    )
    # Separator line under annotation
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"),
        data=pd.DataFrame({"x": [-13.5], "y": [63.2], "xend": [5.0], "yend": [63.2]}),
        color="#AAAAAA",
        size=0.4,
    )
    + labs(
        title="European Population Cartogram \u00b7 cartogram-area-distortion \u00b7 letsplot \u00b7 pyplots.ai",
        subtitle="Bubble size = population  |  Color = GDP per capita  |  Smaller nations often lead in wealth per person",
    )
    + coord_cartesian(xlim=[-15, 33], ylim=[34, 66])
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        plot_subtitle=element_text(size=16, color="#555555"),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
        plot_background=element_rect(fill="white"),
    )
)

# Save
export_ggsave(plot, "plot.png", path=".", scale=3)
export_ggsave(plot, "plot.html", path=".")
