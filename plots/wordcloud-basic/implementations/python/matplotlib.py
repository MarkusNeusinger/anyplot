""" anyplot.ai
wordcloud-basic: Basic Word Cloud
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-06
"""

import os

import matplotlib.pyplot as plt
from wordcloud import WordCloud


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

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


# Create word cloud with Okabe-Ito color palette and proper backgrounds
def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    return OKABE_ITO[hash(word) % len(OKABE_ITO)]


wc = WordCloud(
    width=4800,
    height=2700,
    background_color=PAGE_BG,
    max_words=100,
    min_font_size=20,
    max_font_size=300,
    random_state=42,
    prefer_horizontal=0.7,
    margin=10,
).generate_from_frequencies(word_frequencies)
wc.recolor(color_func=color_func)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.imshow(wc, interpolation="bilinear")
ax.axis("off")

# Title
fig.suptitle("wordcloud-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK, y=0.98)

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
