"""anyplot.ai
heatmap-polar: Polar Heatmap for Cyclic Two-Dimensional Data
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Created: 2026-05-13
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
# Single-polarity continuous scale built from Imprint positions 1 and 3
imprint_seq = [[0.0, IMPRINT_PALETTE[0]], [1.0, IMPRINT_PALETTE[2]]]

# Columns: set these to your table's column names
DAY = "Day"  # role: radial
HOUR = "Hour of day"  # role: angular
VIEWS = "Page views"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("traffic.csv")
np.random.seed(42)
rows = []
for day_idx, day_name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
    for hour in range(24):
        morning_peak = np.exp(-0.5 * ((hour - 9) / 1.5) ** 2)
        evening_peak = np.exp(-0.5 * ((hour - 20) / 2.0) ** 2)
        lunch_peak = 0.4 * np.exp(-0.5 * ((hour - 13) / 1.0) ** 2)
        if day_idx >= 5:  # weekend: single midday peak
            views = 3500 * np.exp(-0.5 * ((hour - 13) / 3.5) ** 2) + np.random.normal(0, 80)
        else:  # weekday: morning + lunch + evening peaks
            views = 5500 * (morning_peak + 0.8 * evening_peak + lunch_peak) + np.random.normal(0, 150)
        rows.append({DAY: day_name, HOUR: hour, VIEWS: max(views, 0.0)})
df = pd.DataFrame(rows)

# Plot
table = df.pivot_table(index=DAY, columns=HOUR, values=VIEWS, sort=False)
n_days, n_hours = table.shape
hours = list(table.columns)
bar_width = 360.0 / n_hours
hour_angles = [h * bar_width for h in range(n_hours)]
vmin, vmax = np.nanmin(table.to_numpy()), np.nanmax(table.to_numpy())

fig = go.Figure()
for d, day in enumerate(table.index):
    hourly = table.loc[day].tolist()
    fig.add_trace(
        go.Barpolar(
            r=[1.0] * n_hours,
            base=[d] * n_hours,
            theta=hour_angles,
            width=[bar_width] * n_hours,
            marker={"color": hourly, "coloraxis": "coloraxis", "line": {"color": PAGE_BG, "width": 0.4}},
            name=str(day),
            showlegend=False,
            customdata=np.column_stack([hours, hourly]),
            hovertemplate=(
                f"<b>{day}</b><br>{HOUR}: %{{customdata[0]:.0f}}:00<br>{VIEWS}: %{{customdata[1]:,.0f}}<extra></extra>"
            ),
        )
    )

# Style: label every third hour, in 12-hour clock text
tick_hours = hours[::3]
angular_tickvals = [h * bar_width for h in tick_hours]
angular_ticktext = [f"{(h % 12) or 12}{'am' if h < 12 else 'pm'}" for h in tick_hours]

fig.update_layout(
    autosize=False,
    title={
        "text": "Website Traffic · heatmap-polar · python · plotly · anyplot.ai",
        "font": {"size": 15, "color": INK},
        "x": 0.44,
        "y": 0.98,
        "xanchor": "center",
        "yanchor": "top",
    },
    polar={
        "bgcolor": PAGE_BG,
        "domain": {"x": [0.07, 0.8], "y": [0.04, 0.9]},
        "angularaxis": {
            "direction": "clockwise",
            "rotation": 90,
            "tickvals": angular_tickvals,
            "ticktext": angular_ticktext,
            "tickfont": {"size": 11, "color": INK_SOFT},
            "linecolor": INK_SOFT,
            "gridcolor": GRID,
            "gridwidth": 1,
        },
        "radialaxis": {
            "range": [0, n_days],
            "tickvals": [d + 0.5 for d in range(n_days)],
            "ticktext": list(table.index),
            "tickfont": {"size": 10, "color": INK_SOFT},
            "gridcolor": GRID,
            "showgrid": True,
            "showline": False,
            "angle": 45,
            "tickangle": 0,
        },
    },
    coloraxis={
        "colorscale": imprint_seq,
        "cmin": vmin,
        "cmax": vmax,
        "colorbar": {
            "title": {"text": VIEWS, "font": {"size": 12, "color": INK}},
            "tickfont": {"size": 10, "color": INK_SOFT},
            "bgcolor": ELEVATED_BG,
            "bordercolor": INK_SOFT,
            "borderwidth": 1,
            "thickness": 14,
            "len": 0.55,
            "x": 0.9,
            "y": 0.5,
            "yanchor": "middle",
        },
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 20, "r": 40, "t": 50, "b": 20},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
