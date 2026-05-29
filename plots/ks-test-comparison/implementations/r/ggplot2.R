#' anyplot.ai
#' ks-test-comparison: Kolmogorov-Smirnov Plot for Distribution Comparison
#' Library: ggplot2 | R
#' Quality: pending | Created: 2026-05-29

library(ggplot2)
library(dplyr)
library(scales)
library(ragg)

set.seed(42)

# Theme tokens — Imprint palette
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

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

# Data: credit scoring — Good vs Bad customer score distributions
n_good <- 500
n_bad  <- 500

good_scores <- rnorm(n_good, mean = 680, sd = 60)
bad_scores  <- rnorm(n_bad,  mean = 580, sd = 80)

# Kolmogorov-Smirnov test
ks_result <- ks.test(good_scores, bad_scores)

# Find K-S statistic location — maximum vertical distance between ECDFs
all_x     <- sort(unique(c(good_scores, bad_scores)))
ecdf_good <- ecdf(good_scores)
ecdf_bad  <- ecdf(bad_scores)
good_vals <- ecdf_good(all_x)
bad_vals  <- ecdf_bad(all_x)
diffs     <- abs(good_vals - bad_vals)
max_idx   <- which.max(diffs)
ks_x      <- all_x[max_idx]
ks_y_lo   <- min(good_vals[max_idx], bad_vals[max_idx])
ks_y_hi   <- max(good_vals[max_idx], bad_vals[max_idx])
ks_y_mid  <- (ks_y_lo + ks_y_hi) / 2

# Annotation text
ks_d     <- round(as.numeric(ks_result$statistic), 3)
ks_p_fmt <- formatC(ks_result$p.value, format = "e", digits = 2)
annot    <- paste0("D = ", ks_d, "\np = ", ks_p_fmt)

# Long-format data frame for stat_ecdf
df_scores <- data.frame(
  score = c(good_scores, bad_scores),
  group = factor(
    c(rep("Good Customers", n_good), rep("Bad Customers", n_bad)),
    levels = c("Good Customers", "Bad Customers")
  )
)

# K-S segment data frame
ks_seg <- data.frame(x = ks_x, xend = ks_x, y = ks_y_lo, yend = ks_y_hi)

# Plot
p <- ggplot(df_scores, aes(x = score, color = group, linetype = group)) +
  stat_ecdf(geom = "step", linewidth = 1.2, pad = FALSE) +
  geom_segment(
    data = ks_seg,
    aes(x = x, xend = xend, y = y, yend = yend),
    color       = INK,
    linewidth   = 0.9,
    linetype    = "dotdash",
    inherit.aes = FALSE
  ) +
  annotate(
    "label",
    x             = ks_x + 22,
    y             = ks_y_mid,
    label         = annot,
    color         = INK,
    fill          = ELEVATED_BG,
    size          = 3.0,
    hjust         = 0,
    label.padding = unit(0.4, "lines"),
    label.size    = 0.25,
    label.r       = unit(0.12, "lines")
  ) +
  scale_color_manual(
    name   = NULL,
    values = c("Good Customers" = IMPRINT_PALETTE[1],
               "Bad Customers"  = IMPRINT_PALETTE[2])
  ) +
  scale_linetype_manual(
    name   = NULL,
    values = c("Good Customers" = "solid", "Bad Customers" = "longdash")
  ) +
  scale_y_continuous(
    labels = percent_format(accuracy = 1),
    limits = c(0, 1),
    expand = expansion(mult = c(0.01, 0.03))
  ) +
  scale_x_continuous(expand = expansion(mult = c(0.02, 0.06))) +
  labs(
    title = "ks-test-comparison · r · ggplot2 · anyplot.ai",
    x     = "Credit Score",
    y     = "Cumulative Proportion"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG,     color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG,     color = NA),
    panel.grid.major  = element_line(color = INK_SOFT,   linewidth = 0.2),
    panel.grid.minor  = element_blank(),
    panel.border      = element_blank(),
    axis.title        = element_text(color = INK,        size = 10),
    axis.text         = element_text(color = INK_SOFT,   size = 8),
    axis.line         = element_line(color = INK_SOFT,   linewidth = 0.4),
    plot.title        = element_text(color = INK,        size = 12,
                                     face = "bold",
                                     margin = margin(b = 10)),
    plot.margin       = margin(t = 16, r = 24, b = 12, l = 12),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT,
                                     linewidth = 0.3),
    legend.text       = element_text(color = INK_SOFT,   size = 8),
    legend.title      = element_text(color = INK,        size = 10),
    legend.position   = "bottom",
    legend.key.width  = unit(1.5, "cm")
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
