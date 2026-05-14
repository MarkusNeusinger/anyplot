"""anyplot.ai
map-tilegrid: Tile Grid Map for Equal-Area Geographic Comparison
Library: altair | Python 3.13
Quality: pending | Created: 2026-05-14
"""

import os

import altair as alt
import pandas as pd


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data — US states tile grid positions (row 0 = north) and renewable energy share (%)
state_grid = [
    ("ME", 0, 11),
    ("NH", 1, 10),
    ("VT", 1, 9),
    ("WA", 2, 0),
    ("MT", 2, 1),
    ("ND", 2, 2),
    ("MN", 2, 3),
    ("WI", 2, 4),
    ("MI", 2, 6),
    ("NY", 2, 8),
    ("MA", 2, 10),
    ("RI", 2, 11),
    ("OR", 3, 0),
    ("ID", 3, 1),
    ("WY", 3, 2),
    ("SD", 3, 3),
    ("IA", 3, 4),
    ("IL", 3, 5),
    ("IN", 3, 6),
    ("OH", 3, 7),
    ("PA", 3, 8),
    ("NJ", 3, 9),
    ("CT", 3, 10),
    ("CA", 4, 0),
    ("NV", 4, 1),
    ("CO", 4, 2),
    ("NE", 4, 3),
    ("MO", 4, 4),
    ("KY", 4, 5),
    ("WV", 4, 6),
    ("VA", 4, 7),
    ("MD", 4, 8),
    ("DE", 4, 9),
    ("AZ", 5, 1),
    ("UT", 5, 2),
    ("KS", 5, 3),
    ("AR", 5, 4),
    ("TN", 5, 5),
    ("NC", 5, 6),
    ("SC", 5, 7),
    ("DC", 5, 8),
    ("NM", 6, 2),
    ("OK", 6, 3),
    ("LA", 6, 4),
    ("MS", 6, 5),
    ("AL", 6, 6),
    ("GA", 6, 7),
    ("FL", 6, 8),
    ("AK", 7, 0),
    ("HI", 7, 1),
    ("TX", 7, 3),
]

renewable_share = {
    "AK": 29,
    "AL": 9,
    "AR": 12,
    "AZ": 20,
    "CA": 36,
    "CO": 34,
    "CT": 6,
    "DC": 3,
    "DE": 12,
    "FL": 14,
    "GA": 12,
    "HI": 37,
    "IA": 59,
    "ID": 57,
    "IL": 13,
    "IN": 10,
    "KS": 43,
    "KY": 9,
    "LA": 9,
    "MA": 18,
    "MD": 14,
    "ME": 79,
    "MI": 13,
    "MN": 28,
    "MO": 12,
    "MS": 5,
    "MT": 50,
    "NC": 14,
    "ND": 34,
    "NE": 24,
    "NH": 27,
    "NJ": 10,
    "NM": 31,
    "NV": 29,
    "NY": 32,
    "OH": 9,
    "OK": 38,
    "OR": 67,
    "PA": 12,
    "RI": 23,
    "SC": 7,
    "SD": 81,
    "TN": 17,
    "TX": 28,
    "UT": 24,
    "VA": 16,
    "VT": 82,
    "WA": 76,
    "WI": 13,
    "WV": 7,
    "WY": 18,
}

df = pd.DataFrame(state_grid, columns=["state", "row", "col"])
df["value"] = df["state"].map(renewable_share)

# Plot
x_enc = alt.X("col:O", scale=alt.Scale(paddingInner=0.04, paddingOuter=0), axis=None)
y_enc = alt.Y("row:O", scale=alt.Scale(paddingInner=0.04, paddingOuter=0), axis=None)

base = alt.Chart(df)

tiles = base.mark_rect().encode(
    x=x_enc,
    y=y_enc,
    color=alt.Color(
        "value:Q",
        scale=alt.Scale(scheme="viridis"),
        legend=alt.Legend(
            title="Renewables %", titleFontSize=18, labelFontSize=16, gradientLength=280, gradientThickness=18
        ),
    ),
    tooltip=[alt.Tooltip("state:N", title="State"), alt.Tooltip("value:Q", title="Renewable %", format=".0f")],
)

labels = base.mark_text(fontSize=22, fontWeight="bold").encode(
    x=x_enc,
    y=y_enc,
    text="state:N",
    color=alt.condition("datum.value > 50", alt.value("#1A1A17"), alt.value("#F0EFE8")),
)

chart = (
    alt.layer(tiles, labels)
    .properties(
        width=1600,
        height=900,
        title="US Renewable Energy Share · map-tilegrid · altair · anyplot.ai",
        background=PAGE_BG,
    )
    .configure_title(color=INK, fontSize=28, anchor="middle", offset=16)
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
