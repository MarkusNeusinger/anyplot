### Added

- **Data from your own code in "Use with my data".** You can paste or type code that
  generates your data (Python, JavaScript, R, or a formula from a textbook). The
  assistant translates it into Python, and its new `run_data_code` tool runs it in the
  renderer's sandbox through a new `POST /run-data` route. The resulting table becomes a
  new data version that you confirm, and the data panel shows the Python that ran under
  `# code that made this data`. The validator's new DATA profile (which also counts text
  values and repeated lists as written-out rows), an audit hook in the harness (no file
  access, new imports, frames, native code, processes, or sockets), per-user and per-minute
  limits, and the dataset judge on the computed table keep the sandbox to the plot's
  data. The tool never passes the snippet's own output back to the model. A request in
  words that needs a computation (the Lorenz attractor, a random walk) goes this way too;
  a closed formula stays on `generate_data`. (#12172)
- **`422 code` for code pasted into the data field.** A classifier now runs before any
  parser or the transcriber reads a paste. It catches code such as
  `np.linspace(0, 10, 100)`, which used to parse as a one-row table, and the page offers
  to send it to the chat instead. (#12172)

### Changed

- **The scope judge treats data-generating code as in scope.** A snippet or formula
  whose job is to generate the plot's data is now in scope in any language. Code with
  another purpose is out of scope, and code that touches files, the network, or the
  system is an attack. Scope case `off-053`, a sine wave for homework, is now in scope.
  (#12172)
