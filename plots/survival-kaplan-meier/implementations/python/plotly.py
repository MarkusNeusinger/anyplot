""" anyplot.ai
survival-kaplan-meier: Kaplan-Meier Survival Plot
Library: plotly 7.1.0 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-21
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

# Constants
Z_95 = 1.96  # normal quantile for the 95% confidence interval
BAND_ALPHA = 0.15  # translucency of the confidence band
SURVIVAL_HALF = 0.5  # the median survival time is where the curve reaches this level

# Columns: set these to your table's column names
TIME = "Time (months)"  # role: time
EVENT = "Event (1 = event, 0 = censored)"  # role: event
GROUP = "Treatment"  # role: group

# Data: replace this block with your own table, for example df = pd.read_csv("trial.csv")
rng = np.random.default_rng(42)
n_per_group = 80
arms = {"Treatment A (Experimental)": (24, 0.7), "Treatment B (Standard Care)": (16, 0.8)}
frames = []
for arm, (scale, event_rate) in arms.items():
    arm_time = np.clip(rng.exponential(scale=scale, size=n_per_group), 1, 48)
    arm_event = rng.binomial(1, event_rate, size=n_per_group)
    arm_event[arm_time > 36] = 0  # follow-up ends: late subjects are censored
    frames.append(pd.DataFrame({TIME: arm_time, EVENT: arm_event, GROUP: arm}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above


def kaplan_meier(times, events):
    """Return event times, survival and log-log 95% CI bounds after each event time."""
    order = np.argsort(times)
    times, events = times[order], events[order]
    survival, var_sum = 1.0, 0.0
    out_t, out_s, out_lo, out_hi = [], [], [], []
    for t in np.unique(times[events == 1]):
        at_risk = np.sum(times >= t)
        d = np.sum((times == t) & (events == 1))
        survival *= 1 - d / at_risk
        if at_risk > d:
            var_sum += d / (at_risk * (at_risk - d))
        if 0 < survival < 1 and var_sum > 0:
            se_log = np.sqrt(var_sum) / abs(np.log(survival))
            lo, hi = survival ** np.exp(Z_95 * se_log), survival ** np.exp(-Z_95 * se_log)
        else:
            lo, hi = max(0.0, survival - 0.1), min(1.0, survival + 0.1)
        out_t.append(t)
        out_s.append(survival)
        out_lo.append(max(0.0, lo))
        out_hi.append(min(1.0, hi))
    return np.array(out_t), np.array(out_s), np.array(out_lo), np.array(out_hi)


def to_steps(km_t, values, end):
    """Expand per-event values into step coordinates from 1.0 at time zero, flat to the last follow-up time."""
    xs, ys = [0.0], [1.0]
    for i, t in enumerate(km_t):
        xs += [t, t]
        ys += [1.0 if i == 0 else values[i - 1], values[i]]
    if len(km_t) == 0 or end > xs[-1]:
        xs.append(end)
        ys.append(ys[-1])
    return np.array(xs), np.array(ys)


def hex_to_rgba(hex_color, alpha):
    r, g, b = (int(hex_color.lstrip("#")[k : k + 2], 16) for k in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"


clean = df.dropna(subset=[TIME, EVENT, GROUP])
groups = list(clean[GROUP].unique())
fig = go.Figure()
medians = {}
censor_traces = []
for i, group in enumerate(groups):
    rows = clean[clean[GROUP] == group]
    t_all = rows[TIME].to_numpy(dtype=float)
    e_all = rows[EVENT].to_numpy(dtype=int)
    km_t, km_s, km_lo, km_hi = kaplan_meier(t_all, e_all)
    color = IMPRINT_PALETTE[i]
    x_step, y_step = to_steps(km_t, km_s, t_all.max())
    _, y_lo = to_steps(km_t, km_lo, t_all.max())
    _, y_hi = to_steps(km_t, km_hi, t_all.max())

    # Confidence band, stepping with its curve
    fig.add_trace(
        go.Scatter(
            x=np.concatenate([x_step, x_step[::-1]]),
            y=np.concatenate([y_hi, y_lo[::-1]]),
            fill="toself",
            fillcolor=hex_to_rgba(color, BAND_ALPHA),
            line=dict(color="rgba(0,0,0,0)"),
            showlegend=False,
            hoverinfo="skip",
            legendgroup=str(group),
        )
    )
    # Survival step curve
    fig.add_trace(
        go.Scatter(
            x=x_step,
            y=y_step,
            mode="lines",
            line=dict(color=color, width=2),
            name=str(group),
            legendgroup=str(group),
            hovertemplate="Time: %{x:.1f} months<br>Survival: %{y:.1%}<extra></extra>",
        )
    )

    # Censoring ticks at the curve's height at each censoring time
    t_cens = t_all[e_all == 0]
    idx = np.searchsorted(km_t, t_cens, side="right")
    s_cens = np.where(idx > 0, km_s[np.maximum(idx - 1, 0)] if len(km_s) else 1.0, 1.0)
    censor_traces.append(
        go.Scatter(
            x=t_cens,
            y=s_cens,
            mode="markers",
            marker=dict(symbol="line-ns", size=8, line=dict(width=1.5, color=color)),
            name="Censored",
            legendgroup="censored",
            showlegend=i == 0,
            hovertemplate="Censored at: %{x:.1f} months<extra></extra>",
        )
    )

    below = np.flatnonzero(km_s <= SURVIVAL_HALF)
    medians[group] = km_t[below[0]] if len(below) else np.nan

for trace in censor_traces:
    fig.add_trace(trace)

# Style
title = "survival-kaplan-meier · python · plotly · anyplot.ai"
median_lines = [f"{g}: {m:.1f} months" if not np.isnan(m) else f"{g}: not reached" for g, m in medians.items()]
fig.add_annotation(
    x=0.02,
    y=0.03,
    xref="paper",
    yref="paper",
    xanchor="left",
    yanchor="bottom",
    text="Median survival<br>" + "<br>".join(median_lines),
    showarrow=False,
    font=dict(size=10, color=INK),
    align="left",
    bgcolor=ELEVATED_BG,
    bordercolor=INK_SOFT,
    borderwidth=1,
    borderpad=5,
)
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    margin=dict(l=80, r=40, t=70, b=60),
    title=dict(text=title, font=dict(size=16, color=INK), x=0.5, xanchor="center"),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    xaxis=dict(
        title=dict(text=TIME, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        range=[0, clean[TIME].max() * 1.04],
        gridcolor=GRID,
        showline=True,
        linewidth=1,
        linecolor=INK_SOFT,
        zeroline=False,
    ),
    yaxis=dict(
        title=dict(text="Survival probability", font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        tickformat=".0%",
        range=[0, 1.05],
        gridcolor=GRID,
        showline=True,
        linewidth=1,
        linecolor=INK_SOFT,
        zeroline=False,
    ),
    legend=dict(
        title=dict(text=GROUP, font=dict(size=10, color=INK)),
        x=0.98,
        y=0.98,
        xanchor="right",
        yanchor="top",
        font=dict(size=10, color=INK_SOFT),
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
