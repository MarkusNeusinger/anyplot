#' anyplot.ai
#' violin-grouped-swarm: Grouped Violin Plot with Swarm Overlay
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 88/100 | Created: 2026-05-18

library(ggplot2)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
OKABE_ITO   <- c("#009E73", "#D55E00", "#0072B2", "#CC79A7",
                 "#E69F00", "#56B4E9", "#F0E442")

# --- Data -------------------------------------------------------------------
# Response times (ms) across task types and expertise levels
set.seed(42)
n_per_group <- 50

df <- data.frame(
  category = character(n_per_group * 6),
  group = character(n_per_group * 6),
  value = numeric(n_per_group * 6),
  stringsAsFactors = FALSE
)

idx <- 1
for (cat in c("Data Entry", "Analysis", "Decision-Making")) {
  for (grp in c("Junior", "Senior")) {
    mean_val <- if (cat == "Data Entry") {
      if (grp == "Junior") 800 else 520
    } else if (cat == "Analysis") {
      if (grp == "Junior") 1500 else 975
    } else {
      if (grp == "Junior") 2200 else 1430
    }

    sd_val <- if (cat == "Data Entry") 200 else if (cat == "Analysis") 300 else 350
    if (grp == "Senior") sd_val <- sd_val * 0.75

    for (i in 1:n_per_group) {
      df$category[idx] <- cat
      df$group[idx] <- grp
      df$value[idx] <- max(100, rnorm(1, mean = mean_val, sd = sd_val))
      idx <- idx + 1
    }
  }
}

# --- Plot -------------------------------------------------------------------
p <- ggplot(df, aes(x = category, y = value, fill = group, color = group)) +
  geom_violin(
    alpha = 0.5,
    linewidth = 0.6,
    position = position_dodge(width = 0.8)
  ) +
  geom_point(
    size = 2.5,
    alpha = 0.6,
    position = position_dodge(width = 0.8),
    shape = 21,
    stroke = 0.5
  ) +
  scale_fill_manual(values = OKABE_ITO[1:2]) +
  scale_color_manual(values = OKABE_ITO[1:2]) +
  labs(
    title = "violin-grouped-swarm · R · ggplot2 · anyplot.ai",
    x = "Task Type",
    y = "Response Time (ms)",
    fill = "Expertise Level",
    color = "Expertise Level"
  ) +
  theme_minimal(base_size = 14) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major = element_line(color = INK, linewidth = 0.3),
    panel.grid.minor = element_blank(),
    axis.title       = element_text(color = INK, size = 20, face = "bold"),
    axis.text        = element_text(color = INK_SOFT, size = 16),
    plot.title       = element_text(color = INK, size = 24, face = "bold"),
    legend.background = element_rect(fill = PAGE_BG, color = NA),
    legend.text      = element_text(color = INK_SOFT, size = 16),
    legend.title     = element_text(color = INK, size = 18, face = "bold"),
    legend.position  = "top",
    panel.border     = element_rect(color = INK_SOFT, fill = NA, linewidth = 0.4)
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 16,
  height   = 9,
  units    = "in",
  dpi      = 300
)
