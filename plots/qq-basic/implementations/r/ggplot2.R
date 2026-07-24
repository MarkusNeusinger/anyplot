#' anyplot.ai
#' qq-basic: Basic Q-Q Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 85/100 | Created: 2026-07-24

library(ggplot2)
library(ragg)

set.seed(42)

# --- Theme tokens -------------------------------------------------------
THEME <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c(
    "#009E73", "#C475FD", "#4467A3", "#BD8233",
    "#AE3030", "#2ABCCD", "#954477", "#99B314"
)

# --- Data -----------------------------------------------------------------
# Shaft diameter measurements (mm) from a machining quality-control line —
# checking the normality assumption before running a process-capability test.
n <- 150
shaft_diameter_mm <- rnorm(n, mean = 25.00, sd = 0.08)
df <- tibble::tibble(sample = shaft_diameter_mm)

# --- Confidence envelope ----------------------------------------------------
# Pointwise 95% normal-theory band around the reference line (the classic
# car::qqPlot approach): the standard error of each order statistic is scaled
# by the local normal density, giving a band that narrows in the dense center
# and widens in the tails — exactly where deviations are most informative.
p_i <- (seq_len(n) - 0.5) / n
z <- qnorm(p_i)
mu <- mean(shaft_diameter_mm)
sigma <- sd(shaft_diameter_mm)
se <- (sigma / dnorm(z)) * sqrt(p_i * (1 - p_i) / n)
band <- tibble::tibble(
    z = z,
    fit = mu + sigma * z,
    lower = fit - qnorm(0.975) * se,
    upper = fit + qnorm(0.975) * se
)

# --- Plot -------------------------------------------------------------------
# stat_qq_line draws the 45-degree reference line (Imprint "neutral" anchor,
# since it is a baseline/reference element rather than a data series); the
# ribbon is the 95% pointwise confidence envelope under normality, showing
# whether the tail deviations exceed ordinary sampling variation.
p <- ggplot(df, aes(sample = sample)) +
    geom_ribbon(
        data = band, aes(x = z, ymin = lower, ymax = upper),
        inherit.aes = FALSE, fill = INK, alpha = 0.08
    ) +
    stat_qq_line(color = INK, linewidth = 1.0) +
    stat_qq(color = IMPRINT_PALETTE[1], size = 2.5, alpha = 0.6) +
    labs(
        title = "qq-basic · r · ggplot2 · anyplot.ai",
        subtitle = sprintf("Shaft diameter QC measurements (n = %d) vs. normal distribution", n),
        x = "Theoretical Quantiles",
        y = "Sample Quantiles"
    ) +
    theme_minimal(base_size = 8) +
    theme(
        plot.background = element_rect(fill = PAGE_BG, color = PAGE_BG),
        panel.background = element_rect(fill = PAGE_BG, color = NA),
        panel.grid.major = element_line(color = INK, linewidth = 0.15),
        panel.grid.minor = element_blank(),
        panel.border = element_blank(),
        axis.title = element_text(color = INK, size = 10),
        axis.text = element_text(color = INK_SOFT, size = 8),
        axis.line = element_line(color = INK_SOFT),
        plot.title = element_text(color = INK, size = 12),
        plot.subtitle = element_text(color = INK_SOFT, size = 9)
    )

# --- Save -------------------------------------------------------------------
ggsave(
    filename = sprintf("plot-%s.png", THEME),
    plot = p,
    device = ragg::agg_png,
    width = 8,
    height = 4.5,
    units = "in",
    dpi = 400
)
