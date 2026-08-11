#' anyplot.ai
#' bland-altman-basic: Bland-Altman Agreement Plot
#' Library: ggplot2 | R 4.x
#' Quality: pending | Created: 2026-08-11

library(ggplot2)
library(tibble)
library(ragg)
library(scales)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"

IMPRINT_PALETTE <- c(
  "#009E73", "#C475FD", "#4467A3", "#BD8233",
  "#AE3030", "#2ABCCD", "#954477", "#99B314"
)

# --- Data ---------------------------------------------------------------
# Systolic blood pressure (mmHg) from two sphygmomanometers on 90 subjects
n <- 90
true_sbp <- rnorm(n, mean = 128, sd = 15)
device_a <- true_sbp + rnorm(n, mean = 0, sd = 4)
device_b <- true_sbp + rnorm(n, mean = 2.5, sd = 5)

avg_sbp <- (device_a + device_b) / 2
diff_sbp <- device_a - device_b

bias <- mean(diff_sbp)
sd_diff <- sd(diff_sbp)
loa_upper <- bias + 1.96 * sd_diff
loa_lower <- bias - 1.96 * sd_diff

df <- tibble(avg_sbp = avg_sbp, diff_sbp = diff_sbp)

annotation_x <- max(avg_sbp) - 0.02 * diff(range(avg_sbp))

# --- Plot -----------------------------------------------------------------
p <- ggplot(df, aes(x = avg_sbp, y = diff_sbp)) +
  geom_hline(yintercept = 0, color = INK_MUTED, linewidth = 0.4, linetype = "solid") +
  geom_hline(yintercept = bias, color = IMPRINT_PALETTE[3], linewidth = 1.1) +
  geom_hline(yintercept = loa_upper, color = IMPRINT_PALETTE[5], linewidth = 0.9, linetype = "dashed") +
  geom_hline(yintercept = loa_lower, color = IMPRINT_PALETTE[5], linewidth = 0.9, linetype = "dashed") +
  geom_point(color = IMPRINT_PALETTE[1], size = 2.5, alpha = 0.6) +
  annotate(
    "text", x = annotation_x, y = bias, hjust = 1, vjust = -0.6,
    label = sprintf("Bias = %.1f mmHg", bias),
    size = 3.4, color = IMPRINT_PALETTE[3]
  ) +
  annotate(
    "text", x = annotation_x, y = loa_upper, hjust = 1, vjust = -0.6,
    label = sprintf("+1.96 SD = %.1f", loa_upper),
    size = 3.4, color = IMPRINT_PALETTE[5]
  ) +
  annotate(
    "text", x = annotation_x, y = loa_lower, hjust = 1, vjust = 1.4,
    label = sprintf("-1.96 SD = %.1f", loa_lower),
    size = 3.4, color = IMPRINT_PALETTE[5]
  ) +
  labs(
    title = "bland-altman-basic · r · ggplot2 · anyplot.ai",
    x = "Mean of Device A and Device B (mmHg)",
    y = "Difference: Device A − Device B (mmHg)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = alpha(INK, 0.15), linewidth = 0.4),
    panel.grid.minor  = element_blank(),
    axis.line         = element_line(color = INK_SOFT, linewidth = 0.4),
    axis.ticks        = element_blank(),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    plot.title        = element_text(color = INK, size = 12, face = "bold"),
    plot.margin       = margin(t = 14, r = 24, b = 10, l = 10)
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
