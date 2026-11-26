""" anyplot.ai
sn-curve-basic: S-N Curve (Wöhler Curve)
Library: plotly 7.1.0 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-26
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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants: material properties of the steel and the regime boundary
ULTIMATE_STRENGTH = 650  # MPa
YIELD_STRENGTH = 450  # MPa
ENDURANCE_LIMIT = 230  # MPa
LCF_HCF_BOUNDARY = 1e4  # cycles, below this fatigue is low-cycle (plastic)

# Columns: set these to your table's column names
CYCLES = "Cycles to Failure (N)"  # role: cycles
STRESS = "Stress Amplitude (MPa)"  # role: stress

# Data: replace this block with your own table, for example df = pd.read_csv("fatigue_tests.csv")
np.random.seed(42)
basquin_coefficient = 1200  # MPa
basquin_exponent = -0.12
stress_levels = np.array([600, 550, 500, 450, 400, 350, 320, 300, 280, 260, 250, 240])
rows = []
for level in stress_levels:
    n_base = (level / basquin_coefficient) ** (1 / basquin_exponent)
    for factor in 10 ** np.random.normal(0, 0.15, np.random.randint(2, 5)):
        rows.append((n_base * factor, level))
df = pd.DataFrame(rows, columns=[CYCLES, STRESS])

# Plot: reads only df and the constants above
valid = df[[CYCLES, STRESS]].dropna().astype(float)
slope, intercept = np.polyfit(np.log10(valid[CYCLES]), np.log10(valid[STRESS]), 1)
x_lo = 10 ** np.floor(np.log10(df[CYCLES].min()))
x_hi = 10 ** np.ceil(np.log10(df[CYCLES].max()))
y_lo = min(ENDURANCE_LIMIT, df[STRESS].min()) * 0.85
y_hi = max(ULTIMATE_STRENGTH, df[STRESS].max()) * 1.25
fit_cycles = np.logspace(np.log10(x_lo), np.log10(x_hi), 100)
fit_stress = 10**intercept * fit_cycles**slope

fig = go.Figure()

# Light regime shading: low-cycle region and infinite-life band
fig.add_vrect(x0=x_lo, x1=LCF_HCF_BOUNDARY, fillcolor=INK_SOFT, opacity=0.08, layer="below", line_width=0)
fig.add_hrect(y0=y_lo, y1=ENDURANCE_LIMIT, fillcolor=IMPRINT_PALETTE[0], opacity=0.18, layer="below", line_width=0)

fig.add_trace(
    go.Scatter(
        x=fit_cycles,
        y=fit_stress,
        mode="lines",
        name="Basquin fit",
        line={"color": IMPRINT_PALETTE[0], "width": 3},
        hovertemplate="Cycles: %{x:.2e}<br>Stress: %{y:.0f} MPa<extra>Basquin fit</extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=df[CYCLES],
        y=df[STRESS],
        mode="markers",
        name="Test data",
        marker={"color": IMPRINT_PALETTE[1], "size": 12, "line": {"color": PAGE_BG, "width": 1.5}},
        hovertemplate="Cycles: %{x:.2e}<br>Stress: %{y:.0f} MPa<extra>Test data</extra>",
    )
)

# Reference lines, labeled directly at the right edge instead of in the legend
references = [
    ("Ultimate strength", ULTIMATE_STRENGTH, IMPRINT_PALETTE[2], "bottom"),
    ("Yield strength", YIELD_STRENGTH, IMPRINT_PALETTE[3], "bottom"),
    ("Endurance limit", ENDURANCE_LIMIT, IMPRINT_PALETTE[4], "bottom"),
]
for name, value, color, anchor in references:
    fig.add_trace(
        go.Scatter(
            x=[x_lo, x_hi],
            y=[value, value],
            mode="lines",
            name=name,
            line={"color": color, "width": 2, "dash": "dash"},
            showlegend=False,
            hovertemplate=f"{name}: {value} MPa<extra></extra>",
        )
    )
    fig.add_annotation(
        x=np.log10(x_hi) - 0.08 if value != ENDURANCE_LIMIT else np.log10(x_lo) + 0.08,
        y=np.log10(value),
        text=f"{name}, {value} MPa",
        xanchor="right" if value != ENDURANCE_LIMIT else "left",
        yanchor=anchor,
        yshift=4,
        showarrow=False,
        font={"color": color if THEME == "light" else INK, "size": 12},
        bgcolor=ELEVATED_BG,
        bordercolor=color,
        borderwidth=1,
        borderpad=3,
    )

# Region labels: plain text for the three fatigue regimes
lcf_x = np.log10(x_lo) + (np.log10(LCF_HCF_BOUNDARY) - np.log10(x_lo)) / 2
hcf_x = np.log10(LCF_HCF_BOUNDARY) + (np.log10(x_hi) - np.log10(LCF_HCF_BOUNDARY)) / 2
for text, x_pos in [("Low-cycle fatigue", lcf_x), ("High-cycle fatigue", hcf_x)]:
    fig.add_annotation(
        x=x_pos, y=0.97, xref="x", yref="paper", text=text, showarrow=False, font={"size": 12, "color": INK_SOFT}
    )
fig.add_annotation(
    x=np.log10(x_hi) - 0.08,
    y=np.log10((y_lo * ENDURANCE_LIMIT) ** 0.5),
    text="Infinite life",
    xanchor="right",
    yanchor="middle",
    showarrow=False,
    font={"size": 12, "color": INK_SOFT},
)

# Style
fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    hovermode="closest",
    title={
        "text": "sn-curve-basic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": CYCLES, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "type": "log",
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": GRID,
        "showline": True,
        "linewidth": 1,
        "linecolor": INK_SOFT,
        "mirror": False,
        "range": [np.log10(x_lo), np.log10(x_hi)],
        "zerolinecolor": GRID,
    },
    yaxis={
        "title": {"text": STRESS, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "type": "log",
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": GRID,
        "showline": True,
        "linewidth": 1,
        "linecolor": INK_SOFT,
        "mirror": False,
        "range": [np.log10(y_lo), np.log10(y_hi)],
        "zerolinecolor": GRID,
    },
    legend={
        "font": {"size": 10, "color": INK_SOFT},
        "x": 0.36,
        "y": 0.2,
        "xanchor": "left",
        "yanchor": "bottom",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    margin={"l": 80, "r": 40, "t": 60, "b": 60},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
