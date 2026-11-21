"""anyplot.ai
shap-summary: SHAP Summary Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-14
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.12)" if THEME == "light" else "rgba(240,239,232,0.12)"

# Imprint palette: all eight positions (the SHAP scale below uses the diverging Imprint ramp)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# imprint_div with the muted anchor as midpoint, so mid-scale dots stay visible against the page
IMPRINT_DIV = [[0.0, "#4467A3"], [0.5, INK_MUTED], [1.0, "#AE3030"]]

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature_names
SHAP = "SHAP value (impact on model output)"  # role: shap_values
FEATURE_VALUE = "Feature value"  # role: feature_values

# Data: replace this block with your own long table, for example df = pd.read_csv("shap_long.csv")
rng = np.random.default_rng(42)
n_samples = 200
feature_names = [
    "mean radius",
    "mean texture",
    "mean perimeter",
    "mean area",
    "mean smoothness",
    "mean compactness",
    "mean concavity",
    "mean concave points",
    "mean symmetry",
    "mean fractal dimension",
    "radius error",
    "texture error",
    "perimeter error",
    "area error",
    "smoothness error",
]
means = [14, 19, 92, 655, 0.096, 0.104, 0.089, 0.049, 0.181, 0.063, 0.41, 1.22, 2.87, 40, 0.007]
sds = [3.5, 4, 24, 350, 0.014, 0.053, 0.08, 0.039, 0.027, 0.007, 0.28, 0.55, 2.02, 45, 0.003]
importances = [0.32, 0.06, 0.14, 0.20, 0.02, 0.04, 0.08, 0.06, 0.01, 0.01, 0.02, 0.01, 0.01, 0.01, 0.01]

rows = []
for name, mu, sd, imp in zip(feature_names, means, sds, importances, strict=True):
    values = rng.normal(mu, sd, n_samples)
    scaled = (values - values.min()) / (values.max() - values.min())
    # SHAP values follow the feature value, scaled by importance, plus noise
    shap = (scaled - 0.5) * imp * 2 + rng.normal(0, imp * 0.3, n_samples)
    rows.append(pd.DataFrame({FEATURE: name, SHAP: shap, FEATURE_VALUE: values}))
df = pd.concat(rows, ignore_index=True)

# Plot: reads only df and the constants above
# Rows sorted by mean absolute SHAP value, most important at the top
order = df.groupby(FEATURE)[SHAP].agg(lambda s: s.abs().mean()).sort_values(ascending=False).index.tolist()
row_of = {name: len(order) - 1 - i for i, name in enumerate(order)}
y_row = df[FEATURE].map(row_of).to_numpy(dtype=float)

# Vertical jitter inside a row is layout only; the x position stays the SHAP value
jitter = np.random.default_rng(7).uniform(-0.3, 0.3, len(df))

# Feature values scaled to 0..1 within each feature, so every row spans the full color scale
by_feature = df.groupby(FEATURE)[FEATURE_VALUE]
scaled = (df[FEATURE_VALUE] - by_feature.transform("min")) / (by_feature.transform("max") - by_feature.transform("min"))

fig = go.Figure(
    go.Scatter(
        x=df[SHAP],
        y=y_row + jitter,
        mode="markers",
        marker={
            "size": 5,
            "color": scaled,
            "colorscale": IMPRINT_DIV,
            "cmin": 0,
            "cmax": 1,
            "opacity": 0.8,
            "line": {"width": 0.4, "color": PAGE_BG},
            "colorbar": {
                "title": {"text": FEATURE_VALUE, "font": {"size": 12, "color": INK}},
                "tickfont": {"size": 10, "color": INK_SOFT},
                "tickvals": [0, 1],
                "ticktext": ["Low", "High"],
                "outlinewidth": 0,
                "len": 0.5,
                "thickness": 14,
            },
        },
        customdata=np.column_stack([df[FEATURE], df[FEATURE_VALUE]]),
        hovertemplate="<b>%{customdata[0]}</b><br>SHAP: %{x:.3f}<br>Value: %{customdata[1]:.3g}<extra></extra>",
        showlegend=False,
    )
)
fig.add_vline(x=0, line_width=1.2, line_color=INK_SOFT, layer="below")

fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    margin={"l": 130, "r": 40, "t": 60, "b": 60},
    title={"text": "shap-summary · python · plotly · anyplot.ai", "font": {"size": 16, "color": INK}},
    xaxis={
        "title": {"text": SHAP, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "zeroline": False,
        "linecolor": INK_SOFT,
    },
    yaxis={
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickmode": "array",
        "tickvals": list(row_of.values()),
        "ticktext": list(row_of.keys()),
        "range": [-0.7, len(order) - 0.3],
        "showgrid": False,
        "zeroline": False,
        "linecolor": INK_SOFT,
    },
    plot_bgcolor=PAGE_BG,
    paper_bgcolor=PAGE_BG,
    font={"color": INK},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
