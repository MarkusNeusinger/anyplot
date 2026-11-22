""" anyplot.ai
scatter-text: Scatter Plot with Text Labels Instead of Points
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-22
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_color_manual,
    scale_x_continuous,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
X = "Object-Oriented ← Paradigm → Functional"  # role: x
Y = "Abstraction Level (Low → High)"  # role: y
LABEL = "Language"  # role: label
USE = "Primary Use"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("points.csv")
# Programming languages placed by paradigm (object-oriented to functional) and abstraction level
rows = [
    ("Python", 0.58, 0.88, "General"),
    ("JavaScript", 0.42, 0.72, "Web"),
    ("Java", 0.28, 0.68, "General"),
    ("C++", 0.18, 0.38, "Systems"),
    ("Ruby", 0.72, 0.92, "Web"),
    ("Go", 0.22, 0.58, "Systems"),
    ("Rust", 0.12, 0.48, "Systems"),
    ("Swift", 0.38, 0.80, "Mobile"),
    ("Kotlin", 0.48, 0.85, "Mobile"),
    ("TypeScript", 0.55, 0.68, "Web"),
    ("Scala", 0.72, 0.62, "General"),
    ("Haskell", 0.95, 0.90, "Functional"),
    ("Clojure", 0.88, 0.82, "Functional"),
    ("Elixir", 0.82, 0.88, "Functional"),
    ("F#", 0.78, 0.72, "Functional"),
    ("C#", 0.32, 0.78, "General"),
    ("PHP", 0.35, 0.60, "Web"),
    ("Perl", 0.48, 0.52, "Scripting"),
    ("R", 0.68, 0.78, "Data Science"),
    ("Julia", 0.62, 0.58, "Data Science"),
    ("MATLAB", 0.52, 0.48, "Data Science"),
    ("Lua", 0.42, 0.45, "Scripting"),
    ("Dart", 0.32, 0.52, "Mobile"),
    ("Groovy", 0.45, 0.62, "General"),
    ("OCaml", 0.90, 0.68, "Functional"),
    ("Erlang", 0.85, 0.58, "Functional"),
    ("Fortran", 0.08, 0.32, "Scientific"),
    ("COBOL", 0.05, 0.22, "Legacy"),
    ("Assembly", 0.02, 0.12, "Systems"),
    ("Lisp", 0.92, 0.52, "Functional"),
]
df = pd.DataFrame(rows, columns=[LABEL, X, Y, USE])

# Plot
# Legend order is the data's order; the first seven groups take Imprint colors, any further group is neutral
groups = list(dict.fromkeys(df[USE]))
group_colors = {g: IMPRINT_PALETTE[i] if i < 7 else INK_SOFT for i, g in enumerate(groups)}

plot = (
    ggplot(df, aes(x=X, y=Y, color=USE))
    + geom_text(
        aes(label=LABEL),
        size=6,
        alpha=0.9,
        fontface="bold",
        tooltips=layer_tooltips()
        .title(f"@{{{LABEL}}}")
        .line(f"Category|@{{{USE}}}")
        .line(f"Paradigm|@{{{X}}}")
        .line(f"Abstraction|@{{{Y}}}"),
    )
    + scale_color_manual(values=[group_colors[g] for g in groups], limits=groups, name=USE)
    + scale_x_continuous(expand=[0.06, 0])
    + labs(title="scatter-text · python · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.05),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.25),
        plot_title=element_text(size=16, color=INK, face="bold"),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=12, color=INK),
    )
    + ggsize(800, 450)
)

# Save PNG (800 x 450 at scale 4 = 3200 x 1800 px) and the interactive HTML with tooltips
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
