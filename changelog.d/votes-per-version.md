### Changed

- **Plot votes count per version of the image.** A 👍/👎 belongs to the image it was cast on: once a plot is
  regenerated (its `updated` changes), only the votes from that moment on count for the current version, and the
  earlier ones stay in the table as votes on an earlier version; nothing is deleted. A visitor who rated the old
  image may rate the new one once: the page keeps its vote per spec, language, library and version, so the old
  thumb no longer stays inked on the new image, and the API's one-vote-per-session guard looks only at the current
  version. A vote stored before this change inks nothing and blocks nothing. `/debug`'s top pages show the current
  version's count, with the earlier rows as "+n earlier". One rule in `core/plot_votes.py` serves the API, the
  debug lists and the audit skill's selector, which now counts a session once on each side of the update.
