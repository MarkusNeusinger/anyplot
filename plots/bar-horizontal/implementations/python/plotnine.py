""" anyplot.ai
bar-horizontal: Horizontal Bar Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-07
"""

import os
import sys
from importlib import import_module


remove_paths = {os.path.dirname(os.path.abspath(__file__)), os.getcwd()}
sys.path[:] = [p for p in sys.path if os.path.abspath(p) not in remove_paths]  # noqa: E402

import pandas as pd  # noqa: E402


pn = import_module("plotnine")
aes = pn.aes
coord_flip = pn.coord_flip
element_line = pn.element_line
element_rect = pn.element_rect
element_text = pn.element_text
geom_bar = pn.geom_bar
ggplot = pn.ggplot
labs = pn.labs
theme = pn.theme
theme_minimal = pn.theme_minimal


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data: Top 10 programming languages by popularity (survey results)
data = {
    "language": ["JavaScript", "Python", "Java", "TypeScript", "C#", "C++", "PHP", "Go", "Rust", "Swift"],
    "users_percent": [65.6, 49.3, 35.4, 34.8, 29.7, 23.0, 18.4, 14.3, 13.1, 6.6],
}

df = pd.DataFrame(data)

# Sort by value and convert to categorical for proper ordering
df = df.sort_values("users_percent", ascending=True)
df["language"] = pd.Categorical(df["language"], categories=df["language"], ordered=True)

# Theme-adaptive styling
anyplot_theme = theme(
    figure_size=(16, 9),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major_x=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor_x=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_rect(color=INK_SOFT, fill=None),
    axis_title=element_text(size=20, color=INK),
    axis_text=element_text(size=16, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(size=24, color=INK, weight="bold"),
)

# Plot
plot = (
    ggplot(df, aes(x="language", y="users_percent"))
    + geom_bar(stat="identity", fill=BRAND, width=0.7)
    + coord_flip()
    + labs(x="Programming Language", y="Developer Usage (%)", title="bar-horizontal · plotnine · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
