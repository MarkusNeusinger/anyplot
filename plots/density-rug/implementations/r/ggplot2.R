#' anyplot.ai
#' density-rug: Density Plot with Rug Marks
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 95/100 | Created: 2026-05-18

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
# Response times (in milliseconds) from a web application
response_times <- c(
  rnorm(45, mean = 150, sd = 30),
  rnorm(35, mean = 250, sd = 40)
)

df <- data.frame(value = response_times)

# --- Plot -------------------------------------------------------------------
p <- ggplot(df, aes(x = value)) +
  geom_density(
    stat = "density",
    fill = OKABE_ITO[1],
    color = OKABE_ITO[1],
    alpha = 0.35,
    linewidth = 1.4,
    bw = 20
  ) +
  geom_density(
    stat = "density",
    fill = NA,
    color = OKABE_ITO[1],
    alpha = 1,
    linewidth = 2,
    bw = 20,
    key_glyph = "blank"
  ) +
  geom_rug(
    color = OKABE_ITO[1],
    alpha = 0.7,
    linewidth = 0.9,
    length = unit(0.035, "npc")
  ) +
  geom_vline(
    xintercept = 150,
    color = OKABE_ITO[1],
    linewidth = 0.6,
    alpha = 0.5,
    linetype = "dashed"
  ) +
  geom_vline(
    xintercept = 250,
    color = OKABE_ITO[1],
    linewidth = 0.6,
    alpha = 0.5,
    linetype = "dashed"
  ) +
  annotate(
    "text",
    x = 150,
    y = Inf,
    label = "Peak 1",
    vjust = 1.5,
    hjust = 0.5,
    size = 5,
    color = INK,
    family = "sans"
  ) +
  annotate(
    "text",
    x = 250,
    y = Inf,
    label = "Peak 2",
    vjust = 1.5,
    hjust = 0.5,
    size = 5,
    color = INK,
    family = "sans"
  ) +
  labs(
    title = "density-rug · R · ggplot2 · anyplot.ai",
    x = "Response Time (ms)",
    y = "Density"
  ) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.15))) +
  theme_minimal(base_size = 14) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major = element_line(color = INK, linewidth = 0.3),
    panel.grid.minor = element_blank(),
    panel.border     = element_rect(color = INK_SOFT, fill = NA, linewidth = 0.6),
    axis.title       = element_text(color = INK, size = 20),
    axis.text        = element_text(color = INK_SOFT, size = 16),
    plot.title       = element_text(color = INK, size = 24),
    axis.ticks       = element_line(color = INK_SOFT)
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
