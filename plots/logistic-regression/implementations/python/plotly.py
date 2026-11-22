"""anyplot.ai
logistic-regression: Logistic Regression Curve Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-18
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.linear_model import LogisticRegression


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
THRESHOLD = 0.5  # default decision threshold of a binary classifier

# Columns: set these to your table's column names
BIOMARKER = "Biomarker level (mg/dL)"  # role: x
DISEASE = "Disease present"  # role: y
PROBABILITY = "Disease probability"  # role: probability
CI_LOWER = "95% CI lower"  # role: ci_lower
CI_UPPER = "95% CI upper"  # role: ci_upper

# Data: replace this block with your own table, for example df = pd.read_csv("patients.csv")
rng = np.random.default_rng(42)
n_per_class = 75
df = pd.DataFrame(
    {
        BIOMARKER: np.clip(
            np.concatenate([rng.normal(150, 25, n_per_class), rng.normal(220, 30, n_per_class)]), 80, 300
        ),
        DISEASE: np.repeat([0, 1], n_per_class),
    }
)

# Plot: reads only df and the constants above
obs = df.dropna(subset=[BIOMARKER, DISEASE])
x_obs = obs[BIOMARKER].to_numpy(dtype=float)
y_obs = (obs[DISEASE].to_numpy(dtype=float) > 0.5).astype(int)
classes = [0, 1]

# The curve and band need both classes present
x_curve = np.linspace(x_obs.min(), x_obs.max(), 200)
if len(np.unique(y_obs)) == len(classes):
    model = LogisticRegression().fit(x_obs.reshape(-1, 1), y_obs)
    accuracy = model.score(x_obs.reshape(-1, 1), y_obs)
    y_proba = model.predict_proba(x_curve.reshape(-1, 1))[:, 1]
else:
    accuracy = np.nan
    y_proba = np.full_like(x_curve, np.nan)

# Approximate 95% band from the binomial standard error
se = 1.96 * np.sqrt(y_proba * (1 - y_proba) / len(obs))
curve = pd.DataFrame(
    {
        BIOMARKER: x_curve,
        PROBABILITY: y_proba,
        CI_LOWER: np.clip(y_proba - se, 0, 1),
        CI_UPPER: np.clip(y_proba + se, 0, 1),
    }
)

# Jitter along y only; x stays at the observed value
jitter = np.random.default_rng(0).uniform(-0.02, 0.02, len(obs))
y_jittered = np.clip(y_obs + jitter, 0, 1)

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=np.concatenate([curve[BIOMARKER], curve[BIOMARKER][::-1]]),
        y=np.concatenate([curve[CI_UPPER], curve[CI_LOWER][::-1]]),
        fill="toself",
        fillcolor="rgba(0, 158, 115, 0.2)",
        line={"color": "rgba(0,0,0,0)"},
        name="95% CI",
        hoverinfo="skip",
    )
)

fig.add_trace(
    go.Scatter(
        x=curve[BIOMARKER],
        y=curve[PROBABILITY],
        mode="lines",
        line={"color": IMPRINT_PALETTE[0], "width": 2.5},
        name="Logistic curve",
        hovertemplate="<b>Biomarker:</b> %{x:.1f}<br><b>Probability:</b> %{y:.3f}<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=[x_curve[0], x_curve[-1]],
        y=[THRESHOLD, THRESHOLD],
        mode="lines",
        line={"color": INK_SOFT, "width": 1.5, "dash": "dash"},
        name=f"Decision threshold ({THRESHOLD})",
        hoverinfo="skip",
    )
)

for i, cls in enumerate(classes):
    mask = y_obs == cls
    fig.add_trace(
        go.Scatter(
            x=x_obs[mask],
            y=y_jittered[mask],
            mode="markers",
            marker={"size": 8, "color": IMPRINT_PALETTE[i], "opacity": 0.6, "line": {"width": 0.5, "color": PAGE_BG}},
            name=f"{DISEASE} = {cls}",
            hovertemplate=f"<b>{BIOMARKER}:</b> %{{x:.1f}}<br><b>{DISEASE}:</b> {cls}<extra></extra>",
        )
    )

# Style
span = x_obs.max() - x_obs.min()
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    margin={"l": 70, "r": 30, "t": 60, "b": 60},
    title={
        "text": "logistic-regression · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": BIOMARKER, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "range": [x_obs.min() - 0.03 * span, x_obs.max() + 0.03 * span],
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": PROBABILITY, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "range": [-0.05, 1.05],
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "font": {"size": 10, "color": INK_SOFT},
        "x": 0.02,
        "y": 0.98,
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    annotations=[
        {
            "xref": "paper",
            "yref": "paper",
            "x": 0.97,
            "y": 0.2,
            "xanchor": "right",
            "text": f"Accuracy: {accuracy:.1%}",
            "showarrow": False,
            "font": {"size": 11, "color": INK},
            "bgcolor": ELEVATED_BG,
            "bordercolor": INK_SOFT,
            "borderwidth": 1,
            "borderpad": 4,
        }
    ],
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
