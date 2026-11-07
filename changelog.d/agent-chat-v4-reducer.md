### Changed

- **The agent chat's session keeps an item per data version, per switch and
  per turn outcome, with nothing on the page changed yet.** Every data version
  gets an item with a snapshot of what it held (rows, columns, preview,
  profile, file, sheet, change lines), numbered per session as `data v3`,
  since the server's version starts over with every paste. A version a turn
  made leaves a stub where the card stood and moves the card, under its id, to
  the thread's end; a version from the card's own controls (`.undo()`,
  `.to_long()`, the pickers) puts the stub above the card, which stays in
  place, unless a plot stands below the card, in which case the card moves
  below it too. A library switch adds an item with the decisions it carries,
  and a typed turn carries what it changed (data, plot, switch, language,
  memory, or nothing, which marks a question), read from the stream until the
  server names it. `threadModel.ts` reads chapters, folds and counts from the
  items for the chapter lines to come, and the thread still renders one card
  per paste: a long session replayed through both reducers renders byte for
  byte as before. (#12598)
