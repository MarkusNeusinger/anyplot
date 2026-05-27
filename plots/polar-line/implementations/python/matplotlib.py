""" anyplot.ai
polar-line: Polar Line Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 97/100 | Updated: 2026-05-12
"""

import os
import sys


# Remove current directory from sys.path to avoid import conflict with matplotlib.py
sys.path = [p for p in sys.path if os.path.abspath(p) != os.getcwd()]

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"
ACCENT = "#C475FD"

# Data - Simulating hourly temperature patterns for two seasons
np.random.seed(42)

# Hours of day (24 hours = full circle)
hours = np.linspace(0, 2 * np.pi, 25)[:-1]

# Summer temperature pattern (warmer during day)
summer_temps = 20 + 8 * np.sin(hours - np.pi / 2) + np.random.randn(24) * 0.5

# Winter temperature pattern (cooler, smaller amplitude)
winter_temps = 5 + 5 * np.sin(hours - np.pi / 2) + np.random.randn(24) * 0.5

# Close the loop by appending first point
hours_closed = np.append(hours, hours[0])
summer_closed = np.append(summer_temps, summer_temps[0])
winter_closed = np.append(winter_temps, winter_temps[0])

# Plot
fig, ax = plt.subplots(figsize=(12, 12), subplot_kw={"projection": "polar"}, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.plot(hours_closed, summer_closed, linewidth=3, color=BRAND, label="Summer", marker="o", markersize=8)
ax.plot(hours_closed, winter_closed, linewidth=3, color=ACCENT, label="Winter", marker="o", markersize=8)

# Configure theta axis (hours of day)
hour_labels = [f"{h}:00" for h in range(0, 24, 3)]
ax.set_xticks(np.linspace(0, 2 * np.pi, 8, endpoint=False))
ax.set_xticklabels(hour_labels, fontsize=16, color=INK_SOFT)

# Configure radial axis (temperature)
ax.set_ylim(0, 35)
ax.set_yticks([0, 10, 20, 30])
ax.set_yticklabels(["0°C", "10°C", "20°C", "30°C"], fontsize=14, color=INK_SOFT)

# Style
ax.set_title("polar-line · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=40)
ax.set_rlabel_position(45)

leg = ax.legend(loc="upper left", bbox_to_anchor=(0.95, 0.95), fontsize=16)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    leg.get_frame().set_linewidth(0.5)
    for text in leg.get_texts():
        text.set_color(INK_SOFT)

ax.grid(True, alpha=0.15, linewidth=0.8, color=INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
