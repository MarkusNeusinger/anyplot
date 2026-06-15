""" anyplot.ai
heatmap-periodic-table: Periodic Table Property Heatmap
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 90/100 | Created: 2026-06-15
"""

import os

import pandas as pd
from lets_plot import *
from lets_plot.export import ggsave


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
MISSING_FILL = "#C4C4BE" if THEME == "light" else "#383835"

# Fixed luminance-based text colors — tile fill is theme-independent so text choice is too
LIGHT_TEXT = "#F0EFE8"  # for dark tiles (relative luminance < 0.35)
DARK_TEXT = "#1A1A17"  # for light tiles (relative luminance >= 0.35)

# Data: (atomic_number, symbol, group_pos, period_pos, pauling_en)
# period_pos 8.5 = lanthanide row below main table, 9.5 = actinide row
ELEMENTS = [
    # Period 1
    (1, "H", 1, 1, 2.20),
    (2, "He", 18, 1, None),
    # Period 2
    (3, "Li", 1, 2, 0.98),
    (4, "Be", 2, 2, 1.57),
    (5, "B", 13, 2, 2.04),
    (6, "C", 14, 2, 2.55),
    (7, "N", 15, 2, 3.04),
    (8, "O", 16, 2, 3.44),
    (9, "F", 17, 2, 3.98),
    (10, "Ne", 18, 2, None),
    # Period 3
    (11, "Na", 1, 3, 0.93),
    (12, "Mg", 2, 3, 1.31),
    (13, "Al", 13, 3, 1.61),
    (14, "Si", 14, 3, 1.90),
    (15, "P", 15, 3, 2.19),
    (16, "S", 16, 3, 2.58),
    (17, "Cl", 17, 3, 3.16),
    (18, "Ar", 18, 3, None),
    # Period 4
    (19, "K", 1, 4, 0.82),
    (20, "Ca", 2, 4, 1.00),
    (21, "Sc", 3, 4, 1.36),
    (22, "Ti", 4, 4, 1.54),
    (23, "V", 5, 4, 1.63),
    (24, "Cr", 6, 4, 1.66),
    (25, "Mn", 7, 4, 1.55),
    (26, "Fe", 8, 4, 1.83),
    (27, "Co", 9, 4, 1.88),
    (28, "Ni", 10, 4, 1.91),
    (29, "Cu", 11, 4, 1.90),
    (30, "Zn", 12, 4, 1.65),
    (31, "Ga", 13, 4, 1.81),
    (32, "Ge", 14, 4, 2.01),
    (33, "As", 15, 4, 2.18),
    (34, "Se", 16, 4, 2.55),
    (35, "Br", 17, 4, 2.96),
    (36, "Kr", 18, 4, 3.00),
    # Period 5
    (37, "Rb", 1, 5, 0.82),
    (38, "Sr", 2, 5, 0.95),
    (39, "Y", 3, 5, 1.22),
    (40, "Zr", 4, 5, 1.33),
    (41, "Nb", 5, 5, 1.60),
    (42, "Mo", 6, 5, 2.16),
    (43, "Tc", 7, 5, 1.90),
    (44, "Ru", 8, 5, 2.20),
    (45, "Rh", 9, 5, 2.20),
    (46, "Pd", 10, 5, 2.20),
    (47, "Ag", 11, 5, 1.93),
    (48, "Cd", 12, 5, 1.69),
    (49, "In", 13, 5, 1.78),
    (50, "Sn", 14, 5, 1.96),
    (51, "Sb", 15, 5, 2.05),
    (52, "Te", 16, 5, 2.10),
    (53, "I", 17, 5, 2.66),
    (54, "Xe", 18, 5, 2.60),
    # Period 6 — group 3 empty; La–Lu in f-block row below
    (55, "Cs", 1, 6, 0.79),
    (56, "Ba", 2, 6, 0.89),
    (72, "Hf", 4, 6, 1.30),
    (73, "Ta", 5, 6, 1.50),
    (74, "W", 6, 6, 2.36),
    (75, "Re", 7, 6, 1.90),
    (76, "Os", 8, 6, 2.20),
    (77, "Ir", 9, 6, 2.20),
    (78, "Pt", 10, 6, 2.28),
    (79, "Au", 11, 6, 2.54),
    (80, "Hg", 12, 6, 2.00),
    (81, "Tl", 13, 6, 1.62),
    (82, "Pb", 14, 6, 2.33),
    (83, "Bi", 15, 6, 2.02),
    (84, "Po", 16, 6, 2.00),
    (85, "At", 17, 6, 2.20),
    (86, "Rn", 18, 6, 2.20),
    # Period 7 — group 3 empty; Ac–Lr in f-block row below
    (87, "Fr", 1, 7, 0.70),
    (88, "Ra", 2, 7, 0.90),
    (104, "Rf", 4, 7, None),
    (105, "Db", 5, 7, None),
    (106, "Sg", 6, 7, None),
    (107, "Bh", 7, 7, None),
    (108, "Hs", 8, 7, None),
    (109, "Mt", 9, 7, None),
    (110, "Ds", 10, 7, None),
    (111, "Rg", 11, 7, None),
    (112, "Cn", 12, 7, None),
    (113, "Nh", 13, 7, None),
    (114, "Fl", 14, 7, None),
    (115, "Mc", 15, 7, None),
    (116, "Lv", 16, 7, None),
    (117, "Ts", 17, 7, None),
    (118, "Og", 18, 7, None),
    # Lanthanides: period_pos=8.5, groups 3–17
    (57, "La", 3, 8.5, 1.10),
    (58, "Ce", 4, 8.5, 1.12),
    (59, "Pr", 5, 8.5, 1.13),
    (60, "Nd", 6, 8.5, 1.14),
    (61, "Pm", 7, 8.5, None),
    (62, "Sm", 8, 8.5, 1.17),
    (63, "Eu", 9, 8.5, None),
    (64, "Gd", 10, 8.5, 1.20),
    (65, "Tb", 11, 8.5, None),
    (66, "Dy", 12, 8.5, 1.22),
    (67, "Ho", 13, 8.5, 1.23),
    (68, "Er", 14, 8.5, 1.24),
    (69, "Tm", 15, 8.5, 1.25),
    (70, "Yb", 16, 8.5, None),
    (71, "Lu", 17, 8.5, 1.27),
    # Actinides: period_pos=9.5, groups 3–17
    (89, "Ac", 3, 9.5, 1.10),
    (90, "Th", 4, 9.5, 1.30),
    (91, "Pa", 5, 9.5, 1.50),
    (92, "U", 6, 9.5, 1.38),
    (93, "Np", 7, 9.5, 1.36),
    (94, "Pu", 8, 9.5, 1.28),
    (95, "Am", 9, 9.5, 1.13),
    (96, "Cm", 10, 9.5, 1.28),
    (97, "Bk", 11, 9.5, 1.30),
    (98, "Cf", 12, 9.5, 1.30),
    (99, "Es", 13, 9.5, 1.30),
    (100, "Fm", 14, 9.5, 1.30),
    (101, "Md", 15, 9.5, 1.30),
    (102, "No", 16, 9.5, 1.30),
    (103, "Lr", 17, 9.5, None),
]

df = pd.DataFrame(ELEMENTS, columns=["atomic_number", "symbol", "group_pos", "period_pos", "electronegativity"])
df["x"] = df["group_pos"]
df["y"] = -df["period_pos"]
df["label_num"] = df["atomic_number"].astype(str)

df_colored = df[df["electronegativity"].notna()].copy()
df_missing = df[df["electronegativity"].isna()].copy()

# Luminance-adaptive text: lerp gradient endpoints in sRGB, compute WCAG relative luminance
# Gradient: #009E73 (low EN) → #4467A3 (high EN)
en_min = df_colored["electronegativity"].min()
en_max = df_colored["electronegativity"].max()
t = (df_colored["electronegativity"] - en_min) / (en_max - en_min)
r_srgb = (0x00 + t * (0x44 - 0x00)) / 255.0
g_srgb = (0x9E + t * (0x67 - 0x9E)) / 255.0
b_srgb = (0x73 + t * (0xA3 - 0x73)) / 255.0
r_lin = (r_srgb / 12.92).where(r_srgb <= 0.04045, ((r_srgb + 0.055) / 1.055) ** 2.4)
g_lin = (g_srgb / 12.92).where(g_srgb <= 0.04045, ((g_srgb + 0.055) / 1.055) ** 2.4)
b_lin = (b_srgb / 12.92).where(b_srgb <= 0.04045, ((b_srgb + 0.055) / 1.055) ** 2.4)
luminance = 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin
df_colored["sym_color"] = luminance.apply(lambda lum: LIGHT_TEXT if lum < 0.35 else DARK_TEXT)

df_sym_light = df_colored[df_colored["sym_color"] == LIGHT_TEXT]
df_sym_dark = df_colored[df_colored["sym_color"] == DARK_TEXT]

title = "Electronegativity · heatmap-periodic-table · python · letsplot · anyplot.ai"
title_n = len(title)
title_size = max(11, round(16 * 67 / title_n))

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_blank(),
    panel_grid_minor=element_blank(),
    axis_title=element_blank(),
    axis_text=element_blank(),
    axis_ticks=element_blank(),
    axis_line=element_blank(),
    plot_title=element_text(color=INK, size=title_size),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=INK, size=11),
)

plot = (
    ggplot()
    # Grey tiles for elements with no defined electronegativity
    + geom_tile(
        mapping=aes(x="x", y="y"),
        data=df_missing,
        fill=MISSING_FILL,
        color=PAGE_BG,
        size=0.4,
        width=0.93,
        height=0.93,
        tooltips=layer_tooltips().line("@symbol (#@atomic_number)").line("EN: not defined"),
    )
    # Colored tiles — Imprint sequential: green (low EN) → blue (high EN)
    + geom_tile(
        mapping=aes(x="x", y="y", fill="electronegativity"),
        data=df_colored,
        color=PAGE_BG,
        size=0.4,
        width=0.93,
        height=0.93,
        tooltips=layer_tooltips()
        .line("@symbol (#@atomic_number)")
        .line("Electronegativity: @electronegativity Pauling"),
    )
    # Element symbols — luminance-adaptive: LIGHT_TEXT on dark tiles, DARK_TEXT on light tiles
    + geom_text(
        mapping=aes(x="x", y="y", label="symbol"),
        data=df_sym_light,
        color=LIGHT_TEXT,
        size=3.0,
        fontface="bold",
        vjust=0.6,
    )
    + geom_text(
        mapping=aes(x="x", y="y", label="symbol"),
        data=df_sym_dark,
        color=DARK_TEXT,
        size=3.0,
        fontface="bold",
        vjust=0.6,
    )
    + geom_text(
        mapping=aes(x="x", y="y", label="symbol"), data=df_missing, color=INK_SOFT, size=3.0, fontface="bold", vjust=0.6
    )
    # Atomic numbers — top-left corner; LIGHT_TEXT on colored tiles, INK_SOFT on grey tiles
    + geom_text(
        mapping=aes(x="x", y="y", label="label_num"),
        data=df_colored,
        color=LIGHT_TEXT,
        size=1.7,
        nudge_x=-0.30,
        nudge_y=0.30,
        hjust=0,
    )
    + geom_text(
        mapping=aes(x="x", y="y", label="label_num"),
        data=df_missing,
        color=INK_SOFT,
        size=1.7,
        nudge_x=-0.30,
        nudge_y=0.30,
        hjust=0,
    )
    + scale_fill_gradient(low="#009E73", high="#4467A3", name="Pauling\nEN", na_value=MISSING_FILL)
    + labs(title=title)
    + ggsize(800, 450)
    + anyplot_theme
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
