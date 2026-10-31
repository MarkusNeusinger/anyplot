### Added

- **The renderer draws plotly and bokeh figures in two steps, not served yet.**
  The render harness forks the plot before it arms anything: the plot runs
  under the plot guard and the exec filter with the Python limits and may write
  only its figure as JSON, and the harness, never armed, then hands the figure
  to the JavaScript row's browser harness, which draws it as data with the
  installed package's own plotly.js or BokehJS in the sandboxed page, with a
  stricter policy that runs no script the figure carries. The figure keeps the
  size its code gave it, and the scale makes the image exactly 3200x1800 or
  2400x2400, so the catalogue's layouts look as published. Failures in either
  step end with the same final error line as a JavaScript render. The renderer
  image now carries plotly and bokeh without their kaleido and Selenium export
  stacks. The agent chat does not offer plotly or bokeh yet.
