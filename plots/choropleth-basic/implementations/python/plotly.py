"""anyplot.ai
choropleth-basic: Choropleth Map with Regional Coloring
Library: plotly 6.7.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-15
"""

import os

import pandas as pd
import plotly.express as px


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
NO_DATA = "#CFCDC4" if THEME == "light" else "#3A3A35"  # gray for regions without a value

# Imprint palette: sequential scale from brand green to blue (single-polarity data)
imprint_seq = [[0.0, "#009E73"], [1.0, "#4467A3"]]

# Columns: set these to your table's column names
COUNTRY = "Country (ISO-3)"  # role: region_id
LITERACY = "Adult literacy rate (%)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("literacy.csv")
# Adult literacy rate by African country (approximate, latest available years).
# Eritrea, South Sudan and Somalia are left out on purpose: they show as no data.
df = pd.DataFrame(
    {
        COUNTRY: [
            "DZA", "AGO", "BEN", "BWA", "BFA", "BDI", "CMR", "CPV", "CAF", "TCD",
            "COM", "COG", "COD", "CIV", "DJI", "EGY", "GNQ", "SWZ", "ETH", "GAB",
            "GMB", "GHA", "GIN", "GNB", "KEN", "LSO", "LBR", "LBY", "MDG", "MWI",
            "MLI", "MRT", "MUS", "MAR", "MOZ", "NAM", "NER", "NGA", "RWA", "SEN",
            "SLE", "ZAF", "SDN", "TZA", "TGO", "TUN", "UGA", "ZMB", "ZWE",
        ],
        LITERACY: [
            81, 72, 46, 89, 47, 76, 78, 87, 37, 27,
            62, 80, 80, 89, 70, 74, 95, 88, 52, 85,
            59, 80, 45, 46, 82, 82, 48, 91, 77, 68,
            31, 67, 92, 77, 63, 92, 37, 62, 76, 58,
            48, 95, 61, 82, 67, 83, 79, 87, 90,
        ],
    }
)  # fmt: skip

# Plot: reads only df and the constants above
fig = px.choropleth(
    df,
    locations=COUNTRY,
    color=LITERACY,
    color_continuous_scale=imprint_seq,
    range_color=(df[LITERACY].min(), df[LITERACY].max()),
    scope="africa",
    projection="natural earth",
)

fig.update_geos(
    showland=True,
    landcolor=NO_DATA,
    showocean=False,
    showlakes=False,
    showcountries=True,
    countrycolor=PAGE_BG,
    countrywidth=0.8,
    showcoastlines=True,
    coastlinecolor=PAGE_BG,
    coastlinewidth=0.8,
    showframe=False,
    bgcolor=PAGE_BG,
)

# Thin page-colored outlines keep neighbours of similar shade apart without competing with the fills
fig.update_traces(marker_line_width=0.8, marker_line_color=PAGE_BG)

fig.update_layout(
    autosize=False,
    width=600,
    height=600,
    margin=dict(l=20, r=20, t=70, b=20),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    title=dict(
        text="choropleth-basic · python · plotly · anyplot.ai", font=dict(size=20, color=INK), x=0.5, xanchor="center"
    ),
    coloraxis_colorbar=dict(
        title=dict(text=LITERACY, font=dict(size=14, color=INK)),
        tickfont=dict(size=13, color=INK_SOFT),
        thickness=18,
        len=0.7,
        outlinewidth=0,
    ),
)

fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
