""" pyplots.ai
bar-diverging-likert: Likert Scale Diverging Bar Chart
Library: plotly 6.6.0 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-04
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data
np.random.seed(42)
questions = [
    "I feel valued at work",
    "My manager supports my growth",
    "I have the tools I need",
    "Communication is transparent",
    "Work-life balance is respected",
    "I see a clear career path",
    "Team collaboration is effective",
    "Company vision is inspiring",
    "Training opportunities are sufficient",
    "I would recommend this workplace",
]

raw = np.random.dirichlet(np.ones(5), size=len(questions)) * 100
df = pd.DataFrame(
    {
        "question": questions,
        "strongly_disagree": raw[:, 0],
        "disagree": raw[:, 1],
        "neutral": raw[:, 2],
        "agree": raw[:, 3],
        "strongly_agree": raw[:, 4],
    }
)

# Make data more realistic with varied sentiment
adjustments = [
    [5, 10, 15, 35, 35],
    [8, 12, 20, 30, 30],
    [3, 7, 10, 40, 40],
    [15, 20, 25, 25, 15],
    [10, 15, 20, 30, 25],
    [20, 25, 20, 20, 15],
    [5, 10, 15, 35, 35],
    [12, 18, 20, 28, 22],
    [18, 22, 25, 20, 15],
    [6, 9, 12, 33, 40],
]
df[["strongly_disagree", "disagree", "neutral", "agree", "strongly_agree"]] = adjustments

# Sort by net agreement
df["net_agreement"] = df["agree"] + df["strongly_agree"] - df["disagree"] - df["strongly_disagree"]
df = df.sort_values("net_agreement").reset_index(drop=True)

# Calculate diverging positions
half_neutral = df["neutral"] / 2
neg_sd = -(df["strongly_disagree"] + df["disagree"] + half_neutral)
neg_d = -(df["disagree"] + half_neutral)
neg_n = -half_neutral
pos_n = half_neutral
pos_a = half_neutral + df["agree"]
pos_sa = half_neutral + df["agree"] + df["strongly_agree"]

# Colors — diverging red-to-blue with muted neutral
colors = {
    "strongly_disagree": "#C0392B",
    "disagree": "#E67E73",
    "neutral": "#B0B0B0",
    "agree": "#5B9BD5",
    "strongly_agree": "#306998",
}

labels = {
    "strongly_disagree": "Strongly Disagree",
    "disagree": "Disagree",
    "neutral": "Neutral",
    "agree": "Agree",
    "strongly_agree": "Strongly Agree",
}

# Plot
fig = go.Figure()

segments = [
    ("strongly_disagree", neg_sd, neg_d),
    ("disagree", neg_d, neg_n),
    ("neutral", neg_n, pos_n),
    ("agree", pos_n, pos_a),
    ("strongly_agree", pos_a, pos_sa),
]

for key, starts, ends in segments:
    widths = ends - starts
    centers = starts + widths / 2
    text_vals = df[key].astype(int).astype(str) + "%"
    text_display = [t if abs(w) > 8 else "" for t, w in zip(text_vals, widths, strict=False)]

    fig.add_trace(
        go.Bar(
            y=df["question"],
            x=widths,
            base=starts,
            orientation="h",
            name=labels[key],
            marker={"color": colors[key], "line": {"color": "white", "width": 0.5}},
            text=text_display,
            textposition="inside",
            textfont={"size": 16, "color": "white"},
            hovertemplate="%{y}<br>" + labels[key] + ": %{text}<extra></extra>",
        )
    )

# Style
fig.update_layout(
    title={
        "text": "bar-diverging-likert · plotly · pyplots.ai",
        "font": {"size": 28, "weight": "bold"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "← Disagree    |    Agree →", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "ticksuffix": "%",
        "zeroline": True,
        "zerolinecolor": "#333333",
        "zerolinewidth": 2,
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.07)",
        "range": [neg_sd.min() - 5, pos_sa.max() + 5],
    },
    yaxis={"tickfont": {"size": 17}, "automargin": True},
    barmode="overlay",
    template="plotly_white",
    legend={
        "orientation": "h",
        "yanchor": "bottom",
        "y": -0.18,
        "xanchor": "center",
        "x": 0.5,
        "font": {"size": 16},
        "traceorder": "normal",
    },
    margin={"l": 20, "r": 40, "t": 80, "b": 100},
    plot_bgcolor="white",
    paper_bgcolor="white",
    bargap=0.25,
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
