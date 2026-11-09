"""anyplot.ai
violin-grouped-swarm: Grouped Violin Plot with Swarm Overlay
Library: plotly 7.1.0 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-09
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
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TASK = "Task complexity"  # role: category
EXPERTISE = "Expertise level"  # role: group
RESPONSE_TIME = "Response time (ms)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
np.random.seed(42)
scenario = {
    ("Simple", "Novice"): (200, 40),
    ("Simple", "Expert"): (150, 25),
    ("Moderate", "Novice"): (450, 80),
    ("Moderate", "Expert"): (300, 50),
    ("Complex", "Novice"): (800, 150),
    ("Complex", "Expert"): (500, 80),
}
frames = []
for (task, level), (base, spread) in scenario.items():
    times = np.clip(np.random.normal(base, spread, 40), 50, 1200)
    frames.append(pd.DataFrame({TASK: task, EXPERTISE: level, RESPONSE_TIME: times}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
tasks = df[TASK].unique()
levels = df[EXPERTISE].unique()
slot = 0.8 / len(levels)
step = slot / 14
bin_height = (df[RESPONSE_TIME].max() - df[RESPONSE_TIME].min()) / 70

fig = go.Figure()
for j, level in enumerate(levels):
    rows = df[df[EXPERTISE] == level].dropna(subset=[RESPONSE_TIME])
    color = IMPRINT_PALETTE[j]
    position = rows[TASK].map({task: i for i, task in enumerate(tasks)}) + (j - (len(levels) - 1) / 2) * slot

    fig.add_trace(
        go.Violin(
            x=position,
            y=rows[RESPONSE_TIME],
            name=str(level),
            legendgroup=str(level),
            fillcolor=color,
            line={"color": color, "width": 1.5},
            opacity=0.45,
            width=slot * 0.92,
            meanline={"visible": True, "color": INK, "width": 1.5},
            points=False,
            hoverinfo="skip",
        )
    )

    # Violin half-width at each point: Plotly's Silverman KDE; the violins of one trace share a scale,
    # so the trace's highest density peak spans width / 2
    density_at = pd.Series(0.0, index=rows.index)
    peak = 0.0
    for _, values in rows.groupby(TASK)[RESPONSE_TIME]:
        spread = min(values.std(), (values.quantile(0.75) - values.quantile(0.25)) / 1.349)
        bandwidth = max(1.059 * spread * len(values) ** -0.2, 1e-9)
        grid = np.linspace(values.min(), values.max(), 200)
        kernel = np.exp(-0.5 * ((grid[:, None] - values.to_numpy()) / bandwidth) ** 2)
        density = kernel.sum(axis=1) / (len(values) * bandwidth)
        density_at[values.index] = np.interp(values, grid, density)
        peak = max(peak, density.max())
    local_half = slot * 0.46 * density_at / peak

    # Swarm: points that share a value band stack outward from the violin's center, alternating sides,
    # with the row spacing shrunk where needed so the widest point stays inside the violin outline
    band = ((rows[RESPONSE_TIME] - df[RESPONSE_TIME].min()) // bin_height).astype(int)
    ordered = rows.assign(band=band).sort_values(RESPONSE_TIME)
    rank = ordered.groupby([TASK, "band"]).cumcount()
    half = (rank + 1) // 2
    row = [ordered[TASK], ordered["band"]]
    room = local_half.reindex(ordered.index).groupby(row).transform("min") * 0.75
    fit = np.minimum(step, room / half.groupby(row).transform("max").clip(lower=1))
    swarm_offset = half * np.where(rank % 2 == 0, 1, -1) * fit

    fig.add_trace(
        go.Scatter(
            x=position + swarm_offset.reindex(rows.index),
            y=rows[RESPONSE_TIME],
            mode="markers",
            marker={"size": 5.5, "color": color, "opacity": 0.9, "line": {"width": 0.6, "color": PAGE_BG}},
            name=str(level),
            legendgroup=str(level),
            showlegend=False,
            customdata=rows[TASK],
            hovertemplate=f"{level}<br>%{{customdata}}<br>{RESPONSE_TIME}: %{{y:.0f}}<extra></extra>",
        )
    )

# Style
title = "violin-grouped-swarm · python · plotly · anyplot.ai"
fig.update_layout(
    autosize=False,
    title={"text": title, "font": {"size": round(16 * min(1.0, 67 / len(title))), "color": INK}, "x": 0.5},
    xaxis={
        "title": {"text": TASK, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickmode": "array",
        "tickvals": list(range(len(tasks))),
        "ticktext": [str(task) for task in tasks],
        "range": [-0.6, len(tasks) - 0.4],
        "showgrid": False,
        "zeroline": False,
        "linecolor": INK_SOFT,
        "ticks": "",
    },
    yaxis={
        "title": {"text": RESPONSE_TIME, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": False,
        "showline": False,
    },
    legend={
        "title": {"text": EXPERTISE, "font": {"size": 10, "color": INK}},
        "font": {"size": 10, "color": INK_SOFT},
        "x": 0.02,
        "y": 0.98,
        "xanchor": "left",
        "yanchor": "top",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 70, "r": 30, "t": 60, "b": 55},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
