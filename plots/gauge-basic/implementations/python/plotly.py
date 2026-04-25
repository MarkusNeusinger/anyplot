"""anyplot.ai
gauge-basic: Basic Gauge Chart
Library: plotly 6.7.0 | Python 3.14.4
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

# Okabe-Ito colorblind-safe stand-ins for the red/amber/green convention
ZONE_LOW = "#D55E00"  # vermillion (bad)
ZONE_MID = "#E69F00"  # orange (caution)
ZONE_HIGH = "#009E73"  # bluish green — Okabe-Ito brand (good)

# Data — Sales target achievement for the quarter
value = 72
min_value = 0
max_value = 100
thresholds = [30, 70]

# Plot
fig = go.Figure(
    go.Indicator(
        mode="gauge+number",
        value=value,
        number={"font": {"size": 96, "color": INK}, "suffix": "%"},
        title={
            "text": (
                "<b>Sales Target Achievement</b>"
                f"<br><span style='font-size:22px;color:{INK_SOFT}'>"
                "gauge-basic · plotly · anyplot.ai</span>"
            ),
            "font": {"size": 32, "color": INK},
        },
        gauge={
            "shape": "angular",
            "axis": {
                "range": [min_value, max_value],
                "tickwidth": 2,
                "tickcolor": INK_SOFT,
                "tickfont": {"size": 18, "color": INK_SOFT},
                "ticksuffix": "%",
                "dtick": 10,
            },
            # Slim needle-style indicator so the zone colors stay visible
            "bar": {"color": INK, "thickness": 0.06, "line": {"color": INK, "width": 0}},
            "bgcolor": ELEVATED_BG,
            "borderwidth": 1,
            "bordercolor": INK_SOFT,
            "steps": [
                {"range": [min_value, thresholds[0]], "color": ZONE_LOW},
                {"range": [thresholds[0], thresholds[1]], "color": ZONE_MID},
                {"range": [thresholds[1], max_value], "color": ZONE_HIGH},
            ],
            "threshold": {"line": {"color": INK, "width": 5}, "thickness": 0.95, "value": value},
        },
        domain={"x": [0.05, 0.95], "y": [0.30, 0.95]},
    )
)

# Layout — page surface + zone legend + target-exceeded callout
fig.update_layout(
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"family": "Arial", "color": INK},
    margin={"l": 80, "r": 80, "t": 140, "b": 120},
    annotations=[
        # Zone legend row — three color-coded chips below the gauge
        {
            "x": 0.20,
            "y": 0.14,
            "xref": "paper",
            "yref": "paper",
            "text": (
                f"<span style='color:{ZONE_LOW};font-size:24px'>●</span>  "
                f"<b>At Risk</b>  "
                f"<span style='color:{INK_MUTED}'>0–30%</span>"
            ),
            "showarrow": False,
            "font": {"size": 18, "color": INK},
        },
        {
            "x": 0.50,
            "y": 0.14,
            "xref": "paper",
            "yref": "paper",
            "text": (
                f"<span style='color:{ZONE_MID};font-size:24px'>●</span>  "
                f"<b>On Track</b>  "
                f"<span style='color:{INK_MUTED}'>30–70%</span>"
            ),
            "showarrow": False,
            "font": {"size": 18, "color": INK},
        },
        {
            "x": 0.80,
            "y": 0.14,
            "xref": "paper",
            "yref": "paper",
            "text": (
                f"<span style='color:{ZONE_HIGH};font-size:24px'>●</span>  "
                f"<b>Exceeds Target</b>  "
                f"<span style='color:{INK_MUTED}'>70–100%</span>"
            ),
            "showarrow": False,
            "font": {"size": 18, "color": INK},
        },
        # Target-exceeded callout — emphasises the threshold-crossing story
        {
            "x": 0.5,
            "y": 0.02,
            "xref": "paper",
            "yref": "paper",
            "text": "<b>✓ Target Exceeded</b>  ·  72% surpasses the 70% goal",
            "showarrow": False,
            "font": {"size": 22, "color": ZONE_HIGH},
            "bgcolor": ELEVATED_BG,
            "bordercolor": ZONE_HIGH,
            "borderwidth": 2,
            "borderpad": 12,
        },
    ],
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
