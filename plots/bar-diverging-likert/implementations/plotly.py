""" pyplots.ai
bar-diverging-likert: Likert Scale Diverging Bar Chart
Library: plotly 6.6.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-04
"""

import pandas as pd
import plotly.graph_objects as go


# Data — employee engagement survey (10 questions, 5-point Likert scale)
categories = ["strongly_disagree", "disagree", "neutral", "agree", "strongly_agree"]
df = pd.DataFrame(
    {
        "question": [
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
        ],
        "strongly_disagree": [5, 8, 3, 15, 10, 20, 5, 12, 18, 6],
        "disagree": [10, 12, 7, 20, 15, 25, 10, 18, 22, 9],
        "neutral": [15, 20, 10, 25, 20, 20, 15, 20, 25, 12],
        "agree": [35, 30, 40, 25, 30, 20, 35, 28, 20, 33],
        "strongly_agree": [35, 30, 40, 15, 25, 15, 35, 22, 15, 40],
    }
)

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

# Text colors — dark on lighter backgrounds, white on darker backgrounds
text_colors = {
    "strongly_disagree": "white",
    "disagree": "#2C2C2C",
    "neutral": "#2C2C2C",
    "agree": "#2C2C2C",
    "strongly_agree": "white",
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
            textfont={"size": 16, "color": text_colors[key], "family": "Inter, Helvetica Neue, Arial, sans-serif"},
            hovertemplate="%{y}<br>" + labels[key] + ": %{text}<extra></extra>",
        )
    )

# Annotate best and worst items
best_idx = df["net_agreement"].idxmax()
worst_idx = df["net_agreement"].idxmin()
best_net = df.loc[best_idx, "net_agreement"]
worst_net = df.loc[worst_idx, "net_agreement"]
best_end = pos_sa.iloc[best_idx]
worst_start = neg_sd.iloc[worst_idx]

fig.add_annotation(
    x=best_end + 2,
    y=df.loc[best_idx, "question"],
    text=f"<b>+{best_net}</b> net",
    showarrow=False,
    font={"size": 14, "color": "#306998", "family": "Inter, Helvetica Neue, Arial, sans-serif"},
    xanchor="left",
)
fig.add_annotation(
    x=worst_start - 2,
    y=df.loc[worst_idx, "question"],
    text=f"<b>{worst_net}</b> net",
    showarrow=False,
    font={"size": 14, "color": "#C0392B", "family": "Inter, Helvetica Neue, Arial, sans-serif"},
    xanchor="right",
)

# Style
font_family = "Inter, Helvetica Neue, Arial, sans-serif"
fig.update_layout(
    title={
        "text": "bar-diverging-likert · plotly · pyplots.ai",
        "font": {"size": 28, "weight": "bold", "family": font_family},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "← Disagree    |    Agree →", "font": {"size": 22, "family": font_family}},
        "tickfont": {"size": 18, "family": font_family},
        "ticksuffix": "%",
        "zeroline": True,
        "zerolinecolor": "#333333",
        "zerolinewidth": 2,
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.07)",
        "range": [neg_sd.min() - 12, pos_sa.max() + 12],
    },
    yaxis={"tickfont": {"size": 17, "family": font_family}, "automargin": True},
    barmode="overlay",
    template="plotly_white",
    legend={
        "orientation": "h",
        "yanchor": "bottom",
        "y": -0.18,
        "xanchor": "center",
        "x": 0.5,
        "font": {"size": 16, "family": font_family},
        "traceorder": "normal",
    },
    margin={"l": 20, "r": 40, "t": 80, "b": 100},
    plot_bgcolor="white",
    paper_bgcolor="white",
    bargap=0.25,
    font={"family": font_family},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
