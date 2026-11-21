"""anyplot.ai
map-tilegrid: Tile Grid Map for Equal-Area Geographic Comparison
Library: plotly 6.7.0 | Python 3.13.13
Quality: 89/100 | Created: 2026-05-14
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Sequential Imprint colormap for unipolar data
imprint_seq = [[0.0, IMPRINT_PALETTE[0]], [1.0, IMPRINT_PALETTE[2]]]

# Columns: set these to your table's column names
REGION = "State"  # role: region
VALUE = "Renewable electricity share (%)"  # role: value
ROW = "Grid row"  # role: row
COL = "Grid column"  # role: col

# Data: replace this block with your own table, for example df = pd.read_csv("regions.csv")
# US state tile grid (row 0 = north, col 0 = west) and a synthetic renewable share per state
state_grid = {
    "AK": (0, 0), "ME": (0, 11),
    "VT": (1, 10), "NH": (1, 11),
    "WA": (2, 0), "ID": (2, 1), "MT": (2, 2), "ND": (2, 3), "MN": (2, 4), "WI": (2, 5),
    "MI": (2, 6), "NY": (2, 9), "MA": (2, 10), "RI": (2, 11),
    "OR": (3, 0), "NV": (3, 1), "WY": (3, 2), "SD": (3, 3), "IA": (3, 4), "IL": (3, 5),
    "IN": (3, 6), "OH": (3, 7), "PA": (3, 8), "NJ": (3, 10), "CT": (3, 11),
    "CA": (4, 0), "UT": (4, 1), "CO": (4, 2), "NE": (4, 3), "MO": (4, 4), "KY": (4, 5),
    "WV": (4, 6), "VA": (4, 7), "MD": (4, 8), "DE": (4, 10),
    "AZ": (5, 1), "NM": (5, 2), "KS": (5, 3), "OK": (5, 4), "TN": (5, 5), "NC": (5, 7),
    "SC": (5, 8), "DC": (5, 9),
    "TX": (6, 3), "LA": (6, 4), "AR": (6, 5), "MS": (6, 6), "AL": (6, 7), "GA": (6, 8),
    "FL": (6, 9),
    "HI": (7, 1),
}  # fmt: skip
renewable_base = {
    "WA": 82, "OR": 70, "ID": 75, "MT": 68, "VT": 71, "ME": 65, "SD": 79, "ND": 65,
    "IA": 60, "CA": 55, "HI": 48, "KS": 42, "OK": 40, "NM": 30, "NY": 32, "NE": 32,
    "CO": 33, "MN": 28, "AK": 28, "TX": 27, "MA": 26, "NH": 25, "TN": 25, "UT": 22,
    "FL": 22, "SC": 22, "AL": 20, "VA": 20, "WI": 20, "RI": 20, "MD": 19, "CT": 18,
    "AZ": 18, "NC": 18, "IL": 18, "MI": 17, "MO": 17, "NV": 36, "NJ": 16, "GA": 16,
    "AR": 16, "OH": 16, "PA": 14, "WY": 14, "MS": 13, "IN": 13, "DE": 12, "KY": 11,
    "LA": 12, "DC": 5, "WV": 8,
}  # fmt: skip
rng = np.random.default_rng(42)
df = pd.DataFrame(
    {
        REGION: list(state_grid),
        VALUE: [float(np.clip(renewable_base[s] + rng.uniform(-2, 2), 5, 90)) for s in state_grid],
        ROW: [rc[0] for rc in state_grid.values()],
        COL: [rc[1] for rc in state_grid.values()],
    }
)

# Plot: reads only df and the constants above
z = df.pivot_table(index=ROW, columns=COL, values=VALUE, sort=True)
names = df.pivot_table(index=ROW, columns=COL, values=REGION, aggfunc="first")
zmin, zmax = df[VALUE].min(), df[VALUE].max()


def label_color(value):
    """White on dark tiles, dark ink on light ones, chosen by the tile's relative luminance."""
    t = (value - zmin) / (zmax - zmin)
    lo = [int(imprint_seq[0][1][i : i + 2], 16) for i in (1, 3, 5)]
    hi = [int(imprint_seq[1][1][i : i + 2], 16) for i in (1, 3, 5)]
    rgb = [(a + (b - a) * t) / 255 for a, b in zip(lo, hi, strict=True)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    lum = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    return "#1A1A17" if lum > 0.3 else "#FFFFFF"


annotations = [
    {
        "x": r[COL],
        "y": r[ROW],
        "text": f"<b>{r[REGION]}</b>",
        "font": {"size": 12, "color": label_color(r[VALUE])},
        "showarrow": False,
    }
    for _, r in df.iterrows()
]

top, bottom = df.loc[df[VALUE].idxmax()], df.loc[df[VALUE].idxmin()]
subtitle = f"{top[REGION]} leads at {top[VALUE]:.0f}% while {bottom[REGION]} trails at {bottom[VALUE]:.0f}%"
title = "US Renewable Energy Share · map-tilegrid · python · plotly · anyplot.ai"

fig = go.Figure(
    go.Heatmap(
        z=z.to_numpy(),
        x=z.columns,
        y=z.index,
        text=names.to_numpy(),
        hovertemplate="<b>%{text}</b><br>" + VALUE + ": %{z:.1f}<extra></extra>",
        colorscale=imprint_seq,
        zmin=zmin,
        zmax=zmax,
        xgap=3,
        ygap=3,
        colorbar={
            "title": {"text": VALUE, "font": {"size": 12, "color": INK}, "side": "right"},
            "tickfont": {"size": 11, "color": INK_SOFT},
            "outlinewidth": 0,
            "thickness": 14,
            "len": 0.7,
        },
        hoverlabel={"bgcolor": PAGE_BG, "font": {"size": 12, "color": INK}, "bordercolor": INK_SOFT},
    )
)

# Style
axis_off = {"showgrid": False, "showticklabels": False, "showline": False, "zeroline": False, "ticks": ""}
fig.update_layout(
    autosize=False,
    title={
        "text": title,
        "subtitle": {"text": subtitle, "font": {"size": 12, "color": INK_SOFT}},
        "font": {"size": 15, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    xaxis=axis_off,
    yaxis={**axis_off, "autorange": "reversed", "scaleanchor": "x", "scaleratio": 1},
    annotations=annotations,
    margin={"l": 40, "r": 40, "t": 80, "b": 30},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
