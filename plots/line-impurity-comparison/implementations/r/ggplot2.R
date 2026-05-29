#' anyplot.ai
#' line-impurity-comparison: Gini Impurity vs Entropy Comparison
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 86/100 | Created: 2026-05-29

library(ggplot2)
library(dplyr)
library(scales)
library(ragg)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Imprint palette — Gini gets brand green (pos 1), Entropy gets lavender (pos 2)
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

# Data: probability range [0, 1] with 100 points
p_vals <- seq(0, 1, length.out = 100)

gini_vals <- 2 * p_vals * (1 - p_vals)

# Entropy: 0 at boundaries by convention (lim p->0 p*log2(p) = 0)
entropy_vals <- ifelse(
  p_vals == 0 | p_vals == 1,
  0,
  -p_vals * log2(p_vals) - (1 - p_vals) * log2(1 - p_vals)
)

gini_label    <- "Gini: 2p(1-p)"
entropy_label <- "Entropy: -p log2(p) - (1-p) log2(1-p)"

df <- data.frame(
  p        = rep(p_vals, 2),
  impurity = c(gini_vals, entropy_vals),
  metric   = factor(
    rep(c(gini_label, entropy_label), each = 100),
    levels = c(gini_label, entropy_label)
  )
)

# Plot
plot_title <- "line-impurity-comparison · r · ggplot2 · anyplot.ai"

p_plot <- ggplot(df, aes(x = p, y = impurity, color = metric, linetype = metric)) +
  geom_area(aes(fill = metric), alpha = 0.08, position = "identity") +
  geom_line(linewidth = 1.2) +
  geom_vline(
    xintercept = 0.5,
    color      = INK_SOFT,
    linewidth  = 0.4,
    linetype   = "dotted"
  ) +
  annotate(
    "text",
    x      = 0.53,
    y      = 0.88,
    label  = "p = 0.5 (max impurity)",
    color  = INK_SOFT,
    size   = 3,
    hjust  = 0
  ) +
  scale_color_manual(
    name   = "Splitting Criterion",
    values = c(
      "Gini: 2p(1-p)"                                    = IMPRINT_PALETTE[1],
      "Entropy: -p log2(p) - (1-p) log2(1-p)"            = IMPRINT_PALETTE[2]
    )
  ) +
  scale_fill_manual(
    values = c(
      "Gini: 2p(1-p)"                                    = IMPRINT_PALETTE[1],
      "Entropy: -p log2(p) - (1-p) log2(1-p)"            = IMPRINT_PALETTE[2]
    ),
    guide  = "none"
  ) +
  scale_linetype_manual(
    name   = "Splitting Criterion",
    values = c(
      "Gini: 2p(1-p)"                                    = "solid",
      "Entropy: -p log2(p) - (1-p) log2(1-p)"            = "dashed"
    )
  ) +
  scale_x_continuous(
    breaks = seq(0, 1, 0.25),
    labels = c("0", "0.25", "0.5", "0.75", "1")
  ) +
  scale_y_continuous(
    breaks = seq(0, 1, 0.25),
    limits = c(0, 1.08)
  ) +
  labs(
    title = plot_title,
    x     = "Probability p",
    y     = "Impurity (normalized to [0, 1])"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(
      color     = adjustcolor(INK_SOFT, alpha.f = 0.25),
      linewidth = 0.3
    ),
    panel.grid.minor  = element_blank(),
    axis.line         = element_line(color = INK_SOFT, linewidth = 0.4),
    axis.title        = element_text(color = INK,      size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    plot.title        = element_text(color = INK,      size = 12, hjust = 0),
    legend.background = element_rect(
      fill      = ELEVATED_BG,
      color     = adjustcolor(INK_SOFT, alpha.f = 0.4),
      linewidth = 0.3
    ),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK,      size = 10),
    legend.position   = "bottom",
    legend.key        = element_rect(fill = PAGE_BG, color = NA),
    plot.margin       = unit(c(0.5, 0.5, 0.3, 0.5), "cm")
  )

# Save
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p_plot,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
