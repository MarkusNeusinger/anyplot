"""anyplot.ai
violin-box: Violin Plot with Embedded Box Plot
Library: plotly | Python 3.13
Quality: pending | Updated: 2025-12-30
"""

import importlib
import os
import sys


# Avoid importing from local directory
for path in list(sys.path):
    if "violin-box" in path or "implementations" in path:
        sys.path.remove(path)

go = importlib.import_module("plotly.graph_objects")
np = importlib.import_module("numpy")

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette — first series is always #009E73
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data — Test scores across different teaching methods
np.random.seed(42)

groups = ["Traditional", "Interactive", "Online", "Hybrid"]
data = {
    "Traditional": np.random.normal(70, 12, 80),
    "Interactive": np.random.normal(78, 10, 85),
    "Online": np.concatenate([np.random.normal(55, 8, 40), np.random.normal(80, 7, 45)]),
    "Hybrid": np.random.normal(75, 15, 90),
}

# Clip to realistic test score range (0-100)
for group in groups:
    data[group] = np.clip(data[group], 0, 100)

# Plot
fig = go.Figure()

for i, group in enumerate(groups):
    fig.add_trace(
        go.Violin(
            y=data[group],
            name=group,
            box_visible=True,
            meanline_visible=True,
            fillcolor=OKABE_ITO[i],
            opacity=0.7,
            line={"color": INK_SOFT, "width": 2},
            points="outliers",
            pointpos=0,
            marker={"size": 8, "color": INK_SOFT, "opacity": 0.6},
            box={"fillcolor": PAGE_BG, "line": {"color": INK_SOFT, "width": 2}, "width": 0.15},
            meanline={"color": OKABE_ITO[i], "width": 3},
        )
    )

# Style
fig.update_layout(
    title={
        "text": "violin-box · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Teaching Method", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "showgrid": False,
        "linecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Test Score (points)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "range": [0, 105],
        "linecolor": INK_SOFT,
    },
    template="plotly_white",
    showlegend=False,
    plot_bgcolor=PAGE_BG,
    paper_bgcolor=PAGE_BG,
    margin={"l": 100, "r": 50, "t": 100, "b": 100},
    violingap=0.3,
    violinmode="group",
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
