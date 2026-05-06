"""anyplot.ai
wordcloud-basic: Basic Word Cloud
Library: plotly | Python 3.13
Quality: pending | Created: 2025-05-06
"""

import os
import random

import numpy as np
import plotly.graph_objects as go


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (colorblind-safe)
OKABE_ITO = [
    "#009E73",  # bluish green (brand)
    "#D55E00",  # vermillion
    "#0072B2",  # blue
    "#CC79A7",  # reddish purple
    "#E69F00",  # orange
    "#56B4E9",  # sky blue
    "#F0E442",  # yellow
]

# Data - Data science and analytics tools (distinct from programming languages)
word_frequencies = {
    "NumPy": 95,
    "Pandas": 92,
    "TensorFlow": 88,
    "PyTorch": 85,
    "Scikit-learn": 82,
    "Matplotlib": 80,
    "Jupyter": 78,
    "Plotly": 75,
    "Apache Spark": 72,
    "Tableau": 68,
    "Power BI": 65,
    "SQL": 92,
    "Docker": 70,
    "Kubernetes": 62,
    "Git": 88,
    "AWS": 80,
    "Google Cloud": 75,
    "Azure": 68,
    "Airflow": 58,
    "Dask": 52,
    "SciPy": 78,
    "Statsmodels": 45,
    "XGBoost": 75,
    "Keras": 70,
    "OpenCV": 60,
    "NLTK": 48,
    "Hugging Face": 55,
    "MLflow": 50,
}

# Seed for reproducibility
random.seed(42)
np.random.seed(42)

# Calculate font sizes based on frequency
max_freq = max(word_frequencies.values())
min_freq = min(word_frequencies.values())

# Scale font sizes for large canvas
min_size = 26
max_size = 88

# Sort by frequency for better placement
sorted_words = sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)
words = [w[0] for w in sorted_words]
freqs = [w[1] for w in sorted_words]

# Manual positioning to prevent overlap and create cloud-like appearance
positions = [
    # Largest words - center and spread
    (0.50, 0.82),  # NumPy - center top
    (0.15, 0.72),  # Pandas - left
    (0.85, 0.75),  # TensorFlow - right
    (0.50, 0.60),  # PyTorch - center
    (0.25, 0.50),  # Scikit-learn - left mid
    (0.75, 0.52),  # Matplotlib - right mid
    (0.50, 0.40),  # SQL - center lower-mid
    (0.10, 0.35),  # Jupyter - far left
    (0.90, 0.38),  # Plotly - far right
    (0.35, 0.28),  # Apache Spark - left lower
    (0.65, 0.28),  # SciPy - right lower
    (0.50, 0.18),  # Tableau - center bottom
    (0.20, 0.12),  # Power BI - left bottom
    (0.80, 0.12),  # Git - right bottom
    # Medium words
    (0.08, 0.58),  # Docker
    (0.92, 0.60),  # Kubernetes
    (0.30, 0.68),  # AWS
    (0.70, 0.42),  # Google Cloud
    (0.15, 0.08),  # Azure
    (0.40, 0.05),  # Airflow
    (0.60, 0.05),  # Dask
    (0.85, 0.08),  # XGBoost
    # Smaller words - edges
    (0.05, 0.88),  # Keras
    (0.95, 0.85),  # OpenCV
    (0.05, 0.22),  # NLTK
    (0.95, 0.25),  # Hugging Face
    (0.25, 0.92),  # MLflow
]

# Create figure
fig = go.Figure()

# Add each word as a scatter trace with text
for i, (word, freq) in enumerate(zip(words, freqs, strict=False)):
    if i < len(positions):
        x, y = positions[i]
    else:
        x = random.uniform(0.1, 0.9)
        y = random.uniform(0.1, 0.9)

    # Scale frequency to font size
    font_size = min_size + (freq - min_freq) / (max_freq - min_freq) * (max_size - min_size)
    color = OKABE_ITO[i % len(OKABE_ITO)]

    fig.add_trace(
        go.Scatter(
            x=[x],
            y=[y],
            mode="text",
            text=[word],
            textfont=dict(size=font_size, color=color, family="Arial"),
            hovertemplate=f"<b>{word}</b><br>Frequency: {freq}<extra></extra>",
            showlegend=False,
        )
    )

# Update layout with theme-adaptive styling
fig.update_layout(
    title=dict(text="wordcloud-basic · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[-0.05, 1.05], linecolor=INK_SOFT),
    yaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[-0.02, 1.02], linecolor=INK_SOFT),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    margin=dict(l=20, r=20, t=80, b=20),
    hoverlabel=dict(bgcolor=ELEVATED_BG, font=dict(color=INK_SOFT)),
)

# Save outputs
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
