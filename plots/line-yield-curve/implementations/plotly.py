""" pyplots.ai
line-yield-curve: Yield Curve (Interest Rate Term Structure)
Library: plotly 6.6.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-14
"""

import numpy as np
import plotly.graph_objects as go


# Data - U.S. Treasury yield curves on three dates showing normal, flat, and inverted shapes
maturity_labels = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
maturity_years = np.array([1 / 12, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30])

# Normal upward-sloping curve (Jan 2022)
yields_normal = np.array([0.08, 0.21, 0.44, 0.78, 1.18, 1.42, 1.72, 1.90, 1.98, 2.32, 2.27])

# Flat curve (Jun 2023)
yields_flat = np.array([5.27, 5.40, 5.47, 5.40, 4.87, 4.49, 4.13, 4.03, 3.84, 4.09, 3.91])

# Inverted curve (Oct 2023)
yields_inverted = np.array([5.54, 5.55, 5.56, 5.46, 5.05, 4.80, 4.62, 4.65, 4.62, 4.98, 4.81])

# Colorblind-safe palette: steel blue, teal, amber
colors = ["#306998", "#17BECF", "#BCBD22"]
markers = ["circle", "diamond", "square"]

# Plot
fig = go.Figure()

for ydata, name, color, marker in [
    (yields_normal, "Jan 2022 (Normal)", colors[0], markers[0]),
    (yields_flat, "Jun 2023 (Flat)", colors[1], markers[1]),
    (yields_inverted, "Oct 2023 (Inverted)", colors[2], markers[2]),
]:
    fig.add_trace(
        go.Scatter(
            x=maturity_years,
            y=ydata,
            name=name,
            mode="lines+markers",
            line={"color": color, "width": 4, "shape": "spline"},
            marker={"size": 12, "symbol": marker, "line": {"width": 1.5, "color": "#FFFFFF"}},
            hovertemplate="%{text}<br>Yield: %{y:.2f}%<extra>" + name + "</extra>",
            text=maturity_labels,
        )
    )

# Inversion shading - filled region between short-term and long-term yields
short_term_max = max(yields_inverted[:4])
long_term_min = min(yields_inverted[6:])
fig.add_hrect(y0=long_term_min, y1=short_term_max, fillcolor="rgba(188, 189, 34, 0.08)", line_width=0)

# Annotation arrow pointing to the inversion zone
fig.add_annotation(
    x=np.log10(0.5),
    y=short_term_max,
    xref="x",
    yref="y",
    text="<b>Inversion Zone</b><br><i>Short-term yields exceed<br>long-term yields</i>",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.5,
    arrowwidth=2,
    arrowcolor="#BCBD22",
    ax=80,
    ay=-60,
    font={"size": 16, "color": "#555555"},
    align="left",
    bordercolor="#BCBD22",
    borderwidth=1.5,
    borderpad=6,
    bgcolor="rgba(255, 255, 255, 0.9)",
)

# Annotation highlighting the spread at 10Y maturity
spread_10y_bps = int(round((yields_inverted[8] - yields_normal[8]) * 100))
fig.add_annotation(
    x=np.log10(10),
    y=(yields_inverted[8] + yields_normal[8]) / 2,
    xref="x",
    yref="y",
    text=f"<b>+{spread_10y_bps} bps</b><br>at 10Y",
    showarrow=False,
    font={"size": 15, "color": "#306998"},
    bgcolor="rgba(255, 255, 255, 0.85)",
    borderpad=4,
)

# Layout
fig.update_layout(
    title={
        "text": (
            "<b>U.S. Treasury Yield Curves</b>"
            "<br><span style='font-size:18px;color:#888888'>"
            "line-yield-curve · plotly · pyplots.ai</span>"
        ),
        "font": {"size": 28, "color": "#333333"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.96,
    },
    xaxis={
        "title": {"text": "Maturity", "font": {"size": 22, "color": "#555555"}},
        "tickfont": {"size": 18, "color": "#555555"},
        "tickvals": maturity_years,
        "ticktext": maturity_labels,
        "type": "log",
        "showgrid": False,
        "showline": True,
        "linewidth": 1.5,
        "linecolor": "#CCCCCC",
        "zeroline": False,
        "spikemode": "across",
        "spikethickness": 1,
        "spikecolor": "#AAAAAA",
        "spikedash": "dot",
    },
    yaxis={
        "title": {"text": "Yield (%)", "font": {"size": 22, "color": "#555555"}},
        "tickfont": {"size": 18, "color": "#555555"},
        "ticksuffix": "%",
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(200, 200, 200, 0.3)",
        "griddash": "dot",
        "showline": True,
        "linewidth": 1.5,
        "linecolor": "#CCCCCC",
        "zeroline": False,
        "spikemode": "across",
        "spikethickness": 1,
        "spikecolor": "#AAAAAA",
        "spikedash": "dot",
    },
    legend={
        "font": {"size": 20},
        "x": 0.02,
        "y": 0.98,
        "xanchor": "left",
        "yanchor": "top",
        "bgcolor": "rgba(255, 255, 255, 0.9)",
        "bordercolor": "rgba(200, 200, 200, 0.5)",
        "borderwidth": 1,
        "itemsizing": "constant",
    },
    template="plotly_white",
    plot_bgcolor="rgba(250, 250, 252, 1)",
    margin={"l": 100, "r": 80, "t": 130, "b": 100},
    hovermode="x unified",
    hoverlabel={"font_size": 16, "namelength": -1},
    spikedistance=-1,
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
