"""anyplot.ai
line-training-load-pmc: Training Load Performance Management Chart
Library: plotly 6.8.0 | Python 3.13.13
Quality: 87/100 | Created: 2026-06-13
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette — semantic mapping for training metrics
FITNESS_GREEN = "#009E73"  # CTL / positive form — Imprint position 1 (growth/fitness)
FATIGUE_RED = "#AE3030"  # ATL / negative form — Imprint position 5 (stress/fatigue)
TSS_BLUE = "#4467A3"  # Daily TSS bars — Imprint position 3 (neutral input)

# Data — 180-day periodized training block with build/recovery cycles and end taper
np.random.seed(42)
n_days = 180
dates = pd.date_range("2025-01-01", periods=n_days, freq="D").strftime("%Y-%m-%d").tolist()

tss = np.zeros(n_days)
for i in range(n_days):
    day_of_week = i % 7
    week_phase = (i // 7) % 4  # 0,1 = base build; 2 = peak build; 3 = recovery
    if day_of_week == 6:  # Sunday rest
        tss[i] = 0.0
    elif i >= 160:  # Taper for peak event at day 180
        tss[i] = np.random.uniform(20, 60) * max(0.3, 1 - (i - 160) / 25)
    elif week_phase == 3:  # Recovery week
        tss[i] = np.random.uniform(25, 60)
    elif week_phase == 2:  # Peak build week
        tss[i] = np.random.uniform(90, 155)
    else:  # Base build
        tss[i] = np.random.uniform(55, 115)

# Standard PMC formulas: EWMA with 42-day (CTL) and 7-day (ATL) time constants
ctl_alpha = 1 - np.exp(-1 / 42)
atl_alpha = 1 - np.exp(-1 / 7)

ctl = np.zeros(n_days)
atl = np.zeros(n_days)
tsb = np.zeros(n_days)
ctl[0] = tss[0] * 0.5
atl[0] = tss[0] * 0.7

for i in range(1, n_days):
    tsb[i] = ctl[i - 1] - atl[i - 1]  # Form = yesterday's fitness − yesterday's fatigue
    ctl[i] = ctl[i - 1] + (tss[i] - ctl[i - 1]) * ctl_alpha
    atl[i] = atl[i - 1] + (tss[i] - atl[i - 1]) * atl_alpha

# Plot — secondary y-axis keeps TSB (±50) readable against CTL/ATL (0–150)
fig = make_subplots(specs=[[{"secondary_y": True}]])

# Daily TSS bars (primary axis — background layer, raw workout stress)
fig.add_trace(
    go.Bar(
        x=dates,
        y=tss,
        name="Daily TSS",
        width=86400000,  # one day in ms — fills each slot without gaps
        marker={"color": TSS_BLUE, "opacity": 0.28, "line": {"width": 0}},
        hovertemplate="%{x|%b %d}: TSS %{y:.0f}<extra></extra>",
    ),
    secondary_y=False,
)

# TSB positive fill — fresh / "in form" (secondary axis)
fig.add_trace(
    go.Scatter(
        x=dates,
        y=np.where(tsb >= 0, tsb, 0.0),
        fill="tozeroy",
        fillcolor="rgba(0,158,115,0.18)",
        line={"width": 0},
        mode="lines",
        showlegend=False,
        hoverinfo="skip",
    ),
    secondary_y=True,
)

# TSB negative fill — fatigued (secondary axis)
fig.add_trace(
    go.Scatter(
        x=dates,
        y=np.where(tsb <= 0, tsb, 0.0),
        fill="tozeroy",
        fillcolor="rgba(174,48,48,0.18)",
        line={"width": 0},
        mode="lines",
        showlegend=False,
        hoverinfo="skip",
    ),
    secondary_y=True,
)

# TSB = 0 reference — separates "fresh" from "fatigued" zones (secondary axis)
fig.add_trace(
    go.Scatter(
        x=[dates[0], dates[-1]],
        y=[0, 0],
        mode="lines",
        line={"color": INK_SOFT, "width": 1.0, "dash": "dot"},
        showlegend=False,
        hoverinfo="skip",
    ),
    secondary_y=True,
)

# ATL — Acute Training Load / Fatigue (primary axis, dashed for color-blind accessibility)
fig.add_trace(
    go.Scatter(
        x=dates,
        y=atl,
        name="Fatigue (ATL)",
        line={"color": FATIGUE_RED, "width": 2.5, "dash": "dot"},
        mode="lines",
        hovertemplate="%{x|%b %d}: ATL %{y:.1f}<extra></extra>",
    ),
    secondary_y=False,
)

# CTL — Chronic Training Load / Fitness (primary axis, drawn on top)
fig.add_trace(
    go.Scatter(
        x=dates,
        y=ctl,
        name="Fitness (CTL)",
        line={"color": FITNESS_GREEN, "width": 3.0},
        mode="lines",
        hovertemplate="%{x|%b %d}: CTL %{y:.1f}<extra></extra>",
    ),
    secondary_y=False,
)

# TSB — Form line with legend entry (secondary axis, 2px for better visibility)
fig.add_trace(
    go.Scatter(
        x=dates,
        y=tsb,
        name="Form (TSB)",
        line={"color": INK_SOFT, "width": 2.0},
        mode="lines",
        hovertemplate="%{x|%b %d}: TSB %{y:.1f}<extra></extra>",
    ),
    secondary_y=True,
)

# Title with scaled font for the long string (73 chars → ratio 67/73)
title = "Training Load PMC · line-training-load-pmc · python · plotly · anyplot.ai"
n = len(title)
title_fontsize = max(11, round(16 * 67 / n)) if n > 67 else 16

fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    title={"text": title, "font": {"size": title_fontsize, "color": INK}, "x": 0.02, "xanchor": "left"},
    margin={"l": 80, "r": 80, "t": 80, "b": 90},
    legend={
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "font": {"color": INK_SOFT, "size": 10},
        "x": 0.99,
        "y": 0.97,
        "xanchor": "right",
        "yanchor": "top",
    },
    barmode="overlay",
)

# Primary y-axis: Training Load (TSS bars, CTL, ATL — all non-negative)
fig.update_yaxes(
    title={"text": "Training Load (TSS · CTL · ATL)", "font": {"color": INK, "size": 12}},
    tickfont={"color": INK_SOFT, "size": 10},
    gridcolor=GRID,
    showline=True,
    linecolor=INK_SOFT,
    mirror=False,
    zeroline=False,
    rangemode="tozero",
    secondary_y=False,
)

# Secondary y-axis: Form / TSB (oscillates around 0 — no grid to avoid doubling)
fig.update_yaxes(
    title={"text": "Form (TSB)", "font": {"color": INK, "size": 12}},
    tickfont={"color": INK_SOFT, "size": 10},
    showgrid=False,
    zeroline=False,
    showline=True,
    linecolor=INK_SOFT,
    mirror=False,
    secondary_y=True,
)

# x-axis: shared date axis with monthly ticks
fig.update_xaxes(
    tickfont={"color": INK_SOFT, "size": 10},
    showline=True,
    linecolor=INK_SOFT,
    mirror=False,
    showgrid=False,
    dtick="M1",
    tickformat="%b '%y",
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
