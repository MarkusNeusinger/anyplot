""" pyplots.ai
heatmap-loss-triangle: Actuarial Loss Development Triangle
Library: plotly 6.6.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-09
"""

import numpy as np
import plotly.graph_objects as go


# Data: Cumulative paid claims triangle (10 accident years x 10 development periods)
np.random.seed(42)

accident_years = list(range(2015, 2025))
development_periods = list(range(1, 11))
n_years = len(accident_years)
n_periods = len(development_periods)

# Age-to-age development factors (decreasing as claims mature)
dev_factors = [2.50, 1.60, 1.30, 1.15, 1.08, 1.05, 1.03, 1.02, 1.01]

# Generate base first-period claims for each accident year (increasing trend)
base_claims = np.array([4200, 4500, 4800, 5100, 5500, 5800, 6200, 6500, 6900, 7300], dtype=float)
base_claims += np.random.normal(0, 200, n_years)
base_claims = np.round(base_claims / 100) * 100

# Build the full 10x10 cumulative triangle
cumulative = np.full((n_years, n_periods), np.nan)
cumulative[:, 0] = base_claims

for col in range(1, n_periods):
    factor = dev_factors[col - 1] + np.random.normal(0, 0.02, n_years)
    cumulative[:, col] = cumulative[:, col - 1] * factor

cumulative = np.round(cumulative, 0)

# Determine actual vs projected: row i has actual data for columns 0..(n_years-1-i)
is_actual = np.full((n_years, n_periods), False)
for i in range(n_years):
    actual_cols = n_years - i
    is_actual[i, :actual_cols] = True

# Normalize for color contrast
z_min = np.nanmin(cumulative)
z_max = np.nanmax(cumulative)

# Plot using numeric axes for precise shape/annotation control
fig = go.Figure()

fig.add_trace(
    go.Heatmap(
        z=cumulative,
        x=list(range(n_periods)),
        y=list(range(n_years)),
        colorscale="Blues",
        zmin=z_min,
        zmax=z_max,
        colorbar={
            "title": {"text": "Cumulative Claims ($)", "font": {"size": 18}},
            "tickfont": {"size": 14},
            "thickness": 25,
            "len": 0.8,
            "tickformat": ",.0f",
        },
        hovertemplate="Accident Year: %{customdata[0]}<br>Dev Period: %{customdata[1]}"
        "<br>Claims: $%{z:,.0f}<extra></extra>",
        customdata=[[(accident_years[i], development_periods[j]) for j in range(n_periods)] for i in range(n_years)],
        showscale=True,
    )
)


# Cell value annotations with per-cell contrast colors
annotations = []
for i in range(n_years):
    for j in range(n_periods):
        val = cumulative[i, j]
        relative = (val - z_min) / (z_max - z_min)
        font_color = "white" if relative > 0.55 else "#222222"
        boundary = j == n_years - 1 - i
        annotations.append(
            {
                "x": j,
                "y": i,
                "text": f"{val:,.0f}",
                "showarrow": False,
                "font": {"size": 17, "color": font_color, "family": "Arial Black, Arial, sans-serif"},
                "bgcolor": "rgba(255,255,255,0.75)" if boundary else None,
                "borderpad": 3 if boundary else 0,
            }
        )

# Add amber overlay rectangles for projected cells
shapes = []
for i in range(n_years):
    for j in range(n_periods):
        if not is_actual[i, j]:
            shapes.append(
                {
                    "type": "rect",
                    "x0": j - 0.5,
                    "x1": j + 0.5,
                    "y0": i - 0.5,
                    "y1": i + 0.5,
                    "line": {"color": "rgba(0,0,0,0)"},
                    "fillcolor": "rgba(255, 165, 0, 0.20)",
                    "layer": "above",
                }
            )

# Diagonal line separating actual from projected (top-right to bottom-left)
shapes.append(
    {
        "type": "line",
        "x0": n_periods - 1 + 0.5,
        "y0": 0 - 0.5,
        "x1": 0 - 0.5,
        "y1": n_years - 1 + 0.5,
        "line": {"color": "rgba(60, 60, 60, 0.6)", "width": 2, "dash": "dash"},
        "layer": "above",
    }
)

# Development factors as individual annotations aligned with columns
for k, factor in enumerate(dev_factors):
    annotations.append(
        {
            "x": (k + 0.5) / n_periods,
            "y": -0.14,
            "xref": "paper",
            "yref": "paper",
            "text": f"{factor:.3f}",
            "showarrow": False,
            "font": {"size": 13, "color": "#555555", "family": "Arial, Helvetica, sans-serif"},
            "xanchor": "center",
        }
    )
annotations.append(
    {
        "x": 0.0,
        "y": -0.14,
        "xref": "paper",
        "yref": "paper",
        "text": "<b>Dev Factors</b>",
        "showarrow": False,
        "font": {"size": 13, "color": "#555555", "family": "Arial, Helvetica, sans-serif"},
        "xanchor": "right",
    }
)

# Legend for actual vs projected
annotations.append(
    {
        "x": 0.01,
        "y": 1.06,
        "xref": "paper",
        "yref": "paper",
        "text": "■ <b>Actual</b> (observed)",
        "showarrow": False,
        "font": {"size": 16, "color": "#306998", "family": "Arial, Helvetica, sans-serif"},
        "xanchor": "left",
    }
)
annotations.append(
    {
        "x": 0.18,
        "y": 1.06,
        "xref": "paper",
        "yref": "paper",
        "text": "■ <b>Projected</b> (estimated IBNR)",
        "showarrow": False,
        "font": {"size": 16, "color": "#CC7722", "family": "Arial, Helvetica, sans-serif"},
        "xanchor": "left",
    }
)

# Style
fig.update_layout(
    title={
        "text": "heatmap-loss-triangle · plotly · pyplots.ai",
        "font": {"size": 28, "family": "Arial, Helvetica, sans-serif", "color": "#1a1a2e"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
    },
    xaxis={
        "title": {"text": "Development Period (Years)", "font": {"size": 22, "color": "#2c3e50"}},
        "tickfont": {"size": 17, "color": "#34495e"},
        "tickvals": list(range(n_periods)),
        "ticktext": [str(p) for p in development_periods],
        "side": "bottom",
    },
    yaxis={
        "title": {"text": "Accident Year", "font": {"size": 22, "color": "#2c3e50"}},
        "tickfont": {"size": 17, "color": "#34495e"},
        "tickvals": list(range(n_years)),
        "ticktext": [str(y) for y in accident_years],
        "autorange": "reversed",
    },
    template="plotly_white",
    shapes=shapes,
    annotations=annotations,
    margin={"l": 140, "r": 100, "t": 120, "b": 140},
    paper_bgcolor="#fafafa",
    plot_bgcolor="#fafafa",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
