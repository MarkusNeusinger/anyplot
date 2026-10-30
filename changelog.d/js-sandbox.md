### Added

- **A sandbox mode for the JavaScript render harness, not served yet.**
  `automation/js-render/render.mjs` gains switches that only the renderer's
  JavaScript row sets, so the catalogue pipeline renders exactly as before:
  `ANYPLOT_SANDBOX=1` aborts every request of the page, closes every WebSocket,
  blocks popups and WebRTC, adds a content security policy, renders in UTC and
  caps the page's memory; MUI X imports are closed to the image's allowlist, so
  a snippet can no longer bundle a file of the image; the console keeps the first
  five errors; and a failure ends stderr with one line naming the error's kind,
  class and line in the snippet. `ANYPLOT_NO_HTML=1` skips the interactive page,
  and `ANYPLOT_DATA_JSON` injects the table as `window.ANYPLOT_DATA`, typed by the
  service from the canonical CSV (`agents/anyplot/data/typed_json.py`) and carried
  by a new optional `data_json` field of the render request. Every catalogue
  JavaScript file that rendered before renders the same way in sandbox mode. The
  agent chat does not offer JavaScript yet. (#12466)
