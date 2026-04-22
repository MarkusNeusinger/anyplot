""" pyplots.ai
wordcloud-basic: Basic Word Cloud
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 68/100 | Created: 2025-12-24
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Set random seed for reproducibility
np.random.seed(42)

# Data - Tech industry survey responses about skills (50 words)
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

# Spiral-based layout using golden angle for even distribution (no overlap)
golden_angle = np.pi * (3 - np.sqrt(5))
x_positions = []
y_positions = []

for i in range(n_words):
    angle = i * golden_angle
    radius = 0.15 * np.sqrt(i + 1)  # Sqrt for even spacing
    x_positions.append(radius * np.cos(angle) * 2.0)
    y_positions.append(radius * np.sin(angle) * 1.1)

# Calculate font sizes (14-48pt range for better differentiation)
freq_array = np.array(frequencies)
max_freq, min_freq = freq_array.max(), freq_array.min()
font_sizes = 14 + (freq_array - min_freq) / (max_freq - min_freq) * 34

# Create DataFrame
df = pd.DataFrame({"word": words, "frequency": frequencies, "x": x_positions, "y": y_positions, "fontsize": font_sizes})

# Plot using seaborn
sns.set_theme(style="white", context="poster", font_scale=1.0)
fig, ax = plt.subplots(figsize=(16, 9))

# Use seaborn scatterplot as background layer
sns.scatterplot(
    data=df,
    x="x",
    y="y",
    size="frequency",
    sizes=(100, 2000),
    hue="frequency",
    palette="muted",
    alpha=0.15,
    legend=False,
    ax=ax,
)

# Add word labels with seaborn muted palette colors
colors = sns.color_palette("muted", n_colors=10)
for idx, row_data in df.iterrows():
    ax.text(
        row_data["x"],
        row_data["y"],
        row_data["word"],
        fontsize=row_data["fontsize"],
        fontweight="bold",
        ha="center",
        va="center",
        color=colors[idx % len(colors)],
    )

# Clean up axes for word cloud appearance
ax.set_xlim(-2.4, 2.4)
ax.set_ylim(-1.4, 1.4)
ax.axis("off")

# Title following exact pyplots.ai format
ax.set_title("wordcloud-basic · seaborn · pyplots.ai", fontsize=26, fontweight="bold", pad=20)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
