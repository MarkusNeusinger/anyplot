### Changed

- **The agent chat answers short and asks only when it matters.** The root's new "Replies" rules lead with the
  result in two or three sentences, keep every notice the data rules require (the loader's "reads", "keeps time"
  and "converts" lines, data changes with their counts, `requested_not_found`, refusals and limits), ask a
  question only when the turn cannot go on without it or the answer changes the data or the plot materially, close
  with no offer, and act on the user's answer in the same turn: "the scores are out of 100" now sets the axis to 0
  to 100. On seven chat scenarios from the user test of 2026-11-01, questions per reply fell from 0.75 to 0 and the
  words per reply from 58.7 to 50.4 on average (plot replies from 50 to 37). The version's "what changed" notes are
  written in the plot language and in plain words, without the code's own names such as `load_user_data()`.
  (#12506)

### Added

- **The prep eval measures the root's replies.** Every reply's words, questions and closing question are counted;
  a closing question the turn was not blocked for, or a reply over 100 words, is a reply miss, gated at 10 %
  (`--max-reply-misses`). A case can send the page's summary action, and four step-1 summary cases join the set.
  (#12506)
