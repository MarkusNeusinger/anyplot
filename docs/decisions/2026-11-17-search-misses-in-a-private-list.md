# Searches without a hit go to a private list, not to the public dashboard

- Date: 2026-11-17
- Proposed: the gallery sent the text of a search to Plausible, whose dashboard is public. Taking
  the text out of the events would have left only a count.
- Decided: build the list of the project's own, in its database, read only by the owner. His reason:
  without the texts, a gap such as a missing synonym would no longer be seen.
- Where: #13181
