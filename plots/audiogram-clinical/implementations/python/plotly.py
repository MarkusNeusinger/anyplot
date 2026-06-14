"""anyplot.ai
audiogram-clinical: Clinical Audiogram
Library: plotly 6.8.0 | Python 3.13.13
Quality: 88/100 | Created: 2026-06-14
"""

import os

import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette — semantic clinical colors (audiogram convention)
# Red-right / blue-left is the universal audiometric standard; use closest Imprint members
RIGHT_EAR_COLOR = "#AE3030"  # matte red (Imprint pos 5) — right ear
LEFT_EAR_COLOR = "#4467A3"  # blue (Imprint pos 3) — left ear

# Data — occupational noise-induced high-frequency sensorineural notch
frequencies = [125, 250, 500, 1000, 2000, 4000, 8000]
freq_labels = ["125", "250", "500", "1k", "2k", "4k", "8k"]

threshold_right = [10, 10, 15, 20, 30, 70, 55]  # right ear: classic 4 kHz noise notch
threshold_left = [15, 15, 20, 25, 35, 75, 60]  # left ear: slightly worse

# Severity bands: (label, dB_low, dB_high, fill_rgba)
# Fills derived from Imprint palette hues at low opacity — distinguishable but non-competing
severity_bands = [
    ("Normal", -10, 25, "rgba(0,158,115,0.07)"),
    ("Mild", 25, 40, "rgba(221,204,119,0.12)"),
    ("Moderate", 40, 55, "rgba(189,130,51,0.12)"),
    ("Mod. Severe", 55, 70, "rgba(196,117,253,0.09)"),
    ("Severe", 70, 90, "rgba(174,48,48,0.12)"),
    ("Profound", 90, 120, "rgba(174,48,48,0.22)"),
]

# Plot
fig = go.Figure()

# Severity band shading (below data layer)
for _, y0, y1, color in severity_bands:
    fig.add_shape(
        type="rect", xref="paper", yref="y", x0=0, x1=1, y0=y0, y1=y1, fillcolor=color, line={"width": 0}, layer="below"
    )

# Severity band labels — right margin (outside plot, within figure)
for label, y0, y1, _ in severity_bands:
    fig.add_annotation(
        x=1.01,
        xref="paper",
        y=(y0 + y1) / 2,
        yref="y",
        text=label,
        showarrow=False,
        xanchor="left",
        font={"size": 10, "color": INK_MUTED},
    )

# Right ear — red circles, solid connecting line
fig.add_trace(
    go.Scatter(
        x=frequencies,
        y=threshold_right,
        name="Right Ear (O)",
        mode="lines+markers",
        line={"color": RIGHT_EAR_COLOR, "width": 2.5},
        marker={
            "symbol": "circle",
            "size": 12,
            "color": RIGHT_EAR_COLOR,
            "line": {"color": RIGHT_EAR_COLOR, "width": 2},
        },
    )
)

# Left ear — blue crosses, dashed connecting line (standard audiogram convention)
fig.add_trace(
    go.Scatter(
        x=frequencies,
        y=threshold_left,
        name="Left Ear (X)",
        mode="lines+markers",
        line={"color": LEFT_EAR_COLOR, "width": 2.5, "dash": "dash"},
        marker={"symbol": "x", "size": 12, "color": LEFT_EAR_COLOR, "line": {"color": LEFT_EAR_COLOR, "width": 2.5}},
    )
)

# Title — compute fontsize from length
title = "audiogram-clinical · python · plotly · anyplot.ai"
n = len(title)
title_fontsize = max(11, round(16 * (67 / n if n > 67 else 1.0)))

fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin={"l": 80, "r": 150, "t": 80, "b": 80},
    title={"text": title, "font": {"size": title_fontsize, "color": INK}},
    xaxis={
        "type": "log",
        "title": {"text": "Frequency (Hz)", "font": {"size": 12, "color": INK}},
        "tickvals": frequencies,
        "ticktext": freq_labels,
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "showgrid": True,
        "range": [2.0, 3.95],
    },
    yaxis={
        "title": {"text": "Hearing Level (dB HL)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": GRID,
        "showgrid": True,
        "range": [120, -10],
        "dtick": 10,
    },
    legend={
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "font": {"color": INK_SOFT, "size": 10},
        "x": 0.02,
        "y": 0.02,
        "xanchor": "left",
        "yanchor": "bottom",
    },
    font={"color": INK},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
