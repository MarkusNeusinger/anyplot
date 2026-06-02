#' anyplot.ai
#' scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 85/100 | Created: 2026-06-02

library(ggplot2)
library(ragg)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

IMPRINT_PALETTE <- c(
    "#009E73",  # 1 — brand green (5th roots of unity)
    "#C475FD",  # 2 — lavender (arbitrary points)
    "#4467A3",  # 3 — blue
    "#BD8233",  # 4 — ochre
    "#AE3030",  # 5 — matte red
    "#2ABCCD",  # 6 — cyan
    "#954477",  # 7 — rose
    "#99B314"   # 8 — lime
)

GRID_COLOR <- adjustcolor(INK, alpha.f = 0.12)

# Data: 5th roots of unity (z^5 = 1, evenly spaced on the unit circle)
n      <- 5
angles <- 2 * pi * (0:(n - 1)) / n

unity_real <- cos(angles)
unity_imag <- sin(angles)

# Rectangular form labels: a + bi (inlined)
unity_labels <- mapply(
    function(r, i) if (i >= 0) sprintf("%.2f + %.2fi", r, i) else sprintf("%.2f - %.2fi", r, abs(i)),
    unity_real, unity_imag
)

# Two arbitrary complex numbers outside the unit circle
arb_real   <- c( 1.30,  -0.60)
arb_imag   <- c( 0.70,  -1.40)
arb_angles <- atan2(arb_imag, arb_real)
arb_labels <- mapply(
    function(r, i) if (i >= 0) sprintf("%.2f + %.2fi", r, i) else sprintf("%.2f - %.2fi", r, abs(i)),
    arb_real, arb_imag
)

# Combined data frame
df <- data.frame(
    real     = c(unity_real, arb_real),
    imag     = c(unity_imag, arb_imag),
    label    = c(unity_labels, arb_labels),
    angle    = c(angles, arb_angles),
    category = factor(
        c(rep("5th Roots of Unity", n), rep("Arbitrary Points", 2)),
        levels = c("5th Roots of Unity", "Arbitrary Points")
    ),
    stringsAsFactors = FALSE
)

# Nudge labels outward from origin for readability
nudge_scale <- 0.30
df$nx <- cos(df$angle) * nudge_scale
df$ny <- sin(df$angle) * nudge_scale
# Per-point hjust: left-align rightward labels so text clears the arrowhead
df$hjust <- ifelse(cos(df$angle) > 0.8, 0, ifelse(cos(df$angle) < -0.8, 1, 0.5))

# Unit circle reference path
theta_seq <- seq(0, 2 * pi, length.out = 300)
circle_df <- data.frame(x = cos(theta_seq), y = sin(theta_seq))

# Title (48 chars — below 67-char baseline, no font shrink needed)
title_str  <- "scatter-complex-plane · r · ggplot2 · anyplot.ai"
title_size <- max(8, round(12 * 67 / max(nchar(title_str), 67)))

category_colors <- c(
    "5th Roots of Unity" = IMPRINT_PALETTE[1],
    "Arbitrary Points"   = IMPRINT_PALETTE[2]
)

p <- ggplot() +
    # Unit circle (dashed reference)
    geom_path(
        data = circle_df, aes(x = x, y = y),
        color = INK_SOFT, linetype = "dashed", linewidth = 0.5
    ) +
    # Origin axes (horizontal and vertical lines through 0)
    geom_hline(yintercept = 0, color = INK_SOFT, linewidth = 0.5) +
    geom_vline(xintercept = 0, color = INK_SOFT, linewidth = 0.5) +
    # Vectors: arrows from origin to each complex number
    geom_segment(
        data = df,
        aes(x = 0, y = 0, xend = real, yend = imag, color = category),
        arrow     = arrow(length = unit(0.12, "inches"), type = "closed"),
        linewidth  = 0.9,
        alpha     = 0.85
    ) +
    # Points
    geom_point(
        data = df,
        aes(x = real, y = imag, color = category),
        size = 3.5
    ) +
    # Labels: rectangular form (a + bi), nudged outward from origin
    geom_text(
        data = df,
        aes(x = real + nx, y = imag + ny, label = label, color = category, hjust = hjust),
        size        = 3.2,
        show.legend = FALSE
    ) +
    scale_color_manual(values = category_colors, name = NULL) +
    coord_equal(xlim = c(-2.1, 2.1), ylim = c(-2.1, 2.1)) +
    labs(
        title = title_str,
        x     = "Real",
        y     = "Imaginary"
    ) +
    theme_minimal(base_size = 8) +
    theme(
        plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
        panel.background  = element_rect(fill = PAGE_BG, color = NA),
        panel.grid.major  = element_line(color = GRID_COLOR, linewidth = 0.3),
        panel.grid.minor  = element_blank(),
        panel.border      = element_blank(),
        axis.title        = element_text(color = INK, size = 10),
        axis.text         = element_text(color = INK_SOFT, size = 8),
        plot.title        = element_text(color = INK, size = title_size, face = "bold"),
        legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.3),
        legend.text       = element_text(color = INK_SOFT, size = 8),
        legend.position   = "bottom",
        plot.margin       = margin(t = 20, r = 20, b = 20, l = 20)
    )

ggsave(
    filename = sprintf("plot-%s.png", THEME),
    plot     = p,
    device   = ragg::agg_png,
    width    = 6,
    height   = 6,
    units    = "in",
    dpi      = 400
)
