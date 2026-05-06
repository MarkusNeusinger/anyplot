""" anyplot.ai
wordcloud-basic: Basic Word Cloud
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-06
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"
OI_PALETTE = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

# Data - Tech industry survey responses about skills
word_frequencies = {
    "Python": 180,
    "JavaScript": 160,
    "React": 145,
    "Docker": 135,
    "AWS": 130,
    "SQL": 125,
    "Linux": 120,
    "Git": 115,
    "API": 110,
    "DevOps": 105,
    "Cloud": 100,
    "Testing": 95,
    "Agile": 90,
    "TypeScript": 87,
    "Node": 84,
    "Kubernetes": 81,
    "MongoDB": 78,
    "Security": 75,
    "Azure": 72,
    "REST": 69,
    "Redis": 66,
    "GraphQL": 63,
    "Analytics": 60,
    "PostgreSQL": 57,
    "Terraform": 54,
    "Backend": 51,
    "Frontend": 48,
    "CICD": 45,
    "Spark": 42,
    "Kafka": 39,
    "Flask": 36,
    "Django": 33,
    "Pandas": 30,
    "NumPy": 28,
    "FastAPI": 26,
    "Vue": 24,
    "Angular": 22,
    "Nginx": 20,
    "OAuth": 18,
    "Jenkins": 16,
    "Ansible": 14,
    "Prometheus": 12,
    "Grafana": 10,
    "RabbitMQ": 8,
    "Elasticsearch": 7,
    "Hadoop": 6,
    "Airflow": 5,
    "dbt": 4,
    "Pulumi": 3,
    "Istio": 2,
}

# Sort by frequency descending
sorted_pairs = sorted(word_frequencies.items(), key=lambda x: -x[1])
words = [p[0] for p in sorted_pairs]
frequencies = [p[1] for p in sorted_pairs]
n_words = len(words)

# Spiral-based layout using golden angle for even distribution
np.random.seed(42)
golden_angle = np.pi * (3 - np.sqrt(5))
x_positions = []
y_positions = []

for i in range(n_words):
    angle = i * golden_angle
    radius = 0.15 * np.sqrt(i + 1)
    x_positions.append(radius * np.cos(angle) * 2.0)
    y_positions.append(radius * np.sin(angle) * 1.1)

# Calculate font sizes (14-52pt range)
freq_array = np.array(frequencies)
max_freq, min_freq = freq_array.max(), freq_array.min()
font_sizes = 14 + (freq_array - min_freq) / (max_freq - min_freq) * 38

# Create DataFrame
df = pd.DataFrame({"word": words, "frequency": frequencies, "x": x_positions, "y": y_positions, "fontsize": font_sizes})

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Add word labels using Okabe-Ito palette cycling
for idx, row_data in df.iterrows():
    color = OI_PALETTE[idx % len(OI_PALETTE)]
    ax.text(
        row_data["x"],
        row_data["y"],
        row_data["word"],
        fontsize=row_data["fontsize"],
        fontweight="bold",
        ha="center",
        va="center",
        color=color,
    )

# Style
ax.set_xlim(-2.4, 2.4)
ax.set_ylim(-1.4, 1.4)
ax.axis("off")

ax.set_title("wordcloud-basic · seaborn · anyplot.ai", fontsize=26, fontweight="medium", color=INK, pad=20)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
