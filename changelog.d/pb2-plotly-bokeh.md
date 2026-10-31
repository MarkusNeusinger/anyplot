### Added

- **plotly and bokeh in "Use with my data", for the admin's live tests.** The
  Python runtime serves both through the renderer's two-step figure mode: the
  plot writes its figure as JSON under the plot guard, and the JavaScript
  harness draws it in Chromium at the catalogue's canvas. The admin deploy names
  them, so all 15 catalogue libraries are served, and each one's 80 % eval
  matrix gates the public release. Across the catalogue 273 of 325 plotly and
  254 of 325 bokeh files are eligible; in the renderer image 254 of the 273 and
  247 of the 254 render on target in both themes as they stand, the rest only
  because their code divides by the length of the emptied catalogue title.
- **The validator rules for plotly and bokeh.** Both refuse private names, a
  string where the library expects a URL whatever its scheme, and every model
  that loads from the network or a file: plotly's geo and map traces and its
  `plotly_relayout` family, bokeh's JavaScript, markup and tile models and its
  import by name. bokeh's tooltip templates pass as the catalogue writes them,
  text tags with a quoted `style` or `class`, never `{safe}`, because BokehJS
  parses a template and each tooltip value as HTML.
- **The figure save and the exported code.** The normaliser turns the
  catalogue's save block into one protected statement that writes the figure as
  JSON (plotly's size moved into the figure; bokeh's Selenium screenshot block
  removed). The downloaded `plot.py` swaps it back for the library's normal
  save, so it runs unchanged on the user's machine with `data.csv`: plotly's
  `write_image` and `write_html`, bokeh's `export_png`, `output_file` and
  `save`. This is the one place where the export is not the run form byte for
  byte (owner decision).
- **plotly and bokeh adapter sections.** Measured in the renderer image: the
  protected save, the theme tokens on the figure, timestamps converted to UTC
  (plotly draws an offset timestamp's clock time as given), plotly's
  `separators` for the plot language's decimal and thousands marks, bokeh's
  ticks on fixed values with labels written in Python (BokehJS writes English
  marks whatever its `language`), `render_mode="svg"` and no WebGL. An image
  test renders each idiom from a table with missing cells in both themes.
- **plotly and bokeh eval fixtures.** The ten matrix specs for each (120 cases,
  900 generated in all) and the smoke cases `scatter-basic-plotly-renamed` and
  `scatter-basic-bokeh-renamed`; all twenty files are eligible.
- **A plotly figure render gates the renderer's deploy.** The candidate smoke
  renders a plotly figure with an axis range through both steps of the figure
  mode under gVisor and refuses the promotion when it fails twice.

### Changed

- **The scope judge's example of another library is Excel.** "Gibt es das
  auch in Plotly?" stood for a library the assistant does not adapt; plotly is
  served now, and so is every catalogue library.
- **Every profile's URL rule refuses a protocol-relative URL.** The Python, R
  and Julia validators refuse `//host/...`, `ws://`, `wss://`, `blob:` and
  `javascript:` in a string, as the JavaScript one has since JS-3; no catalogue
  file of a served library changes its outcome.

### Fixed

- **A plotly 3D plot no longer passes as a blank render.** The renderer's
  headless browser draws a 3D scene as nothing but its colour bar, without
  plotly's WebGL notice, and the host gates passed it. A figure with a WebGL
  trace now fails as `draw NoWebGL` before it is drawn, and the readiness scan
  blocks such catalogue files (15 plotly files) until the renderer draws WebGL.
