"""anyplot.ai
heatmap-calendar: Basic Calendar Heatmap
Library: plotly 6.7.0 | Python 3.14.4
Quality: 88/100 | Updated: 2026-04-27
"""

import os
import sys


# Prevent this file from shadowing the installed plotly package
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _here]
del _here

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - GitHub-style activity over one year
np.random.seed(42)
start_date = pd.Timestamp("2024-01-01")
end_date = pd.Timestamp("2024-12-31")
dates = pd.date_range(start=start_date, end=end_date, freq="D")

# Realistic activity with weekly patterns and occasional bursts
base_activity = np.random.poisson(lam=3, size=len(dates))
weekend_mask = dates.dayofweek >= 5
base_activity[weekend_mask] = np.random.poisson(lam=1, size=weekend_mask.sum())
burst_days = np.random.choice(len(dates), size=20, replace=False)
base_activity[burst_days] = np.random.randint(10, 20, size=20)
zero_days = np.random.choice(len(dates), size=50, replace=False)
base_activity[zero_days] = 0

df = pd.DataFrame({"date": dates, "value": base_activity})
df["dayofweek"] = df["date"].dt.dayofweek
df["month"] = df["date"].dt.month
df["week_of_year"] = (df["date"] - start_date).dt.days // 7

# Build heatmap matrix: 7 rows (days) × n_weeks columns
n_weeks = df["week_of_year"].max() + 1
heatmap_data = np.full((7, n_weeks), np.nan)
hover_dates = np.full((7, n_weeks), "", dtype=object)

for _, row in df.iterrows():
    w, d = row["week_of_year"], row["dayofweek"]
    heatmap_data[d, w] = row["value"]
    hover_dates[d, w] = row["date"].strftime("%b %d, %Y")

day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
month_starts = df.groupby("month")["week_of_year"].min()
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Imprint sequential colorscale (single-polarity: commit count intensity)
imprint_seq = [[0.0, "#009E73"], [1.0, "#4467A3"]]

# Plot
fig = go.Figure()

fig.add_trace(
    go.Heatmap(
        z=heatmap_data,
        x=list(range(n_weeks)),
        y=day_labels,
        customdata=hover_dates,
        colorscale=imprint_seq,
        showscale=True,
        colorbar={
            "title": {"text": "Daily commits", "font": {"size": 12, "color": INK}},
            "tickfont": {"size": 10, "color": INK_SOFT},
            "thickness": 13,
            "len": 0.6,
            "bgcolor": ELEVATED_BG,
            "bordercolor": INK_SOFT,
            "borderwidth": 1,
        },
        hoverongaps=False,
        hovertemplate="%{customdata}<br>Commits: %{z}<extra></extra>",
        xgap=2,
        ygap=2,
        zmin=0,
    )
)

fig.update_layout(
    autosize=False,
    title={
        "text": "heatmap-calendar · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "tickmode": "array",
        "tickvals": list(month_starts.values),
        "ticktext": month_labels,
        "tickfont": {"size": 11, "color": INK_SOFT},
        "side": "top",
        "showgrid": False,
        "linecolor": INK_SOFT,
    },
    yaxis={
        "tickfont": {"size": 11, "color": INK_SOFT},
        "autorange": "reversed",
        "showgrid": False,
        "linecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 40, "r": 70, "t": 60, "b": 30},
)

# Save — hard target: 3200 x 1800 (landscape)
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
