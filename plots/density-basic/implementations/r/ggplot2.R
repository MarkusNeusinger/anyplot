#' anyplot.ai
#' density-basic: Basic Density Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 87/100 | Created: 2026-05-30

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# Theme tokens — Imprint palette, theme-adaptive chrome
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"

IMPRINT_PALETTE <- c(
    "#009E73",  # 1 — brand green (ALWAYS first series)
    "#C475FD",  # 2 — lavender
    "#4467A3",  # 3 — blue
    "#BD8233",  # 4 — ochre
    "#AE3030",  # 5 — matte red
    "#2ABCCD",  # 6 — cyan
    "#954477",  # 7 — rose
    "#99B314"   # 8 — lime
)
BRAND <- IMPRINT_PALETTE[1]

# Data — simulated plant seedling heights (mm) from two cultivars mixed in one batch,
# producing a characteristic bimodal distribution (short- and tall-growing varieties)
heights_short <- rnorm(420, mean = 38, sd = 6)
heights_tall  <- rnorm(180, mean = 72, sd = 9)
df <- data.frame(height = c(heights_short, heights_tall))

# Plot
p <- ggplot(df, aes(x = height)) +
    geom_density(
        fill      = BRAND,
        color     = BRAND,
        alpha     = 0.22,
        linewidth = 1.2,
        bw        = "sj"
    ) +
    geom_rug(
        color  = BRAND,
        alpha  = 0.12,
        length = unit(0.018, "npc"),
        linewidth = 0.4
    ) +
    scale_x_continuous(expand = expansion(mult = c(0.02, 0.02))) +
    scale_y_continuous(expand = expansion(mult = c(0.0, 0.08))) +
    labs(
        x     = "Seedling Height (mm)",
        y     = "Density",
        title = "density-basic · r · ggplot2 · anyplot.ai"
    ) +
    theme_minimal(base_size = 8) +
    theme(
        plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
        panel.background = element_rect(fill = PAGE_BG, color = NA),
        panel.grid.major.y = element_line(color = INK_SOFT, linewidth = 0.2),
        panel.grid.major.x = element_blank(),
        panel.grid.minor   = element_blank(),
        panel.border       = element_blank(),
        axis.title   = element_text(color = INK,      size = 10),
        axis.text    = element_text(color = INK_SOFT, size = 8),
        axis.line    = element_line(color = INK_SOFT, linewidth = 0.4),
        axis.ticks   = element_line(color = INK_SOFT, linewidth = 0.3),
        plot.title   = element_text(color = INK, size = 12, face = "bold",
                                    margin = margin(b = 10)),
        plot.margin  = margin(20, 25, 15, 15)
    )

# Save
ggsave(
    filename = sprintf("plot-%s.png", THEME),
    plot     = p,
    device   = ragg::agg_png,
    width    = 8,
    height   = 4.5,
    units    = "in",
    dpi      = 400
)
