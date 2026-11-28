"""anyplot.ai
histogram-epidemic: Epidemic Curve (Epi Curve)
Library: plotly 6.7.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-06-02
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette — theme-independent data colors
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
ONSET_DATE = "Week of Symptom Onset"  # role: onset_date
CASE_COUNT = "Weekly New Cases"  # role: case_count
CASE_TYPE = "Case classification"  # role: case_type
EVENTS = "Intervention"  # role: events

# Data: replace this block with your own tables, for example df = pd.read_csv("cases.csv")
# Two influenza-like illness seasons over 104 weeks (weekly bins): winter peaks, low summer baseline
np.random.seed(17)
weeks = pd.date_range("2022-09-05", periods=104, freq="W-MON")
t = np.arange(len(weeks))
season1 = 320 * np.exp(-0.5 * ((t - 20) / 7) ** 2)
season2 = 275 * np.exp(-0.5 * ((t - 72) / 8) ** 2)
endemic = 35 + 12 * np.sin(2 * np.pi * t / 52 - np.pi / 2)
base_cases = np.maximum(0, season1 + season2 + endemic + np.random.poisson(8, len(weeks)))

shares = {"Confirmed": 0.58, "Probable": 0.30, "Suspect": 0.12}
df = pd.concat(
    [
        pd.DataFrame({ONSET_DATE: weeks, CASE_TYPE: kind, CASE_COUNT: np.round(base_cases * share).astype(int)})
        for kind, share in shares.items()
    ],
    ignore_index=True,
)

# Vaccination campaign rollouts before each season peak, marked on the week they start (NaN elsewhere)
df[EVENTS] = np.where(df[ONSET_DATE].isin(weeks[[13, 60]]), "Flu vaccine rollout", None)

# Plot
table = df.pivot_table(index=ONSET_DATE, columns=CASE_TYPE, values=CASE_COUNT, aggfunc="sum", sort=False)
cumulative = table.sum(axis=1).cumsum()
n_types = len(table.columns)
palette = [IMPRINT_PALETTE[k % len(IMPRINT_PALETTE)] for k in range(n_types + 1 + int(df[EVENTS].notna().sum()))]

fig = go.Figure()
for i, kind in enumerate(table.columns):
    fig.add_trace(
        go.Bar(
            x=table.index,
            y=table[kind],
            name=str(kind),
            marker={"color": palette[i], "line": {"color": PAGE_BG, "width": 0.4}},
            hovertemplate="%{y} cases<extra></extra>",
        )
    )

# Cumulative burden line on secondary y-axis
fig.add_trace(
    go.Scatter(
        x=cumulative.index,
        y=cumulative,
        name="Cumulative",
        yaxis="y2",
        mode="lines",
        line={"color": palette[n_types], "width": 2.5},
        hovertemplate="%{y:,} total<extra></extra>",
    )
)

# Intervention annotation lines
events = df.dropna(subset=[EVENTS]).drop_duplicates(ONSET_DATE)
for j, (_, evt) in enumerate(events.iterrows()):
    evt_color = palette[n_types + 1 + j]
    fig.add_shape(
        type="line",
        x0=evt[ONSET_DATE],
        x1=evt[ONSET_DATE],
        y0=0,
        y1=0.78,
        yref="paper",
        line={"color": evt_color, "width": 2, "dash": "dashdot"},
    )
    fig.add_annotation(
        x=evt[ONSET_DATE],
        y=0.85,
        yref="paper",
        text=f"<b>{evt[EVENTS]}</b>",
        showarrow=True,
        arrowhead=0,
        arrowwidth=1.5,
        arrowcolor=evt_color,
        ax=0,
        ay=-30,
        font={"size": 10, "color": evt_color, "family": "Arial"},
        align="center",
        bgcolor=ELEVATED_BG,
        bordercolor=evt_color,
        borderwidth=1,
        borderpad=3,
    )

fig.update_layout(
    autosize=False,
    title={
        "text": "histogram-epidemic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK, "family": "Arial"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.95,
        "yanchor": "top",
    },
    hovermode="x unified",
    xaxis={
        "title": {"text": ONSET_DATE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickformat": "%b %Y",
        "dtick": "M3",
        "tickangle": 0,
        "showgrid": False,
        "zeroline": False,
        "showline": False,
        "spikemode": "across",
        "spikethickness": 1,
        "spikecolor": INK_SOFT,
        "spikedash": "dot",
    },
    yaxis={
        "title": {"text": CASE_COUNT, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": False,
        "showline": False,
        "rangemode": "tozero",
    },
    yaxis2={
        "title": {"text": "Cumulative Cases", "font": {"size": 12, "color": palette[n_types]}},
        "tickfont": {"size": 10, "color": palette[n_types]},
        "overlaying": "y",
        "side": "right",
        "showgrid": False,
        "zeroline": False,
        "rangemode": "tozero",
    },
    barmode="stack",
    bargap=0.15,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK, "family": "Arial"},
    legend={
        "font": {"size": 10, "color": INK_SOFT},
        "orientation": "h",
        "traceorder": "normal",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "center",
        "x": 0.5,
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    margin={"l": 80, "r": 80, "t": 90, "b": 70},
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
