"""anyplot.ai
violin-split: Split Violin Plot
Library: plotly 7.1.0 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions, one per split group in order (first is always #009E73)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
JOB = "Job Category"  # role: category
SALARY = "Annual Salary ($)"  # role: value
GENDER = "Gender"  # role: split_group

# Data: replace this block with your own table, for example df = pd.read_csv("salaries.csv")
np.random.seed(42)
n_per_group = 100
salary_mixtures = {  # (mean, sd) of each mixture component; components share the rows equally
    "Software Engineering": {"Male": [(95000, 18000), (135000, 15000)], "Female": [(92000, 17000), (132000, 16000)]},
    "Product Management": {"Male": [(105000, 20000)], "Female": [(101000, 21000)]},
    "Sales": {
        "Male": [(60000, 12000), (95000, 15000), (140000, 18000)],
        "Female": [(58000, 13000), (92000, 16000), (135000, 19000)],
    },
    "Operations": {"Male": [(72000, 16000)], "Female": [(68000, 17000)]},
}
frames = []
for job, genders in salary_mixtures.items():
    for gender, components in genders.items():
        n = n_per_group // len(components)
        # Truncated normal by rejection: oversample, keep draws inside the pay band, take the first n
        draws = [np.random.normal(mean, sd, 3 * n) for mean, sd in components]
        salaries = np.concatenate([d[(d >= 40000) & (d <= 200000)][:n] for d in draws])
        frames.append(pd.DataFrame({JOB: job, SALARY: salaries, GENDER: gender}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
fig = go.Figure()
for i, (gender, rows) in enumerate(df.groupby(GENDER, sort=False)):
    fig.add_trace(
        go.Violin(
            x=rows[JOB],
            y=rows[SALARY],
            name=str(gender),
            side="negative" if i % 2 == 0 else "positive",
            line=dict(color=IMPRINT_PALETTE[i], width=1.5),
            fillcolor=IMPRINT_PALETTE[i],
            opacity=0.75,
            meanline=dict(visible=True, color=INK, width=6),
            box=dict(visible=True, width=0.25, fillcolor=ELEVATED_BG, line=dict(color=INK_SOFT, width=4)),
            points=False,
            spanmode="hard",
            scalemode="width",
            width=0.9,
        )
    )

# Style
fig.update_layout(
    autosize=False,
    title=dict(
        text="violin-split · python · plotly · anyplot.ai",
        font=dict(size=16, color=INK),
        x=0.5,
        xanchor="center",
        y=0.96,
    ),
    xaxis=dict(
        title=dict(text=JOB, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        showgrid=False,
        showline=True,
        linecolor=INK_SOFT,
        ticks="",
    ),
    yaxis=dict(
        title=dict(text=SALARY, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        tickformat="$,.0f",
        gridcolor=GRID,
        showline=True,
        linecolor=INK_SOFT,
        zeroline=False,
        ticks="",
    ),
    legend=dict(
        title=dict(text=GENDER, font=dict(size=10, color=INK), side="left"),
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
        font=dict(size=10, color=INK_SOFT),
        orientation="h",
        yanchor="bottom",
        y=1.0,
        xanchor="center",
        x=0.5,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    violingap=0.15,
    violinmode="overlay",
    margin=dict(l=80, r=40, t=90, b=60),
    font=dict(family="sans-serif", color=INK),
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
