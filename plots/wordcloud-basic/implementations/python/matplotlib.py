""" pyplots.ai
wordcloud-basic: Basic Word Cloud
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-24
"""

import matplotlib.pyplot as plt
from wordcloud import WordCloud


# Data - Tech industry survey responses about most valued skills
word_frequencies = {
    "Python": 150,
    "JavaScript": 120,
    "Data": 110,
    "Machine Learning": 100,
    "Cloud": 95,
    "API": 90,
    "Database": 85,
    "Security": 80,
    "DevOps": 75,
    "Docker": 70,
    "Kubernetes": 65,
    "React": 60,
    "SQL": 58,
    "AWS": 55,
    "Git": 52,
    "Agile": 50,
    "Testing": 48,
    "Linux": 45,
    "TypeScript": 42,
    "Node": 40,
    "REST": 38,
    "CI/CD": 35,
    "Microservices": 32,
    "Azure": 30,
    "MongoDB": 28,
    "Redis": 26,
    "GraphQL": 24,
    "Terraform": 22,
    "Spark": 20,
    "Analytics": 18,
    "Frontend": 16,
    "Backend": 15,
    "Scalability": 14,
    "Automation": 13,
    "Architecture": 12,
    "Networking": 11,
    "Performance": 10,
    "Monitoring": 9,
    "Debugging": 8,
    "Documentation": 7,
}

# Create word cloud with Python-themed colors
wc = WordCloud(
    width=4800,
    height=2700,
    background_color="white",
    colormap="Blues",
    max_words=100,
    min_font_size=20,
    max_font_size=300,
    random_state=42,
    prefer_horizontal=0.7,
    margin=10,
).generate_from_frequencies(word_frequencies)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
ax.imshow(wc, interpolation="bilinear")
ax.axis("off")

# Title - positioned above the word cloud
fig.suptitle("Tech Skills Survey · wordcloud-basic · matplotlib · pyplots.ai", fontsize=24, y=0.98)

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
