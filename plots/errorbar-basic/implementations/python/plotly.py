"""anyplot.ai
errorbar-basic: Basic Error Bar Plot
Library: plotly 6.8.0 | Python 3.13.14
Quality: 89/100 | Updated: 2026-06-30
"""

import importlib
import os
import sys


# Drop script directory from sys.path so the `plotly` package resolves, not this file
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
go = importlib.import_module("plotly.graph_objects")
np = importlib.import_module("numpy")

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
CTRL_FILL = "rgba(26,26,23,0.05)" if THEME == "light" else "rgba(240,239,232,0.05)"

# Imprint palette — one hue per group (positions 1–6)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#2ABCCD", "#954477"]

# Data — clinical trial response (mg/dL) with asymmetric 95% confidence intervals
groups = ["Control", "Treatment A", "Treatment B", "Treatment C", "Treatment D", "Treatment E"]
x_positions = list(range(len(groups)))
means = np.array([42.3, 51.7, 63.2, 47.8, 72.4, 58.9])
err_upper = np.array([5.4, 7.8, 4.1, 9.3, 3.6, 6.5])
err_lower = np.array([4.1, 6.2, 3.8, 7.9, 4.7, 5.1])

# Control CI bounds — reference band for comparison
control_lo = float(means[0] - err_lower[0])
control_hi = float(means[0] + err_upper[0])

fig = go.Figure()

# Subtle control CI reference band (drawn below data)
fig.add_hrect(y0=control_lo, y1=control_hi, fillcolor=CTRL_FILL, line_width=0, layer="below")

# Control baseline dashed reference line
fig.add_hline(y=float(means[0]), line_dash="dot", line_color=INK_MUTED, line_width=1.5)

# Per-group traces — Imprint palette assigns each group a distinct hue
for i, (group, x, mean, eu, el) in enumerate(
    zip(groups, x_positions, means.tolist(), err_upper.tolist(), err_lower.tolist(), strict=False)
):
    color = IMPRINT_PALETTE[i]
    fig.add_trace(
        go.Scatter(
            x=[x],
            y=[mean],
            mode="markers",
            marker={"size": 20, "color": color, "line": {"color": PAGE_BG, "width": 2}},
            error_y={
                "type": "data",
                "symmetric": False,
                "array": [eu],
                "arrayminus": [el],
                "visible": True,
                "thickness": 3,
                "width": 12,
                "color": color,
            },
            name=group,
            customdata=[[group, round(mean - el, 1), round(mean + eu, 1)]],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Mean: %{y:.1f} mg/dL<br>"
                "95%% CI: [%{customdata[1]}, %{customdata[2]}]"
                "<extra></extra>"
            ),
        )
    )

# Annotation: Treatment D (index 4) — highest mean response
fig.add_annotation(
    x=4,
    y=float(means[4] + err_upper[4]),
    text="Peak response",
    showarrow=True,
    arrowhead=2,
    arrowcolor=INK_SOFT,
    arrowwidth=1.5,
    ax=0,
    ay=-32,
    font={"size": 10, "color": INK_SOFT},
    bgcolor=ELEVATED_BG,
    bordercolor=INK_SOFT,
    borderwidth=1,
    borderpad=3,
    xanchor="center",
)

# Annotation: control baseline label
fig.add_annotation(
    x=5.55,
    y=float(means[0]),
    text="Control<br>baseline",
    showarrow=False,
    font={"size": 10, "color": INK_MUTED},
    xanchor="left",
    yanchor="middle",
    bgcolor=ELEVATED_BG,
    borderpad=2,
)

fig.update_layout(
    autosize=False,
    title={
        "text": "Clinical Response by Group · errorbar-basic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Experimental Group", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickmode": "array",
        "tickvals": x_positions,
        "ticktext": groups,
        "showgrid": False,
        "linecolor": INK_SOFT,
        "zeroline": False,
        "ticks": "",
        "range": [-0.6, 6.0],
    },
    yaxis={
        "title": {"text": "Response (mg/dL)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zeroline": False,
        "range": [28, 88],
        "ticks": "",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 80, "r": 80, "t": 80, "b": 60},
    showlegend=True,
    legend={
        "font": {"size": 10, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "x": 0.98,
        "y": 0.98,
        "xanchor": "right",
        "yanchor": "top",
    },
    hoverlabel={"bgcolor": ELEVATED_BG, "bordercolor": INK_SOFT, "font": {"color": INK, "size": 10}},
)

# Save — landscape 3200 × 1800 (width=800 × scale=4, height=450 × scale=4)
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
