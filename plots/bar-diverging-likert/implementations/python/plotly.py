"""anyplot.ai
bar-diverging-likert: Likert Scale Diverging Bar Chart
Library: plotly 7.1.0 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-28
"""

import os
import sys


# Prevent self-import: remove this script's directory from sys.path so that
# "import plotly" resolves to the installed package, not this file.
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _here]

import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

FONT_FAMILY = "Inter, Helvetica Neue, Arial, sans-serif"

# Constants
# Imprint diverging scale for the five Likert levels, in scale order: the poles are the red and blue
# anchors of imprint_div, the neutral level is its grey midpoint, the steps between are tints toward it.
LIKERT_COLORS = [
    IMPRINT_PALETTE[4],
    "#CC807D" if THEME == "light" else "#B06060",
    "#6B6A63" if THEME == "light" else "#686762",
    "#8DA1C2" if THEME == "light" else "#56677F",
    IMPRINT_PALETTE[2],
]
# Text color inside each level's segments, chosen for contrast against its fill
LIKERT_TEXT = [
    "#F0EFE8",
    INK if THEME == "light" else "#F0EFE8",
    "#F0EFE8",
    INK if THEME == "light" else "#F0EFE8",
    "#F0EFE8",
]
LABEL_MIN_WIDTH = 7  # segments narrower than this many percentage points stay unlabeled

# Columns: set these to your table's column names
QUESTION = "Question"  # role: question
STRONGLY_DISAGREE = "Strongly Disagree"  # role: strongly_disagree
DISAGREE = "Disagree"  # role: disagree
NEUTRAL = "Neutral"  # role: neutral
AGREE = "Agree"  # role: agree
STRONGLY_AGREE = "Strongly Agree"  # role: strongly_agree
LEVELS = [STRONGLY_DISAGREE, DISAGREE, NEUTRAL, AGREE, STRONGLY_AGREE]

# Data: employee engagement survey, 10 questions on a 5-point Likert scale (percent of responses per row)
df = pd.DataFrame(
    {
        QUESTION: [
            "I feel valued at work",
            "My manager supports my growth",
            "I have the tools I need",
            "Communication is transparent",
            "Work-life balance is respected",
            "I see a clear career path",
            "Team collaboration is effective",
            "Company vision is inspiring",
            "Training opportunities are sufficient",
            "I would recommend this workplace",
        ],
        STRONGLY_DISAGREE: [5, 8, 3, 15, 10, 20, 5, 12, 18, 6],
        DISAGREE: [10, 12, 7, 20, 15, 25, 10, 18, 22, 9],
        NEUTRAL: [15, 20, 10, 25, 20, 20, 15, 20, 25, 12],
        AGREE: [35, 30, 40, 25, 30, 20, 35, 28, 20, 33],
        STRONGLY_AGREE: [35, 30, 40, 15, 25, 15, 35, 22, 15, 40],
    }
)

# Plot
# Sort by net agreement (agree plus strongly agree, minus the two disagree levels); the best row ends on top
net = df[AGREE] + df[STRONGLY_AGREE] - df[DISAGREE] - df[STRONGLY_DISAGREE]
order = net.sort_values(kind="stable").index
df = df.loc[order].reset_index(drop=True)
net = net.loc[order].reset_index(drop=True)

# Diverging positions: the neutral level is split evenly across the zero midpoint
half_neutral = df[NEUTRAL] / 2
starts = {
    STRONGLY_DISAGREE: -(df[STRONGLY_DISAGREE] + df[DISAGREE] + half_neutral),
    DISAGREE: -(df[DISAGREE] + half_neutral),
    NEUTRAL: -half_neutral,
    AGREE: half_neutral,
    STRONGLY_AGREE: half_neutral + df[AGREE],
}
left_end = starts[STRONGLY_DISAGREE]
right_end = half_neutral + df[AGREE] + df[STRONGLY_AGREE]
span = right_end.max() - left_end.min()

fig = go.Figure()
for level, color, text_color in zip(LEVELS, LIKERT_COLORS, LIKERT_TEXT, strict=False):
    share = df[level]
    labels = [f"{v:g}%" if pd.notna(v) and v > LABEL_MIN_WIDTH else "" for v in share]
    fig.add_trace(
        go.Bar(
            y=df[QUESTION],
            x=share,
            base=starts[level],
            orientation="h",
            name=level,
            marker={"color": color, "line": {"color": PAGE_BG, "width": 0.8}},
            text=labels,
            textposition="inside",
            textfont={"size": 11, "color": text_color, "family": FONT_FAMILY},
            customdata=share,
            hovertemplate="%{y}<br>" + level + ": %{customdata}%<extra></extra>",
        )
    )

# Net score annotations on the best and the worst row
best_idx = net.idxmax()
worst_idx = net.idxmin()
fig.add_annotation(
    x=right_end[best_idx],
    y=df.loc[best_idx, QUESTION],
    text=f"<b>{net[best_idx]:+g}</b> net",
    showarrow=False,
    xshift=6,
    font={"size": 11, "color": IMPRINT_PALETTE[2], "family": FONT_FAMILY},
    xanchor="left",
)
fig.add_annotation(
    x=left_end[worst_idx],
    y=df.loc[worst_idx, QUESTION],
    text=f"<b>{net[worst_idx]:+g}</b> net".replace("-", "\u2212"),
    showarrow=False,
    xshift=-6,
    font={"size": 11, "color": IMPRINT_PALETTE[4], "family": FONT_FAMILY},
    xanchor="right",
)

# Title: the mandated format, scaled down from 16 px when it runs long
title_text = "Employee Engagement Survey · bar-diverging-likert · python · plotly · anyplot.ai"
title_size = round(16 * 67 / len(title_text)) if len(title_text) > 67 else 16
subtitle = f"Highest net agreement: {df.loc[best_idx, QUESTION]}; lowest: {df.loc[worst_idx, QUESTION]}"

# Style
fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"family": FONT_FAMILY, "color": INK},
    title={
        "text": title_text,
        "subtitle": {"text": subtitle, "font": {"size": 10, "color": INK_MUTED, "family": FONT_FAMILY}},
        "font": {"size": title_size, "family": FONT_FAMILY, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Response (%)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "ticksuffix": "%",
        "zeroline": True,
        "zerolinecolor": INK_SOFT,
        "zerolinewidth": 2,
        "showgrid": True,
        "gridcolor": GRID,
        "showline": False,
        "range": [left_end.min() - 0.12 * span, right_end.max() + 0.12 * span],
    },
    yaxis={"tickfont": {"size": 10, "color": INK_SOFT, "family": FONT_FAMILY}, "automargin": True, "showline": False},
    barmode="overlay",
    legend={
        "orientation": "h",
        "yanchor": "bottom",
        "y": -0.42,
        "xanchor": "center",
        "x": 0.5,
        "font": {"size": 10, "family": FONT_FAMILY, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 0.5,
        "traceorder": "normal",
    },
    margin={"l": 20, "r": 40, "t": 90, "b": 130},
    bargap=0.25,
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
