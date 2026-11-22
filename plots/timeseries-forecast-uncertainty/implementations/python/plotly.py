""" anyplot.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: plotly 7.1.0 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-22
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
GRID = "rgba(26, 26, 23, 0.10)" if THEME == "light" else "rgba(240, 239, 232, 0.10)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
COLOR_HISTORICAL = IMPRINT_PALETTE[0]
COLOR_FORECAST = IMPRINT_PALETTE[1]


def rgba(hex_color, alpha):
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r}, {g}, {b}, {alpha})"


# Columns: set these to your table's column names
DATE = "Month"  # role: date
ACTUAL = "Measured capacity (% of rated)"  # role: actual
FORECAST = "Forecast capacity (% of rated)"  # role: forecast
LOWER_80 = "Lower 80%"  # role: lower_80
UPPER_80 = "Upper 80%"  # role: upper_80
LOWER_95 = "Lower 95%"  # role: lower_95
UPPER_95 = "Upper 95%"  # role: upper_95
Y_LABEL = "Battery capacity (% of rated)"

# Data: replace this block with your own table, for example df = pd.read_csv("capacity.csv")
# Battery capacity fade: exponential decay toward a plateau, 36 months measured, 12 forecast.
np.random.seed(42)
n_hist, n_fore = 36, 12
months = pd.date_range("2022-01-01", periods=n_hist + n_fore, freq="MS")
t = np.arange(n_hist + n_fore)
trend = 100 * (0.62 + 0.38 * np.exp(-t / 20))
measured = trend[:n_hist] + np.random.normal(0, 0.7, n_hist)
horizon = np.arange(1, n_fore + 1)
spread = 0.8 + 0.55 * np.sqrt(horizon)
nan_hist = np.full(n_hist, np.nan)
df = pd.DataFrame(
    {
        DATE: months,
        ACTUAL: np.concatenate([measured, np.full(n_fore, np.nan)]),
        FORECAST: np.concatenate([nan_hist, trend[n_hist:]]),
        LOWER_80: np.concatenate([nan_hist, trend[n_hist:] - 1.28 * spread]),
        UPPER_80: np.concatenate([nan_hist, trend[n_hist:] + 1.28 * spread]),
        LOWER_95: np.concatenate([nan_hist, trend[n_hist:] - 1.96 * spread]),
        UPPER_95: np.concatenate([nan_hist, trend[n_hist:] + 1.96 * spread]),
    }
)

# Plot
hist = df[df[ACTUAL].notna()]
fore = df[df[FORECAST].notna()]
forecast_start = fore[DATE].min() if len(fore) else hist[DATE].max()


def band(lower, upper, name, alpha):
    return go.Scatter(
        x=pd.concat([fore[DATE], fore[DATE][::-1]]),
        y=pd.concat([fore[upper], fore[lower][::-1]]),
        fill="toself",
        fillcolor=rgba(COLOR_FORECAST, alpha),
        line={"color": rgba(COLOR_FORECAST, 0)},
        name=name,
        hoverinfo="skip",
    )


fig = go.Figure()
fig.add_trace(band(LOWER_95, UPPER_95, "95% CI", 0.18))
fig.add_trace(band(LOWER_80, UPPER_80, "80% CI", 0.38))

# Forecast start marker
fig.add_shape(
    type="line",
    x0=forecast_start,
    x1=forecast_start,
    y0=0,
    y1=1,
    yref="paper",
    line={"color": INK_SOFT, "width": 2, "dash": "dash"},
)
fig.add_annotation(
    x=forecast_start, y=1.02, yref="paper", text="Forecast start", showarrow=False, font={"size": 16, "color": INK_SOFT}
)

# Historical line (solid)
fig.add_trace(
    go.Scatter(
        x=hist[DATE],
        y=hist[ACTUAL],
        mode="lines",
        name="Historical",
        line={"color": COLOR_HISTORICAL, "width": 3},
        hovertemplate="%{x|%b %Y}<br>Measured: %{y:.1f}%<extra></extra>",
    )
)

# Forecast line (dashed)
fig.add_trace(
    go.Scatter(
        x=fore[DATE],
        y=fore[FORECAST],
        mode="lines",
        name="Forecast",
        line={"color": COLOR_FORECAST, "width": 3, "dash": "dash"},
        hovertemplate="%{x|%b %Y}<br>Forecast: %{y:.1f}%<extra></extra>",
    )
)

# Dotted connector from the last measurement to the first forecast point
fig.add_trace(
    go.Scatter(
        x=[hist[DATE].iloc[-1], forecast_start],
        y=[hist[ACTUAL].iloc[-1], fore[FORECAST].iloc[0] if len(fore) else hist[ACTUAL].iloc[-1]],
        mode="lines",
        line={"color": COLOR_HISTORICAL, "width": 2, "dash": "dot"},
        showlegend=False,
        hoverinfo="skip",
    )
)

fig.update_layout(
    autosize=False,
    title={
        "text": "timeseries-forecast-uncertainty · python · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": DATE, "font": {"size": 18, "color": INK}},
        "tickfont": {"size": 16, "color": INK_SOFT},
        "showgrid": False,
        "showline": True,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": Y_LABEL, "font": {"size": 18, "color": INK}},
        "tickfont": {"size": 16, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "showline": True,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    legend={
        "font": {"size": 16, "color": INK_SOFT},
        "x": 0.02,
        "y": 0.04,
        "xanchor": "left",
        "yanchor": "bottom",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    margin={"l": 100, "r": 60, "t": 100, "b": 80},
    hovermode="x unified",
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
