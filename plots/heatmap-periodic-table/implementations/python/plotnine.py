"""anyplot.ai
heatmap-periodic-table: Periodic Table Property Heatmap
Library: plotnine 0.15.7 | Python 3.13.13
Quality: 87/100 | Created: 2026-06-15
"""

import os
import sys


sys.path = [p for p in sys.path if os.path.abspath(p) != os.getcwd()]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_text,
    geom_tile,
    ggplot,
    guide_colorbar,
    labs,
    scale_color_identity,
    scale_fill_gradient,
    scale_y_reverse,
    theme,
    theme_void,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
NA_TILE = "#E0DFD8" if THEME == "light" else "#2C2C28"

# fmt: off
# (symbol, atomic_num, group, display_row, pauling_electronegativity)
# display_row: 1–7 for main periods, 8.5 = lanthanides, 9.5 = actinides
elements = [
    # Period 1
    ("H",   1,  1, 1.0, 2.20), ("He",  2, 18, 1.0, None),
    # Period 2
    ("Li",  3,  1, 2.0, 0.98), ("Be",  4,  2, 2.0, 1.57),
    ("B",   5, 13, 2.0, 2.04), ("C",   6, 14, 2.0, 2.55),
    ("N",   7, 15, 2.0, 3.04), ("O",   8, 16, 2.0, 3.44),
    ("F",   9, 17, 2.0, 3.98), ("Ne", 10, 18, 2.0, None),
    # Period 3
    ("Na", 11,  1, 3.0, 0.93), ("Mg", 12,  2, 3.0, 1.31),
    ("Al", 13, 13, 3.0, 1.61), ("Si", 14, 14, 3.0, 1.90),
    ("P",  15, 15, 3.0, 2.19), ("S",  16, 16, 3.0, 2.58),
    ("Cl", 17, 17, 3.0, 3.16), ("Ar", 18, 18, 3.0, None),
    # Period 4
    ("K",  19,  1, 4.0, 0.82), ("Ca", 20,  2, 4.0, 1.00),
    ("Sc", 21,  3, 4.0, 1.36), ("Ti", 22,  4, 4.0, 1.54),
    ("V",  23,  5, 4.0, 1.63), ("Cr", 24,  6, 4.0, 1.66),
    ("Mn", 25,  7, 4.0, 1.55), ("Fe", 26,  8, 4.0, 1.83),
    ("Co", 27,  9, 4.0, 1.88), ("Ni", 28, 10, 4.0, 1.91),
    ("Cu", 29, 11, 4.0, 1.90), ("Zn", 30, 12, 4.0, 1.65),
    ("Ga", 31, 13, 4.0, 1.81), ("Ge", 32, 14, 4.0, 2.01),
    ("As", 33, 15, 4.0, 2.18), ("Se", 34, 16, 4.0, 2.55),
    ("Br", 35, 17, 4.0, 2.96), ("Kr", 36, 18, 4.0, 3.00),
    # Period 5
    ("Rb", 37,  1, 5.0, 0.82), ("Sr", 38,  2, 5.0, 0.95),
    ("Y",  39,  3, 5.0, 1.22), ("Zr", 40,  4, 5.0, 1.33),
    ("Nb", 41,  5, 5.0, 1.60), ("Mo", 42,  6, 5.0, 2.16),
    ("Tc", 43,  7, 5.0, 1.90), ("Ru", 44,  8, 5.0, 2.20),
    ("Rh", 45,  9, 5.0, 2.28), ("Pd", 46, 10, 5.0, 2.20),
    ("Ag", 47, 11, 5.0, 1.93), ("Cd", 48, 12, 5.0, 1.69),
    ("In", 49, 13, 5.0, 1.78), ("Sn", 50, 14, 5.0, 1.96),
    ("Sb", 51, 15, 5.0, 2.05), ("Te", 52, 16, 5.0, 2.10),
    ("I",  53, 17, 5.0, 2.66), ("Xe", 54, 18, 5.0, 2.60),
    # Period 6 (group 3 placeholder for lanthanide block)
    ("Cs", 55,  1, 6.0, 0.79), ("Ba", 56,  2, 6.0, 0.89),
    ("*",   0,  3, 6.0, None),
    ("Hf", 72,  4, 6.0, 1.30), ("Ta", 73,  5, 6.0, 1.50),
    ("W",  74,  6, 6.0, 2.36), ("Re", 75,  7, 6.0, 1.90),
    ("Os", 76,  8, 6.0, 2.20), ("Ir", 77,  9, 6.0, 2.20),
    ("Pt", 78, 10, 6.0, 2.28), ("Au", 79, 11, 6.0, 2.54),
    ("Hg", 80, 12, 6.0, 2.00), ("Tl", 81, 13, 6.0, 1.62),
    ("Pb", 82, 14, 6.0, 2.33), ("Bi", 83, 15, 6.0, 2.02),
    ("Po", 84, 16, 6.0, 2.00), ("At", 85, 17, 6.0, 2.20),
    ("Rn", 86, 18, 6.0, None),
    # Period 7 (group 3 placeholder for actinide block)
    ("Fr", 87,  1, 7.0, 0.70), ("Ra", 88,  2, 7.0, 0.90),
    ("*",   0,  3, 7.0, None),
    ("Rf",104,  4, 7.0, None), ("Db",105,  5, 7.0, None),
    ("Sg",106,  6, 7.0, None), ("Bh",107,  7, 7.0, None),
    ("Hs",108,  8, 7.0, None), ("Mt",109,  9, 7.0, None),
    ("Ds",110, 10, 7.0, None), ("Rg",111, 11, 7.0, None),
    ("Cn",112, 12, 7.0, None), ("Nh",113, 13, 7.0, None),
    ("Fl",114, 14, 7.0, None), ("Mc",115, 15, 7.0, None),
    ("Lv",116, 16, 7.0, None), ("Ts",117, 17, 7.0, None),
    ("Og",118, 18, 7.0, None),
    # Lanthanides (detached row 8.5)
    ("La", 57,  3, 8.5, 1.10), ("Ce", 58,  4, 8.5, 1.12),
    ("Pr", 59,  5, 8.5, 1.13), ("Nd", 60,  6, 8.5, 1.14),
    ("Pm", 61,  7, 8.5, 1.13), ("Sm", 62,  8, 8.5, 1.17),
    ("Eu", 63,  9, 8.5, 1.20), ("Gd", 64, 10, 8.5, 1.20),
    ("Tb", 65, 11, 8.5, 1.10), ("Dy", 66, 12, 8.5, 1.22),
    ("Ho", 67, 13, 8.5, 1.23), ("Er", 68, 14, 8.5, 1.24),
    ("Tm", 69, 15, 8.5, 1.25), ("Yb", 70, 16, 8.5, 1.10),
    ("Lu", 71, 17, 8.5, 1.27),
    # Actinides (detached row 9.5)
    ("Ac", 89,  3, 9.5, 1.10), ("Th", 90,  4, 9.5, 1.30),
    ("Pa", 91,  5, 9.5, 1.50), ("U",  92,  6, 9.5, 1.38),
    ("Np", 93,  7, 9.5, 1.36), ("Pu", 94,  8, 9.5, 1.28),
    ("Am", 95,  9, 9.5, 1.30), ("Cm", 96, 10, 9.5, 1.30),
    ("Bk", 97, 11, 9.5, 1.30), ("Cf", 98, 12, 9.5, 1.30),
    ("Es", 99, 13, 9.5, 1.30), ("Fm",100, 14, 9.5, 1.30),
    ("Md",101, 15, 9.5, 1.30), ("No",102, 16, 9.5, 1.30),
    ("Lr",103, 17, 9.5, None),
]
# fmt: on

df = pd.DataFrame(elements, columns=["symbol", "atomic_num", "group", "row", "en"])

# Group number labels (1-18, above main table — row=0.3 appears above row=1.0 with scale_y_reverse)
df_groups = pd.DataFrame({"group": list(range(1, 19)), "row": [0.3] * 18, "label": [str(g) for g in range(1, 19)]})

# Period number labels (1-7, left of main table — group=0.2 is left of group=1 tiles)
df_periods = pd.DataFrame(
    {"group": [0.2] * 7, "row": [float(p) for p in range(1, 8)], "label": [str(p) for p in range(1, 8)]}
)

# Text color: computed from tile luminance so labels stay legible on colored tiles
cmap_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])
en_min, en_max = df["en"].min(), df["en"].max()
en_normed = (df["en"].fillna(en_min) - en_min) / (en_max - en_min)
rgba = cmap_seq(en_normed.values)
lum = 0.2126 * rgba[:, 0] + 0.7152 * rgba[:, 1] + 0.0722 * rgba[:, 2]
df["text_color"] = np.where(df["en"].isna(), INK_SOFT, np.where(lum > 0.38, "#1A1A17", "#F0EFE8"))

df["label_num"] = np.where(df["atomic_num"] > 0, df["atomic_num"].astype(str), "")
df["en_str"] = ["" if pd.isna(v) else f"{v:.2f}" for v in df["en"]]

title = "heatmap-periodic-table · python · plotnine · anyplot.ai"
n = len(title)
title_size = max(8, round(12 * 67 / n))

plot = (
    ggplot(df, aes(x="group", y="row"))
    + geom_tile(aes(fill="en"), width=0.92, height=0.92)
    # Element symbol — centre of each tile
    + geom_text(aes(label="symbol", color="text_color"), size=2.6, fontweight="bold", va="center", ha="center")
    # Atomic number — top-left corner
    + geom_text(
        aes(label="label_num", color="text_color"), size=1.7, nudge_x=-0.36, nudge_y=-0.28, va="center", ha="left"
    )
    # Pauling EN value — bottom centre
    + geom_text(aes(label="en_str", color="text_color"), size=1.5, nudge_y=0.27, va="center", ha="center")
    # Group numbers (1-18) above the table
    + geom_text(
        data=df_groups,
        mapping=aes(x="group", y="row", label="label"),
        color=INK_SOFT,
        size=1.5,
        ha="center",
        va="center",
        inherit_aes=False,
    )
    # Period numbers (1-7) to the left of the table
    + geom_text(
        data=df_periods,
        mapping=aes(x="group", y="row", label="label"),
        color=INK_SOFT,
        size=1.5,
        ha="center",
        va="center",
        inherit_aes=False,
    )
    + scale_fill_gradient(
        low="#009E73", high="#4467A3", na_value=NA_TILE, name="Pauling\nElectronegativity", guide=guide_colorbar()
    )
    + scale_color_identity(guide=None)
    + scale_y_reverse()
    + coord_fixed(ratio=1)
    + labs(title=title)
    + theme_void()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(color=INK, size=title_size, ha="center"),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.3),
        legend_text=element_text(color=INK_SOFT, size=6),
        legend_title=element_text(color=INK, size=8),
        legend_position="right",
        plot_margin=0.05,
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
