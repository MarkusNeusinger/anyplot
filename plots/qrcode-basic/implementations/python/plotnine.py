"""anyplot.ai
qrcode-basic: Basic QR Code Generator
Library: plotnine 0.15.7 | Python 3.13.14
Quality: 87/100 | Created: 2026-06-24
"""

import os
import sys


_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if p and os.path.abspath(p) != _script_dir]

import pandas as pd
import qrcode
import qrcode.constants
from plotnine import (
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_tile,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_void,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# QR module colors — dark on light bg / light on dark bg for scannability
MODULE_ON = "#1A1A17" if THEME == "light" else "#F0EFE8"
MODULE_OFF = PAGE_BG  # quiet zone matches page background

# Data — encode anyplot.ai URL with error correction level M (15%)
URL = "https://anyplot.ai"
qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=1, border=4)
qr.add_data(URL)
qr.make(fit=True)

matrix = qr.get_matrix()
n = len(matrix)

rows = []
for r, row in enumerate(matrix):
    for c, val in enumerate(row):
        rows.append({"x": c, "y": n - 1 - r, "module": "on" if val else "off"})
df = pd.DataFrame(rows)

# Plot
title = "qrcode-basic · python · plotnine · anyplot.ai"

plot = (
    ggplot(df, aes(x="x", y="y", fill="module"))
    + geom_tile(width=1.02, height=1.02)
    + scale_fill_manual(values={"on": MODULE_ON, "off": MODULE_OFF})
    + coord_fixed()
    + labs(title=title, subtitle=URL)
    + theme_void()
    + theme(
        figure_size=(6, 6),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(color=INK, size=12, ha="center"),
        plot_subtitle=element_text(color=INK_SOFT, size=9, ha="center"),
        legend_position="none",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in")
