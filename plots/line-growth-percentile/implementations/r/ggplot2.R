#' anyplot.ai
#' line-growth-percentile: Pediatric Growth Chart with Percentile Curves
#' Library: ggplot2 | R 4.4
#' Quality: pending | Created: 2026-06-20

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"
# Approximate 15%-opacity INK blended onto PAGE_BG (ggplot2 lacks alpha on grid lines)
GRID        <- if (THEME == "light") "#D8D6D0" else "#3A3936"

# Imprint palette
IMPRINT_PALETTE <- c(
  "#009E73",  # 1 — brand green (first categorical series)
  "#C475FD",  # 2 — lavender
  "#4467A3",  # 3 — blue
  "#BD8233",  # 4 — ochre
  "#AE3030",  # 5 — matte red
  "#2ABCCD",  # 6 — cyan
  "#954477",  # 7 — rose
  "#99B314"   # 8 — lime
)
BRAND <- IMPRINT_PALETTE[1]  # #009E73 — patient data (contrasting color)
ROSE  <- IMPRINT_PALETTE[7]  # #954477 — girls' reference percentile bands

# Reference data: WHO weight-for-age for girls, 0–60 months (synthetic)
age_months <- 0:60

# Smooth parametric model approximating WHO LMS growth curves (girls)
p50_fn <- function(t) 3.3 + 2.0 * sqrt(t) - 0.016 * t
sd_fn  <- function(t) 0.45 + 0.12 * sqrt(t)

ref_df <- data.frame(
  age = age_months,
  P3  = p50_fn(age_months) - 1.880 * sd_fn(age_months),
  P10 = p50_fn(age_months) - 1.280 * sd_fn(age_months),
  P25 = p50_fn(age_months) - 0.675 * sd_fn(age_months),
  P50 = p50_fn(age_months),
  P75 = p50_fn(age_months) + 0.675 * sd_fn(age_months),
  P90 = p50_fn(age_months) + 1.280 * sd_fn(age_months),
  P97 = p50_fn(age_months) + 1.880 * sd_fn(age_months)
)

# Individual patient: girl tracking near the 30th percentile
patient_ages  <- c(0, 2, 4, 6, 9, 12, 15, 18, 24, 30, 36, 42, 48, 54, 60)
base_weight   <- p50_fn(patient_ages) - 0.45 * sd_fn(patient_ages)
patient_df    <- data.frame(
  age    = patient_ages,
  weight = base_weight + rnorm(length(patient_ages), 0, 0.10)
)

# Right-margin percentile labels at age = 60 (last row of ref_df)
n_last   <- nrow(ref_df)
label_df <- data.frame(
  x     = 61.5,
  y     = c(ref_df$P3[n_last], ref_df$P10[n_last], ref_df$P25[n_last],
            ref_df$P50[n_last], ref_df$P75[n_last], ref_df$P90[n_last],
            ref_df$P97[n_last]),
  label = c("P3", "P10", "P25", "P50", "P75", "P90", "P97")
)

# Title (49 chars < 67 baseline → default font size is fine)
plot_title <- "line-growth-percentile · r · ggplot2 · anyplot.ai"

# Plot
p <- ggplot(ref_df, aes(x = age)) +
  # Percentile bands: graduated intensity (darker at extremes, lighter near median)
  geom_ribbon(aes(ymin = P3,  ymax = P10), fill = ROSE, alpha = 0.45) +
  geom_ribbon(aes(ymin = P90, ymax = P97), fill = ROSE, alpha = 0.45) +
  geom_ribbon(aes(ymin = P10, ymax = P25), fill = ROSE, alpha = 0.28) +
  geom_ribbon(aes(ymin = P75, ymax = P90), fill = ROSE, alpha = 0.28) +
  geom_ribbon(aes(ymin = P25, ymax = P75), fill = ROSE, alpha = 0.12) +
  # Percentile boundary lines (subtle)
  geom_line(aes(y = P3),  color = ROSE, linewidth = 0.4, alpha = 0.6) +
  geom_line(aes(y = P10), color = ROSE, linewidth = 0.4, alpha = 0.6) +
  geom_line(aes(y = P25), color = ROSE, linewidth = 0.4, alpha = 0.6) +
  geom_line(aes(y = P75), color = ROSE, linewidth = 0.4, alpha = 0.6) +
  geom_line(aes(y = P90), color = ROSE, linewidth = 0.4, alpha = 0.6) +
  geom_line(aes(y = P97), color = ROSE, linewidth = 0.4, alpha = 0.6) +
  # Emphasized median (P50) line
  geom_line(aes(y = P50), color = ROSE, linewidth = 1.4) +
  # Individual patient data (brand green — contrasting with rose reference)
  geom_line(
    data      = patient_df,
    aes(x = age, y = weight),
    color     = BRAND,
    linewidth = 1.2
  ) +
  geom_point(
    data  = patient_df,
    aes(x = age, y = weight),
    color = BRAND,
    size  = 2.5,
    shape = 16
  ) +
  # Percentile labels in right margin (clip = "off" allows drawing past panel edge)
  geom_text(
    data      = label_df,
    aes(x = x, y = y, label = label),
    color     = INK_MUTED,
    size      = 2.8,
    hjust     = 0,
    fontface  = "plain"
  ) +
  # Axis scales
  scale_x_continuous(
    breaks = seq(0, 60, by = 12),
    labels = c("Birth", paste0(1:5, " yr"))
  ) +
  scale_y_continuous(
    breaks       = seq(0, 30, by = 5),
    minor_breaks = seq(0, 30, by = 1),
    expand       = expansion(mult = c(0.02, 0.05))
  ) +
  labs(
    title = plot_title,
    x     = "Age",
    y     = "Weight (kg)"
  ) +
  # clip = "off" lets right-margin labels render past the panel boundary
  coord_cartesian(clip = "off") +
  theme_minimal(base_size = 8) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major = element_line(color = GRID, linewidth = 0.3),
    panel.grid.minor = element_line(color = GRID, linewidth = 0.15),
    panel.border     = element_rect(color = INK_SOFT, fill = NA, linewidth = 0.4),
    axis.line        = element_blank(),
    axis.title       = element_text(color = INK,      size = 10),
    axis.text        = element_text(color = INK_SOFT, size = 8),
    plot.title       = element_text(color = INK,      size = 12, face = "bold"),
    plot.margin      = margin(t = 10, r = 55, b = 10, l = 10, unit = "pt"),
    legend.position  = "none"
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
