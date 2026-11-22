"""anyplot.ai
violin-swarm: Violin Plot with Overlaid Swarm Points
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-11-22
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import gaussian_kde


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.12)" if THEME == "light" else "rgba(240,239,232,0.12)"

# Imprint palette: violin fill takes position 1, swarm points the contrasting position 2
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
VIOLIN_WIDTH = 0.84  # width of the widest violin, in category-spacing units
MARKER_PX = 8  # swarm marker diameter in CSS px of the 800 x 450 layout

# Columns: set these to your table's column names
CLINICAL_GROUP = "Clinical group"  # role: category
GLUCOSE = "Fasting glucose (mg/dL)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("biomarkers.csv")
np.random.seed(42)
n_per_group = 60
glucose_by_group = {
    "Healthy": np.random.normal(90, 6, n_per_group),
    "Pre-diabetic": 100 + np.random.gamma(2.0, 5.0, n_per_group),
    "Type 2, untreated": np.concatenate([np.random.normal(150, 12, 38), np.random.normal(205, 15, 22)]),
    "Type 2, treated": np.random.normal(122, 10, n_per_group),
}
df = pd.DataFrame(
    {
        CLINICAL_GROUP: np.repeat(list(glucose_by_group), n_per_group),
        GLUCOSE: np.concatenate(list(glucose_by_group.values())),
    }
)

# Plot: reads only df and the constants above
groups = list(df[CLINICAL_GROUP].unique())
width_px, height_px = 800, 450
plot_w_px = width_px - 80 - 40  # inner plot size from the pinned margins below
plot_h_px = height_px - 70 - 60
y_span = df[GLUCOSE].max() - df[GLUCOSE].min()
y_pad = y_span * 0.06
px_per_x = plot_w_px / len(groups)
px_per_y = plot_h_px / (y_span + 2 * y_pad)

fig = go.Figure()
for i, group in enumerate(groups):
    values = df.loc[df[CLINICAL_GROUP] == group, GLUCOSE].dropna().to_numpy(dtype=float)

    # Violin: translucent fill, ends at the data range
    fig.add_trace(
        go.Violin(
            x0=i,
            y=values,
            width=VIOLIN_WIDTH,
            spanmode="hard",
            scalemode="width",
            points=False,
            showlegend=False,
            fillcolor="rgba(0,158,115,0.35)",
            line={"color": IMPRINT_PALETTE[0], "width": 1.5},
            hoverinfo="skip",
        )
    )

    # Swarm: each point sits at its value; only the sideways offset is laid out, nearest-to-centre first
    kde = gaussian_kde(values)
    ys = np.linspace(values.min(), values.max(), 200)
    half_width = VIOLIN_WIDTH / 2 * kde(values) / kde(ys).max()
    placed_x, placed_y = [], []
    xs = np.zeros(len(values))
    for k in np.argsort(values):
        step = 0.0
        while True:
            candidates = [0.0] if step == 0 else [step, -step]
            free = [
                c
                for c in candidates
                if all(
                    np.hypot((c - px) * px_per_x, (values[k] - py) * px_per_y) >= MARKER_PX
                    for px, py in zip(placed_x, placed_y, strict=True)
                )
            ]
            if free:
                xs[k] = free[0]
                break
            step += 0.5 * MARKER_PX / px_per_x
        placed_x.append(xs[k])
        placed_y.append(values[k])
    xs = np.clip(xs, -0.9 * half_width, 0.9 * half_width)

    fig.add_trace(
        go.Scatter(
            x=i + xs,
            y=values,
            mode="markers",
            marker={
                "size": MARKER_PX,
                "color": IMPRINT_PALETTE[1],
                "opacity": 0.9,
                "line": {"width": 0.8, "color": PAGE_BG},
            },
            hovertemplate=f"<b>{group}</b><br>{GLUCOSE}: %{{y:.1f}}<extra></extra>",
            showlegend=False,
        )
    )

# Style
fig.update_layout(
    title={"text": "violin-swarm · python · plotly · anyplot.ai", "font": {"size": 16, "color": INK}, "x": 0.5},
    xaxis={
        "title": {"text": CLINICAL_GROUP, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickvals": list(range(len(groups))),
        "ticktext": groups,
        "range": [-0.6, len(groups) - 0.4],
        "showgrid": False,
        "zeroline": False,
        "showline": True,
        "linecolor": INK_SOFT,
        "ticks": "",
    },
    yaxis={
        "title": {"text": GLUCOSE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "range": [df[GLUCOSE].min() - y_pad, df[GLUCOSE].max() + y_pad],
        "gridcolor": GRID,
        "zeroline": False,
        "showline": True,
        "linecolor": INK_SOFT,
        "ticks": "",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    showlegend=False,
    autosize=False,
    margin={"l": 80, "r": 40, "t": 70, "b": 60},
    width=width_px,
    height=height_px,
)

# Save
fig.write_image(f"plot-{THEME}.png", width=width_px, height=height_px, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
