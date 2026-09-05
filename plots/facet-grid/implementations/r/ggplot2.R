#' anyplot.ai
#' facet-grid: Faceted Grid Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 86/100 | Created: 2026-09-05

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# Theme tokens — Imprint palette (prompts/default-style-guide.md)
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c(
  "#009E73", "#C475FD", "#4467A3", "#BD8233",
  "#AE3030", "#2ABCCD", "#954477", "#99B314"
)

# Data — greenhouse growth trial: response to light exposure,
# split by plant species (rows) and soil type (columns)
species_levels <- c("Fern", "Basil", "Clover")
soil_levels    <- c("Sandy", "Clay", "Loamy")
intercepts     <- c(Fern = 2.0, Basil = 4.5, Clover = 3.2)
slopes         <- c(Sandy = 0.9, Clay = 1.6, Loamy = 2.3)
n_per_cell     <- 150

combos <- expand.grid(species = species_levels, soil = soil_levels,
                       stringsAsFactors = FALSE)

df <- dplyr::bind_rows(lapply(seq_len(nrow(combos)), function(i) {
  sp <- combos$species[i]
  so <- combos$soil[i]
  light_hours <- runif(n_per_cell, 4, 16)
  growth_cm <- intercepts[[sp]] + slopes[[so]] * light_hours +
    rnorm(n_per_cell, 0, 2.2)
  # Floor at a small positive value — plant growth cannot be ~0 or negative.
  growth_cm <- pmax(growth_cm, 0.3)
  tibble::tibble(species = sp, soil = so,
                 light_hours = light_hours, growth_cm = growth_cm)
}))

df$species <- factor(df$species, levels = species_levels)
df$soil    <- factor(df$soil, levels = soil_levels)

# Callout for the strongest soil/species interaction: highest intercept
# (Basil) crossed with the steepest slope (Loamy) yields the fastest growth.
callout <- tibble::tibble(
  species     = factor("Basil", levels = species_levels),
  soil        = factor("Loamy", levels = soil_levels),
  light_hours = 5.5,
  growth_cm   = 40,
  label       = "Steepest growth\nresponse"
)

# Plot
p <- ggplot(df, aes(x = light_hours, y = growth_cm)) +
  geom_point(color = IMPRINT_PALETTE[1], size = 1.7, alpha = 0.4) +
  geom_smooth(method = "lm", formula = y ~ x, se = FALSE,
              color = INK, linewidth = 0.9) +
  geom_text(data = callout, aes(x = light_hours, y = growth_cm, label = label),
            inherit.aes = FALSE, hjust = 0, lineheight = 0.9, size = 2.6,
            fontface = "italic", color = INK_SOFT) +
  facet_grid(rows = vars(species), cols = vars(soil)) +
  labs(
    x = "Light Exposure (hours/day)",
    y = "Growth (cm)",
    title = "facet-grid · r · ggplot2 · anyplot.ai"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.spacing.x   = unit(1.2, "lines"),
    panel.spacing.y   = unit(0.9, "lines"),
    panel.grid.major  = element_line(color = INK, linewidth = 0.2),
    panel.grid.minor  = element_blank(),
    strip.background  = element_rect(fill = ELEVATED_BG, color = NA),
    strip.text        = element_text(color = IMPRINT_PALETTE[1], size = 9.5,
                                      face = "bold"),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 7.5),
    axis.ticks        = element_blank(),
    plot.title        = element_text(color = INK, size = 13, face = "bold"),
    plot.title.position = "plot"
  )

# Save
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
