"""anyplot.ai
bump-basic: Basic Bump Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-29
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
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions, one per entity in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
LANGUAGE = "Language"  # role: entity
YEAR = "Survey year"  # role: period
RANK = "Popularity rank"  # role: rank

# Data: replace this block with your own table, for example df = pd.read_csv("rankings.csv")
years = ["2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024"]
ranks_by_language = {
    "Python": [3, 3, 2, 1, 1, 1, 1, 1],
    "JavaScript": [1, 1, 1, 2, 2, 2, 3, 2],
    "Java": [2, 2, 3, 3, 3, 3, 2, 3],
    "C#": [4, 4, 4, 4, 5, 5, 6, 6],
    "Go": [5, 5, 5, 5, 4, 4, 5, 5],
    "Rust": [6, 6, 6, 6, 6, 6, 4, 4],
}
df = pd.DataFrame(
    {
        LANGUAGE: [lang for lang, ranks in ranks_by_language.items() for _ in ranks],
        YEAR: years * len(ranks_by_language),
        RANK: [rank for ranks in ranks_by_language.values() for rank in ranks],
    }
)

# Plot: reads only df and the constants above
fig = go.Figure()
for i, (lang, rows) in enumerate(df.groupby(LANGUAGE, sort=False)):
    color = IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)]
    fig.add_trace(
        go.Scatter(
            x=rows[YEAR],
            y=rows[RANK],
            mode="lines+markers",
            name=str(lang),
            line={"width": 4, "color": color},
            marker={"size": 13, "color": color, "line": {"width": 2, "color": PAGE_BG}},
            showlegend=False,
            hovertemplate=f"<b>{lang}</b><br>%{{x}}: #%{{y}}<extra></extra>",
        )
    )
    # Direct label at the end of the line
    last = rows.iloc[-1]
    fig.add_annotation(
        x=df[YEAR].nunique() - 1,  # category index: annotations read strings as numbers
        y=last[RANK],
        text=f"  <b>{lang}</b>",
        showarrow=False,
        xanchor="left",
        font={"size": 12, "color": INK},
    )

title = "bump-basic · python · plotly · anyplot.ai"
fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    title={"text": title, "font": {"size": 16, "color": INK}, "x": 0.02, "xanchor": "left"},
    xaxis={
        "type": "category",
        "title": {"text": YEAR, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": False,
        "linecolor": INK_SOFT,
        "tickcolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": RANK, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "autorange": "reversed",
        "tickmode": "linear",
        "tick0": 1,
        "dtick": 1,
        "gridcolor": GRID,
        "gridwidth": 1,
        "showgrid": True,
        "zeroline": False,
        "linecolor": INK_SOFT,
    },
    margin={"r": 120, "t": 60, "l": 80, "b": 60},
    hoverlabel={"font_size": 12, "bgcolor": ELEVATED_BG, "bordercolor": INK_SOFT},
    font={"color": INK},
)

# PNG: static export at 3200 x 1800
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)

# HTML: add a range slider for exploring periods (interactive only)
fig.update_xaxes(rangeslider={"visible": True, "bgcolor": ELEVATED_BG, "bordercolor": INK_SOFT, "thickness": 0.06})
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn", config={"scrollZoom": True, "displayModeBar": True})
