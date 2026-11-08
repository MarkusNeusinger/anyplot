### Changed

- **Plot votes count per version of the image.** A 👍/👎 belongs to the image it was cast on: once a plot is
  regenerated (its `updated` changes), only the votes from that moment on count for the current version, and the
  earlier ones stay in the table as votes on an earlier version; nothing is deleted. A visitor who rated the old
  image may rate the new one once: the page keeps its vote per spec, language, library and version, so the old
  thumb no longer stays inked on the new image, and the API's one-vote-per-session guard looks only at the current
  version. A vote stored before this change inks nothing and blocks nothing. One rule in `core/plot_votes.py`
  serves the API, the debug list and the audit skill's selector, which now counts a session once on each side of
  the update. (#12830)
- **`/debug` ranks the plots by their votes.** The "votes per plot" list has one row per implementation with the
  current version's 👍, 👎 and their total, the earlier versions' counts beside them and the newest vote, sorted
  by thumbs down, thumbs up or total from the column headers. It counts one vote per visitor and version and shows
  counts only. `GET /debug/feedback/votes` serves it and replaces `GET /debug/feedback/top`, whose two lists grouped
  the rows of one reaction by page path. (#12830)
