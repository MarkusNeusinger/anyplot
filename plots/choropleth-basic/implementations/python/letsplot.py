""" pyplots.ai
choropleth-basic: Choropleth Map with Regional Coloring
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave
from lets_plot.geo_data import geocode_countries


LetsPlot.setup_html()  # noqa: F405

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
        color="#404040",
        size=0.6,
        alpha=0.95,
    )
    + scale_fill_gradient(  # noqa: F405
        low="#FFD43B", high="#306998", name="GDP per Capita\n(thousands USD)", na_value="#E0E0E0"
    )
    + labs(title="European GDP per Capita · choropleth-basic · letsplot · pyplots.ai")  # noqa: F405
    + coord_cartesian(xlim=[-12, 32], ylim=[35, 71])  # noqa: F405
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=26, face="bold"),  # noqa: F405
        legend_title=element_text(size=18),  # noqa: F405
        legend_text=element_text(size=16),  # noqa: F405
        legend_position=[0.88, 0.35],
        axis_title=element_blank(),  # noqa: F405
        axis_text=element_blank(),  # noqa: F405
        axis_ticks=element_blank(),  # noqa: F405
        panel_grid=element_blank(),  # noqa: F405
        plot_background=element_rect(fill="white"),  # noqa: F405
    )
)

# Save as PNG (scale 3x for 4800 × 2700 px)
export_ggsave(plot, "plot.png", path=".", scale=3)

# Save interactive HTML
export_ggsave(plot, "plot.html", path=".")
