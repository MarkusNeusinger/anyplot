### Added

- **👍 / 👎 directly on the plot.** A spec detail view now carries a thumbs-up
  button top-left and a thumbs-down button bottom-left over the image — both
  on the static preview and the interactive surface — so rating an
  implementation is one tap instead of a trip through the floating feedback
  menu. The tap inks the thumb, flashes `>>> .liked` / `>>> .disliked` in the
  centre like `.copied` does, and posts a reaction-only entry to `/feedback`
  with `library_id` and `language` (a new Alembic revision adds both columns
  and a `(spec_id, library_id)` index), so votes can be counted per image later
  via `FeedbackRepository.reaction_counts` — nothing is displayed yet. One vote
  per image per session: the choice is remembered in localStorage and the other
  thumb fades out, and the server drops a repeat vote from the same session for
  the same implementation silently, so nobody can flip up and down at will.
  Supersedes the stale PR #8126, which placed both thumbs top-left.

### Changed

- **Reaction-only feedback has its own rate limit.** Free-text entries stay at
  5 per minute per IP, now counted over message-bearing rows only; a 👍/👎 tap
  is capped at 30 per minute, so flipping through the library carousel and
  rating several plots no longer trips the free-text limit or blocks a message
  written right after.

### Removed

- **The `.report()` flag over the plot.** Reporting stays on the spec hub page
  (`report issue ↗`) and via the GitHub issue template; the in-plot flag was
  the least-used overlay action and its corner now belongs to the vote.
