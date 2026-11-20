### Added

- **The data card names every plot axis a chat turn reassigned.** In the chat
  of "Use with my data", a turn that changes the table can also put other
  columns on the plot's axes, and the page used to take the new bindings
  silently. Such a turn's change lines now end with one line per axis in the
  server's own words, such as `x takes the new column 'Day no' instead of
  'Air temp'`, `y lost its column 'Rel humidity' and holds none now`, or
  `y takes 'Rel humidity'` for an empty axis the turn filled. A turn that only
  re-binds, a turn whose formula or code replaced the table, the server's own
  conversions of a paste and a renamed column get no line, and nothing is
  blocked. The assistant never reads these lines. The usage telemetry counts
  the marks by their closed codes, never by a role or a column. (#13229)
