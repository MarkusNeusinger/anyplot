""" anyplot.ai
network-bipartite: Bipartite Network Graph
Library: plotly 7.1.0 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-21
"""

import os

import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
EDGE_COLOR = "rgba(107,106,99,0.40)" if THEME == "light" else "rgba(168,167,159,0.32)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
ARTIST = "Artist"  # role: source
FESTIVAL = "Festival"  # role: target
SETS = "Sets played"  # role: weight

# Data: replace this block with your own edge list, for example df = pd.read_csv("lineups.csv")
lineups = {
    "Luna Vega": {"Sunrise Fields": 3, "Harbor Beats": 2, "Neon Desert": 4, "Alpine Sound": 2},
    "The Marlows": {"Sunrise Fields": 2, "Alpine Sound": 3},
    "DJ Koral": {"Harbor Beats": 4, "Neon Desert": 3, "Bass Garden": 3, "Velvet Nights": 2},
    "Mira Okoye": {"Sunrise Fields": 4, "Velvet Nights": 3, "Alpine Sound": 2},
    "Static Birds": {"Neon Desert": 2, "Bass Garden": 3},
    "Odd Harmony": {"Harbor Beats": 3, "Velvet Nights": 4, "Alpine Sound": 3},
    "Rue Calloway": {"Sunrise Fields": 2, "Neon Desert": 3},
    "Kite & Key": {"Bass Garden": 2, "Harbor Beats": 2},
    "Saoirse Vale": {"Sunrise Fields": 3, "Velvet Nights": 2, "Neon Desert": 3},
    "Tiny Giants": {"Alpine Sound": 4},
    "Ono Prism": {"Bass Garden": 4, "Neon Desert": 2, "Harbor Beats": 3},
    "Wild Orchard": {"Velvet Nights": 3, "Sunrise Fields": 2},
}
df = pd.DataFrame(
    [(artist, festival, sets) for artist, shows in lineups.items() for festival, sets in shows.items()],
    columns=[ARTIST, FESTIVAL, SETS],
)

# Plot: reads only df and the constants above
artists = list(df[ARTIST].unique())
festivals = list(df[FESTIVAL].unique())
artist_degree = df[ARTIST].value_counts().reindex(artists)
festival_degree = df[FESTIVAL].value_counts().reindex(festivals)

# Two columns, nodes spread evenly from top to bottom
artist_y = {name: 1 - i / max(len(artists) - 1, 1) for i, name in enumerate(artists)}
festival_y = {name: 0.92 - 0.84 * i / max(len(festivals) - 1, 1) for i, name in enumerate(festivals)}

fig = go.Figure()

# Edges grouped by weight, so each group gets its own line width
for weight, group in df.groupby(SETS):
    xs, ys = [], []
    for artist, festival in zip(group[ARTIST], group[FESTIVAL], strict=True):
        xs += [0.0, 1.0, None]
        ys += [artist_y[artist], festival_y[festival], None]
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="lines",
            line={"width": 0.5 + weight * 0.45, "color": EDGE_COLOR},
            hoverinfo="skip",
            showlegend=False,
        )
    )


def node_sizes(degree):
    span = max(degree.max() - degree.min(), 1)
    return (9 + (degree - degree.min()) / span * 11).tolist()


fig.add_trace(
    go.Scatter(
        x=[0.0] * len(artists),
        y=[artist_y[a] for a in artists],
        mode="markers+text",
        marker={"size": node_sizes(artist_degree), "color": IMPRINT_PALETTE[0], "line": {"color": PAGE_BG, "width": 1}},
        text=artists,
        textposition="middle left",
        textfont={"size": 11, "color": INK},
        name=ARTIST + "s",
        customdata=artist_degree.tolist(),
        hovertemplate="<b>%{text}</b><br>Plays at %{customdata} festivals<extra></extra>",
    )
)
fig.add_trace(
    go.Scatter(
        x=[1.0] * len(festivals),
        y=[festival_y[f] for f in festivals],
        mode="markers+text",
        marker={
            "size": node_sizes(festival_degree),
            "color": IMPRINT_PALETTE[1],
            "line": {"color": PAGE_BG, "width": 1},
        },
        text=festivals,
        textposition="middle right",
        textfont={"size": 11, "color": INK},
        name=FESTIVAL + "s",
        customdata=festival_degree.tolist(),
        hovertemplate="<b>%{text}</b><br>%{customdata} artists on the lineup<extra></extra>",
    )
)

title = "Festival Lineups · network-bipartite · python · plotly · anyplot.ai"
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    title={"text": title, "font": {"size": 16, "color": INK}, "x": 0.5, "xanchor": "center"},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "font": {"size": 11, "color": INK_SOFT},
        "orientation": "h",
        "x": 0.5,
        "xanchor": "center",
        "y": -0.02,
    },
    xaxis={"range": [-0.5, 1.5], "showgrid": False, "zeroline": False, "showticklabels": False, "showline": False},
    yaxis={"range": [-0.07, 1.1], "showgrid": False, "zeroline": False, "showticklabels": False, "showline": False},
    margin={"l": 20, "r": 20, "t": 50, "b": 40},
)

# Column headers name each set
for x, label, color in [(0.0, ARTIST + "s", IMPRINT_PALETTE[0]), (1.0, FESTIVAL + "s", IMPRINT_PALETTE[1])]:
    fig.add_annotation(
        x=x, y=1.075, text=f"<b>{label}</b>", font={"size": 14, "color": color}, showarrow=False, xref="x", yref="y"
    )

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
