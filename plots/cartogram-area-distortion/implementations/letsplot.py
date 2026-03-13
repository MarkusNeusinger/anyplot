""" pyplots.ai
cartogram-area-distortion: Cartogram with Area Distortion by Data Value
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 76/100 | Created: 2026-03-13
"""

import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

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

# Simplified European outline for geographic context
europe_outline = pd.DataFrame(
    {
        "lon": [-12, -10, -5, 0, 5, 10, 15, 20, 25, 30, 32, 30, 28, 25, 28, 32, 30, 25, 20, 15, 10, 5, 0, -5, -10, -12],
        "lat": [43, 36, 36, 38, 37, 36, 36, 35, 36, 38, 42, 45, 45, 50, 55, 60, 65, 70, 68, 62, 58, 52, 50, 48, 44, 43],
        "group": ["outline"] * 26,
    }
)

# Plot: Dorling cartogram - circles sized by population at geographic positions
plot = (
    ggplot()  # noqa: F405
    # Faint European coastline outline for geographic reference
    + geom_polygon(  # noqa: F405
        aes(x="lon", y="lat", group="group"),  # noqa: F405
        data=europe_outline,
        fill="#F5F5F5",
        color="#D0D0D0",
        size=0.5,
        alpha=0.6,
    )
    # Cartogram bubbles: area proportional to population, color shows GDP per capita
    + geom_point(  # noqa: F405
        aes(x="lon", y="lat", size="population", fill="gdp_per_capita"),  # noqa: F405
        data=df,
        shape=21,
        color="white",
        stroke=1.0,
        alpha=0.88,
        tooltips=layer_tooltips()  # noqa: F405
        .title("@country")
        .line("Population|@population M")
        .line("GDP/capita|$@gdp_per_capita K"),
    )
    + scale_size(  # noqa: F405
        range=[5, 26], name="Population\n(millions)", breaks=[5, 20, 40, 80]
    )
    + scale_fill_gradient(  # noqa: F405
        low="#FFD43B", high="#306998", name="GDP per Capita\n(thousands USD)"
    )
    # Labels for large countries (population > 30M)
    + geom_text(  # noqa: F405
        aes(x="lon", y="lat", label="abbr"),  # noqa: F405
        data=df[df["population"] > 30],
        size=12,
        color="#1A1A1A",
        fontface="bold",
    )
    # Labels for medium countries (10-30M)
    + geom_text(  # noqa: F405
        aes(x="lon", y="lat", label="abbr"),  # noqa: F405
        data=df[(df["population"] > 10) & (df["population"] <= 30)],
        size=9,
        color="#333333",
    )
    + labs(  # noqa: F405
        title="European Population Cartogram \u00b7 cartogram-area-distortion \u00b7 letsplot \u00b7 pyplots.ai"
    )
    + coord_cartesian(xlim=[-15, 33], ylim=[34, 66])  # noqa: F405
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=24, face="bold"),  # noqa: F405
        legend_title=element_text(size=16),  # noqa: F405
        legend_text=element_text(size=14),  # noqa: F405
        axis_title=element_blank(),  # noqa: F405
        axis_text=element_blank(),  # noqa: F405
        axis_ticks=element_blank(),  # noqa: F405
        panel_grid=element_blank(),  # noqa: F405
        plot_background=element_rect(fill="white"),  # noqa: F405
    )
)

# Save
export_ggsave(plot, "plot.png", path=".", scale=3)
export_ggsave(plot, "plot.html", path=".")
