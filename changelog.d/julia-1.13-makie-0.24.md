### Changed

- **The Julia render stack moves to Julia 1.13 and Makie 0.24.** The
  Manifest pins Makie 0.24.16 and CairoMakie 0.15.16, up from the 0.21.9 that
  the QRCoders dependency had forced in June: every QRCoders release caps
  ImageCore at 0.9, while Makie 0.21.10 and later need ImageCore 0.10.
  QRCoders leaves the environment, so qrcode-basic's Makie implementation
  needs a regeneration, and nyquist-basic, which crashed on 0.21.9, renders
  again. The setup action installs Julia 1.13, and the Makie generator prompt
  switches to `Figure(size = …)` and adds notes on the 0.24 APIs that changed
  (arrows, text alignment, layout gaps, and `heatmap!` on a `PolarAxis`,
  which renders a blank figure).
