#' anyplot.ai
#' sn-curve-basic: S-N Curve (Wöhler Curve)
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 88/100 | Created: 2026-05-20

library(ggplot2)
library(dplyr)
library(scales)
library(ragg)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"
OKABE_ITO   <- c("#009E73", "#D55E00", "#0072B2", "#CC79A7",
                 "#E69F00", "#56B4E9", "#F0E442")
GRID        <- adjustcolor(INK_SOFT, alpha.f = 0.25)

# AISI 1045 Steel material properties (MPa)
sigma_u <- 750   # Ultimate tensile strength
sigma_y <- 530   # Yield strength
sigma_e <- 250   # Endurance limit

# Basquin equation: log10(N) = C0 - k * log10(stress)
k  <- 10
C0 <- 30

# N at endurance limit — left boundary of infinite-life zone
N_endurance <- 10^(C0 - k * log10(sigma_e))

# Fatigue test specimens: multiple replicates per stress level
stress_levels <- c(620, 580, 540, 500, 460, 420, 390, 360, 330, 300, 275, 260)
reps          <- c(2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3)

df <- data.frame(stress = rep(stress_levels, reps)) |>
    mutate(cycles = 10^(C0 - k * log10(stress) + rnorm(n(), 0, 0.12)))

# Basquin fit line — log-spaced in cycle direction for accurate log-scale rendering
fit_df <- data.frame(
    cycles = 10^seq(log10(12), log10(N_endurance * 0.998), length.out = 300)
) |> mutate(stress = 10^((C0 - log10(cycles)) / k))

# Plot
p <- ggplot() +
    # Infinite-life zone: stronger fill to emphasize key engineering insight
    annotate("rect",
        xmin = N_endurance, xmax = 10^8,
        ymin = 180, ymax = sigma_e,
        fill = OKABE_ITO[5], alpha = 0.14
    ) +
    # Reference lines for key material properties
    geom_hline(yintercept = sigma_u, linetype = "dashed",
               color = OKABE_ITO[2], linewidth = 0.65, alpha = 0.85) +
    geom_hline(yintercept = sigma_y, linetype = "dashed",
               color = OKABE_ITO[3], linewidth = 0.65, alpha = 0.85) +
    # Endurance limit thicker — the key design threshold for infinite life
    geom_hline(yintercept = sigma_e, linetype = "longdash",
               color = OKABE_ITO[5], linewidth = 1.1, alpha = 0.95) +
    # Basquin fit curve
    geom_line(data = fit_df, aes(x = cycles, y = stress),
              color = INK_MUTED, linewidth = 1.0) +
    # Test data scatter (multiple replicates per stress level)
    geom_point(data = df, aes(x = cycles, y = stress),
               shape = 21, size = 3.0, stroke = 0.5,
               color = OKABE_ITO[1], fill = OKABE_ITO[1], alpha = 0.85) +
    # Reference line labels — right-aligned at x = 10^7.5
    annotate("text", x = 10^7.5, y = sigma_u * 1.05,
             label = "Ultimate Strength (750 MPa)",
             color = OKABE_ITO[2], hjust = 1, vjust = 0, size = 4.0) +
    annotate("text", x = 10^7.5, y = sigma_y * 1.05,
             label = "Yield Strength (530 MPa)",
             color = OKABE_ITO[3], hjust = 1, vjust = 0, size = 4.0) +
    annotate("text", x = 10^7.5, y = sigma_e * 1.08,
             label = "Endurance Limit (250 MPa)",
             color = OKABE_ITO[5], hjust = 1, vjust = 0, size = 4.0,
             fontface = "bold") +
    # Infinite-life region label inside shaded zone
    annotate("text", x = 10^7.2, y = 210,
             label = "Infinite Life\nRegion",
             color = INK_MUTED, hjust = 0.5, size = 3.2, fontface = "italic") +
    # Log-log axes
    scale_x_log10(
        limits = c(10, 10^8),
        breaks = 10^(1:8),
        labels = scales::trans_format("log10", scales::math_format(10^.x))
    ) +
    scale_y_log10(
        limits = c(180, 900),
        breaks = c(200, 300, 400, 500, 600, 700, 800),
        labels = scales::comma_format(accuracy = 1)
    ) +
    labs(
        title   = "sn-curve-basic · r · ggplot2 · anyplot.ai",
        x       = "Cycles to Failure",
        y       = "Stress Amplitude (MPa)",
        caption = "Basquin model: log N = 30 − 10 · log σ  |  AISI 1045 steel"
    ) +
    theme_minimal(base_size = 8) +
    theme(
        plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
        panel.background = element_rect(fill = PAGE_BG, color = NA),
        panel.grid.major = element_line(color = GRID, linewidth = 0.3),
        panel.grid.minor = element_blank(),
        panel.border     = element_blank(),
        axis.line        = element_line(color = INK_SOFT, linewidth = 0.5),
        axis.ticks       = element_blank(),
        axis.title       = element_text(color = INK, size = 10),
        axis.text        = element_text(color = INK_SOFT, size = 8),
        plot.title       = element_text(color = INK, size = 12),
        plot.caption     = element_text(color = INK_MUTED, size = 7, hjust = 1),
        plot.margin      = margin(10, 20, 10, 10, "pt")
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
