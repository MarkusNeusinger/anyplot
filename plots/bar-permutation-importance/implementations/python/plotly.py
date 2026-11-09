"""anyplot.ai
bar-permutation-importance: Permutation Feature Importance Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-17
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
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: sequential ramp (brand green -> blue) for single-polarity importance
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
IMPRINT_SEQ = [[0.0, IMPRINT_PALETTE[0]], [1.0, IMPRINT_PALETTE[2]]]

# Constants
TOP_LABELS = 3  # number of leading features that get a value label

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature
IMPORTANCE = "Mean decrease in model score (R² loss)"  # role: importance_mean
IMPORTANCE_STD = "Std. dev. across shuffles"  # role: importance_std

# Data: replace this block with your own table, for example df = pd.read_csv("permutation_importance.csv")
df = pd.DataFrame(
    {
        FEATURE: [
            "Temperature",
            "Humidity",
            "Wind Speed",
            "Pressure",
            "Solar Radiation",
            "Precipitation",
            "Cloud Cover",
            "UV Index",
            "Visibility",
            "Dew Point",
            "Air Quality Index",
            "Altitude",
            "Latitude",
            "Season Encoded",
            "Time of Day",
        ],
        IMPORTANCE: [
            0.245,
            0.198,
            0.156,
            0.089,
            0.072,
            0.058,
            0.045,
            0.038,
            0.025,
            0.018,
            0.012,
            0.008,
            0.003,
            -0.002,
            -0.008,
        ],
        IMPORTANCE_STD: [
            0.045,
            0.038,
            0.032,
            0.022,
            0.018,
            0.015,
            0.012,
            0.010,
            0.008,
            0.006,
            0.005,
            0.004,
            0.003,
            0.003,
            0.004,
        ],
    }
)

# Plot: reads only df and the constants above
# Ascending order puts the highest importance at the top of a horizontal bar chart
ranked = df.sort_values(IMPORTANCE, ascending=True)

fig = go.Figure()
fig.add_trace(
    go.Bar(
        x=ranked[IMPORTANCE],
        y=ranked[FEATURE].astype(str),
        orientation="h",
        marker=dict(
            color=ranked[IMPORTANCE],
            colorscale=IMPRINT_SEQ,
            cmin=ranked[IMPORTANCE].min(),
            cmax=ranked[IMPORTANCE].max(),
            line=dict(color=PAGE_BG, width=0.5),
        ),
        error_x=dict(type="data", array=ranked[IMPORTANCE_STD], color=INK, thickness=1.5, width=4),
        hovertemplate="<b>%{y}</b><br>Importance: %{x:.3f} ± %{error_x.array:.3f}<extra></extra>",
        showlegend=False,
    )
)

# Reference line at zero separates helpful from harmful features
fig.add_vline(x=0, line=dict(color=INK_SOFT, width=1.5, dash="dash"))

# Value labels on the leading features, placed past the error bar
for _, row in ranked.nlargest(TOP_LABELS, IMPORTANCE).iterrows():
    fig.add_annotation(
        x=row[IMPORTANCE] + np.nan_to_num(row[IMPORTANCE_STD]),
        y=str(row[FEATURE]),
        text=f"{row[IMPORTANCE]:.3f}",
        showarrow=False,
        xanchor="left",
        xshift=6,
        font=dict(size=10, color=INK_SOFT),
    )

fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    title=dict(
        text="bar-permutation-importance · python · plotly · anyplot.ai",
        font=dict(size=16, color=INK),
        x=0.5,
        xanchor="center",
    ),
    xaxis=dict(
        title=dict(text=IMPORTANCE, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        zeroline=False,
        linecolor=INK_SOFT,
        showgrid=True,
    ),
    yaxis=dict(
        title=dict(text=FEATURE, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        linecolor=INK_SOFT,
        showgrid=False,
        ticksuffix="  ",
    ),
    plot_bgcolor=PAGE_BG,
    paper_bgcolor=PAGE_BG,
    margin=dict(l=130, r=50, t=60, b=60),
    showlegend=False,
    font=dict(color=INK),
    hoverlabel=dict(bgcolor=ELEVATED_BG, font=dict(color=INK)),
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
