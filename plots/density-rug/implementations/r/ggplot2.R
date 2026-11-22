#' anyplot.ai
#' density-rug: Density Plot with Rug Marks
#' Library: ggplot2 4.0.3 | R 4.6.1
#' Quality: 78/100 | Updated: 2026-11-22

library(ggplot2)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT     <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                 "#AE3030", "#2ABCCD", "#954477", "#99B314")

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
    fill = IMPRINT[1],
    color = IMPRINT[1],
    alpha = 0.35,
    linewidth = 0.8,
    bw = 20
  ) +
  geom_density(
    stat = "density",
    fill = NA,
    color = IMPRINT[1],
    alpha = 1,
    linewidth = 1.1,
    bw = 20,
    key_glyph = "blank"
  ) +
  geom_rug(
    color = IMPRINT[1],
    alpha = 0.7,
    linewidth = 0.5,
    length = unit(0.035, "npc")
  ) +
  geom_vline(
    xintercept = 150,
    color = IMPRINT[1],
    linewidth = 0.4,
    alpha = 0.5,
    linetype = "dashed"
  ) +
  geom_vline(
    xintercept = 250,
    color = IMPRINT[1],
    linewidth = 0.4,
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
    size = 3.2,
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
    size = 3.2,
    color = INK,
    family = "sans"
  ) +
  labs(
    title = "density-rug · r · ggplot2 · anyplot.ai",
    x = "Response Time (ms)",
    y = "Density"
  ) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.15))) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major = element_line(color = INK, linewidth = 0.2),
    panel.grid.minor = element_blank(),
    panel.border     = element_rect(color = INK_SOFT, fill = NA, linewidth = 0.4),
    axis.title       = element_text(color = INK, size = 10),
    axis.text        = element_text(color = INK_SOFT, size = 8),
    plot.title       = element_text(color = INK, size = 12),
    axis.ticks       = element_line(color = INK_SOFT)
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
