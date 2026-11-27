#' anyplot.ai
#' hexbin-basic: Basic Hexbin Plot
#' Library: ggplot2 4.0.3 | R 4.6.1
#' Quality: 82/100 | Updated: 2026-11-27

library(ggplot2)
library(ragg)

# Theme tokens (Imprint palette, theme-adaptive chrome)
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
GRID_COLOR  <- if (THEME == "light") "#1A1A1726" else "#F0EFE826"

# Imprint sequential ramp for fields (filled cells), stops per theme
SEQ_FIELDS <- if (THEME == "light") {
    list(colours = c("#66E2B2", "#009E73", "#024582", "#351E45"), values = c(0, 0.369, 0.803, 1))
} else {
    list(colours = c("#404C02", "#009E73", "#CDD9FF"), values = c(0, 0.487, 1))
}

# Columns: set these to your table's column names
EASTING  <- "Easting (km from city center)"   # role: x
NORTHING <- "Northing (km from city center)"  # role: y
COUNT    <- "Count"                           # role: legend title

# Data: replace this block with your own table, for example df <- read.csv("gps.csv", check.names = FALSE)
set.seed(42)
df <- tibble::tibble(
    !!EASTING := c(
        rnorm(5000, mean =  0.4, sd = 1.1),
        rnorm(3000, mean = -2.6, sd = 0.6),
        rnorm(2000, mean =  3.0, sd = 0.8)
    ),
    !!NORTHING := c(
        rnorm(5000, mean =  0.2, sd = 0.9),
        rnorm(3000, mean =  2.3, sd = 0.5),
        rnorm(2000, mean = -1.6, sd = 0.8)
    )
)

plot_title <- "hexbin-basic · r · ggplot2 · anyplot.ai"
n_chars    <- nchar(plot_title)
title_fs   <- if (n_chars > 67) round(12 * 67 / n_chars) else 12

# Hexagonal binning: 35 hexagons across the easting range (pointy-top, axial coordinates)
BINS   <- 35
x      <- df[[EASTING]]
y      <- df[[NORTHING]]
hex_r  <- diff(range(x)) / BINS / sqrt(3)
fq     <- (sqrt(3) / 3 * x - y / 3) / hex_r
fr     <- (2 / 3 * y) / hex_r
fs     <- -fq - fr
rq     <- round(fq)
rr     <- round(fr)
rs     <- round(fs)
dq     <- abs(rq - fq)
dr     <- abs(rr - fr)
ds     <- abs(rs - fs)
fix_q  <- dq > dr & dq > ds
fix_r  <- !fix_q & dr > ds
rq     <- ifelse(fix_q, -rr - rs, rq)
rr     <- ifelse(fix_r, -rq - rs, rr)
cells  <- as.data.frame(table(q = rq, r = rr), responseName = "n")
cells  <- cells[cells$n > 0, ]
cells$q <- as.numeric(as.character(cells$q))
cells$r <- as.numeric(as.character(cells$r))
angles <- (30 + 60 * 0:5) * pi / 180
hexes  <- data.frame(
    cell = rep(seq_len(nrow(cells)), each = 6),
    px   = rep(hex_r * sqrt(3) * (cells$q + cells$r / 2), each = 6) + hex_r * cos(angles),
    py   = rep(hex_r * 1.5 * cells$r, each = 6) + hex_r * sin(angles),
    n    = rep(cells$n, each = 6)
)

# Plot
p <- ggplot(hexes, aes(x = px, y = py, group = cell, fill = n)) +
    geom_polygon(color = NA) +
    scale_fill_gradientn(
        colours = SEQ_FIELDS$colours,
        values  = SEQ_FIELDS$values,
        guide   = guide_colorbar(
            barwidth  = unit(0.6, "cm"),
            barheight = unit(4.5, "cm"),
            ticks     = FALSE
        )
    ) +
    labs(title = plot_title, x = EASTING, y = NORTHING, fill = COUNT) +
    theme_minimal(base_size = 8) +
    theme(
        plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
        panel.background  = element_rect(fill = PAGE_BG, color = NA),
        panel.border      = element_blank(),
        panel.grid.major  = element_line(color = GRID_COLOR, linewidth = 0.4),
        panel.grid.minor  = element_blank(),
        axis.title        = element_text(color = INK, size = 10),
        axis.text         = element_text(color = INK_SOFT, size = 8),
        axis.line         = element_line(color = INK_SOFT, linewidth = 0.4),
        axis.ticks        = element_blank(),
        plot.title        = element_text(
            color  = INK,
            size   = title_fs,
            face   = "bold",
            margin = margin(b = 8)
        ),
        legend.background = element_rect(fill = ELEVATED_BG, color = NA),
        legend.text       = element_text(color = INK_SOFT, size = 8),
        legend.title      = element_text(color = INK, size = 10),
        plot.margin       = margin(12, 15, 12, 12, "pt")
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
