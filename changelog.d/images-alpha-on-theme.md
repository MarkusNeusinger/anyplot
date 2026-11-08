### Fixed

- **The site's preview images keep a plot's background instead of turning it black.** The smaller PNG and WebP variants dropped the alpha channel, so a render that paints only its panel showed black bars beside the plot; transparent pixels now take the theme's card surface.
