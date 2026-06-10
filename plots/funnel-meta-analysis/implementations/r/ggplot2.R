#' anyplot.ai
#' funnel-meta-analysis: Meta-Analysis Funnel Plot for Publication Bias
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 86/100 | Created: 2026-06-10

library(ggplot2)
library(ragg)

set.seed(42)

# --- Theme tokens ---
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"

# Imprint palette — first categorical series always #009E73
IMPRINT_PALETTE <- c(
  "#009E73",  # 1 — brand green
  "#C475FD",  # 2 — lavender
  "#4467A3",  # 3 — blue
  "#BD8233",  # 4 — ochre
  "#AE3030",  # 5 — matte red
  "#2ABCCD",  # 6 — cyan
  "#954477",  # 7 — rose
  "#99B314"   # 8 — lime
)

# --- Data: 20 RCTs on antihypertensive treatment vs. placebo ---------------
n_studies  <- 20
pooled_lor <- 0.45  # pooled log odds ratio (treatment reduces cardiovascular risk)

se_values <- c(
  0.08, 0.10, 0.12, 0.14, 0.17, 0.19, 0.21, 0.24, 0.27, 0.30,
  0.33, 0.36, 0.39, 0.42, 0.45, 0.48, 0.52, 0.55, 0.59, 0.63
)

# Slight funnel asymmetry: small studies tend toward larger effect (publication bias)
bias    <- 0.22 * se_values
log_ors <- pooled_lor + bias + rnorm(n_studies, mean = 0, sd = se_values * 0.75)

studies <- data.frame(
  log_or    = log_ors,
  std_error = se_values,
  stringsAsFactors = FALSE
)

# Pseudo 95% CI funnel boundaries (pooled_lor ± 1.96 * SE)
max_se  <- max(se_values) * 1.08
se_seq  <- seq(0, max_se, length.out = 300)

funnel_lines <- data.frame(
  se   = rep(se_seq, 2),
  x    = c(pooled_lor - 1.96 * se_seq, pooled_lor + 1.96 * se_seq),
  side = rep(c("lower", "upper"), each = length(se_seq))
)

# Closed polygon for shaded funnel region
funnel_poly <- data.frame(
  x  = c(pooled_lor - 1.96 * se_seq, rev(pooled_lor + 1.96 * se_seq)),
  se = c(se_seq, rev(se_seq))
)

# --- Plot ---
title_str  <- "funnel-meta-analysis · r · ggplot2 · anyplot.ai"
title_size <- round(12 * min(1.0, 67 / nchar(title_str)))

p <- ggplot() +
  # Shaded funnel region
  geom_polygon(
    data  = funnel_poly,
    aes(x = x, y = se),
    fill  = IMPRINT_PALETTE[3],
    alpha = 0.09,
    color = NA
  ) +
  # Funnel boundary lines (pseudo 95% CI)
  geom_line(
    data      = funnel_lines,
    aes(x = x, y = se, group = side),
    color     = IMPRINT_PALETTE[3],
    linewidth = 0.7,
    linetype  = "dashed"
  ) +
  # Null effect reference line (log OR = 0)
  geom_vline(
    xintercept = 0,
    color      = INK_MUTED,
    linewidth  = 0.5,
    linetype   = "dotted"
  ) +
  # Pooled effect line
  geom_vline(
    xintercept = pooled_lor,
    color      = INK,
    linewidth  = 0.8
  ) +
  # Study points (filled circles, edge matches page background for definition)
  geom_point(
    data   = studies,
    aes(x = log_or, y = std_error),
    fill   = IMPRINT_PALETTE[1],
    color  = PAGE_BG,
    shape  = 21,
    size   = 3.5,
    stroke = 0.7,
    alpha  = 0.9
  ) +
  # Invert y-axis: SE = 0 (most precise) at top, largest SE at bottom
  scale_y_reverse(
    expand = expansion(mult = c(0.02, 0.08))
  ) +
  labs(
    x        = "Log Odds Ratio",
    y        = "Standard Error",
    title    = title_str,
    subtitle = "Publication bias assessment — 20 RCTs on antihypertensive treatment vs. placebo",
    caption  = sprintf(
      "n = %d studies  ·  pooled log OR = %.2f  ·  dashed funnel = pseudo 95%% CI",
      n_studies, pooled_lor
    )
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major = element_line(color = INK_MUTED, linewidth = 0.25),
    panel.grid.minor = element_blank(),
    panel.border     = element_blank(),
    axis.title       = element_text(color = INK, size = 10),
    axis.text        = element_text(color = INK_SOFT, size = 8),
    axis.line        = element_line(color = INK_SOFT, linewidth = 0.5),
    plot.title       = element_text(color = INK, size = title_size, face = "bold"),
    plot.subtitle    = element_text(color = INK_SOFT, size = 9),
    plot.caption     = element_text(color = INK_MUTED, size = 7, hjust = 1),
    plot.margin      = margin(t = 16, r = 20, b = 12, l = 14, unit = "pt")
  )

# --- Save ---
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
