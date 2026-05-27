#' anyplot.ai
#' violin-swarm: Violin Plot with Overlaid Swarm Points
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 88/100 | Created: 2026-05-18

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT   <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                 "#AE3030", "#2ABCCD", "#954477")

# --- Data -------------------------------------------------------------------
df <- tibble::tibble(
  condition = rep(c("Control", "Treatment A", "Treatment B", "Treatment C"),
                  each = 60),
  reaction_time = c(
    rnorm(60, mean = 350, sd = 50),
    rnorm(60, mean = 320, sd = 45),
    rnorm(60, mean = 300, sd = 55),
    rnorm(60, mean = 310, sd = 48)
  )
)

# --- Plot -------------------------------------------------------------------
p <- ggplot(df, aes(x = condition, y = reaction_time)) +
  geom_violin(
    fill = IMPRINT[1],
    alpha = 0.4,
    color = INK_SOFT,
    linewidth = 0.8
  ) +
  geom_jitter(
    color = IMPRINT[1],
    size = 2.5,
    alpha = 0.7,
    width = 0.2,
    height = 0
  ) +
  labs(
    title = "violin-swarm · R · ggplot2 · anyplot.ai",
    x = "Experimental Condition",
    y = "Reaction Time (ms)"
  ) +
  theme_minimal(base_size = 14) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x = element_blank(),
    panel.grid.major.y = element_line(color = INK, linewidth = 0.3),
    panel.grid.minor = element_blank(),
    axis.title       = element_text(color = INK, size = 20),
    axis.text        = element_text(color = INK_SOFT, size = 16),
    plot.title       = element_text(color = INK, size = 24)
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
