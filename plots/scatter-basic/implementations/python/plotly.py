""" pyplots.ai
scatter-basic: Basic Scatter Plot
Library: plotly 6.5.2 | Python 3.14
Quality: 92/100 | Created: 2025-12-22
"""

import numpy as np
import plotly.graph_objects as go


# Data: Study hours vs exam scores (realistic educational context)
np.random.seed(42)
n_students = 120
study_hours = np.random.uniform(1, 10, n_students)
base_score = 45 + study_hours * 5
exam_scores = base_score + np.random.randn(n_students) * 8
exam_scores = np.clip(exam_scores, 0, 100)

# Inject outliers to show scatter plot's outlier-detection value
study_hours[0], exam_scores[0] = 8.5, 52.0  # High effort, low result
study_hours[1], exam_scores[1] = 2.0, 78.0  # Low effort, high result
study_hours[2], exam_scores[2] = 9.2, 55.0  # Another underperformer

# Linear regression for trend line
coeffs = np.polyfit(study_hours, exam_scores, 1)
trend_x = np.array([0.5, 10.5])
trend_y = np.polyval(coeffs, trend_x)
r_value = np.corrcoef(study_hours, exam_scores)[0, 1]

# Color palette
python_blue = "#306998"
accent_orange = "#D4782F"

fig = go.Figure()

# Trend line (behind markers)
fig.add_trace(
    go.Scatter(
        x=trend_x,
        y=trend_y,
        mode="lines",
        line={"color": "rgba(48, 105, 152, 0.4)", "width": 2.5, "dash": "dash"},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Main scatter — size 11 avoids congestion in dense regions
fig.add_trace(
    go.Scatter(
        x=study_hours,
        y=exam_scores,
        mode="markers",
        marker={"size": 11, "color": python_blue, "opacity": 0.6, "line": {"width": 1.2, "color": "white"}},
        showlegend=False,
        hovertemplate="<b>Student</b><br>Study: %{x:.1f} h<br>Score: %{y:.1f}%<extra></extra>",
    )
)

# Outlier diamonds
fig.add_trace(
    go.Scatter(
        x=[8.5, 2.0, 9.2],
        y=[52.0, 78.0, 55.0],
        mode="markers",
        marker={
            "size": 15,
            "color": accent_orange,
            "opacity": 0.9,
            "line": {"width": 2, "color": "white"},
            "symbol": "diamond",
        },
        showlegend=False,
        hoverinfo="skip",
    )
)

# Annotations — each outlier gets its own label for clarity
ann_base = {
    "showarrow": True,
    "arrowhead": 2,
    "arrowsize": 1.2,
    "arrowwidth": 2,
    "arrowcolor": accent_orange,
    "align": "center",
    "font": {"size": 16, "color": accent_orange, "family": "Arial, sans-serif"},
    "bgcolor": "rgba(255,255,255,0.85)",
    "bordercolor": accent_orange,
    "borderwidth": 1.5,
    "borderpad": 5,
}
annotations = [
    {**ann_base, "x": 2.0, "y": 78.0, "text": "Low effort,<br>high score", "ax": -75, "ay": -45},
    {**ann_base, "x": 8.5, "y": 52.0, "text": "High effort,<br>low score", "ax": 80, "ay": 40},
    {**ann_base, "x": 9.2, "y": 55.0, "text": "Underperformer", "ax": 75, "ay": -35},
    # Correlation coefficient near trend line
    {
        "x": 8.5,
        "y": np.polyval(coeffs, 8.5) + 4,
        "text": f"<b>r = {r_value:.2f}</b>",
        "showarrow": False,
        "bgcolor": "rgba(255,255,255,0.8)",
        "borderpad": 4,
        "font": {"size": 17, "color": python_blue, "family": "Arial, sans-serif"},
    },
]

fig.update_layout(
    title={
        "text": "scatter-basic · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#2C3E50", "family": "Arial Black, Arial, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.95,
    },
    xaxis={
        "title": {"text": "Study Hours (h)", "font": {"size": 22, "family": "Arial, sans-serif"}, "standoff": 12},
        "tickfont": {"size": 18},
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.06)",
        "range": [0, 11],
        "zeroline": False,
        "dtick": 2,
    },
    yaxis={
        "title": {"text": "Exam Score (%)", "font": {"size": 22, "family": "Arial, sans-serif"}, "standoff": 12},
        "tickfont": {"size": 18},
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.06)",
        "range": [35, 105],
        "zeroline": False,
        "dtick": 10,
    },
    template="plotly_white",
    showlegend=False,
    margin={"l": 80, "r": 40, "t": 90, "b": 70},
    annotations=annotations,
    plot_bgcolor="white",
    paper_bgcolor="#FAFBFC",
    hoverlabel={"bgcolor": "white", "font_size": 14, "font_color": python_blue},
)

fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
