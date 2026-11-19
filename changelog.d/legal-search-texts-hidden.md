### Changed

- **The privacy page says the old search texts are stored, not shown.** The
  gallery's search texts sent to Plausible up to and including November 2026
  are hidden from the public dashboard now that the property `query` is no
  longer an allowed property; Plausible still stores them, so the analytics
  row on `/legal` and its crawler copy say "still stored by Plausible, no
  longer shown" instead of "still show there". (#13203)
