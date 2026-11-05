"""anyplot.ai
pyramid-basic: Basic Pyramid Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-04-29
"""

import math
import os

import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns
AGE_GROUP = "Age Group"  # role: category
MALE = "Male"  # role: value_left
FEMALE = "Female"  # role: value_right

# Data: replace this block with your own table, for example df = pd.read_csv("population.csv")
# Germany-scale population pyramid (~83M total), values in thousands
df = pd.DataFrame(
    {
        AGE_GROUP: ["0–9", "10–19", "20–29", "30–39", "40–49", "50–59", "60–69", "70–79", "80+"],
        MALE: [3800, 4200, 4700, 6300, 6900, 6500, 5800, 3600, 1900],
        FEMALE: [3600, 3900, 4400, 6100, 6700, 6500, 6200, 4600, 3200],
    }
)

# Plot
sides = [(MALE, -1), (FEMALE, 1)]
peak = df[[MALE, FEMALE]].to_numpy().max()
step = 2 * 10 ** (len(str(int(peak))) - 1)  # tick spacing from the data's magnitude
limit = math.ceil(peak * 1.1 / step) * step  # symmetric half-range, rounded up to a tick
tick_vals = [int(k * step) for k in range(-int(limit / step), int(limit / step) + 1)]

fig = go.Figure()
for i, (side, sign) in enumerate(sides):
    fig.add_trace(
        go.Bar(
            y=df[AGE_GROUP],
            x=sign * df[side],
            orientation="h",
            name=side,
            marker_color=IMPRINT_PALETTE[i],
            customdata=df[side],
            hovertemplate=side + "<br>Age: %{y}<br>Population: %{customdata:,}k<extra></extra>",
        )
    )

title = "Population Distribution · pyramid-basic · python · plotly · anyplot.ai"
title_size = round(16 * min(1.0, 67 / len(title)))

fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    title={"text": title, "font": {"size": title_size, "color": INK}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Population (thousands)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickvals": tick_vals,
        "ticktext": [f"{abs(v):,}" for v in tick_vals],
        "range": [-limit, limit],
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": True,
        "zerolinecolor": INK_SOFT,
        "zerolinewidth": 1.5,
        "linecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": AGE_GROUP, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "categoryorder": "array",
        "categoryarray": list(df[AGE_GROUP]),
        "linecolor": INK_SOFT,
    },
    barmode="overlay",
    bargap=0.15,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "font": {"size": 10, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "center",
        "x": 0.5,
    },
    margin={"l": 70, "r": 40, "t": 80, "b": 60},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
