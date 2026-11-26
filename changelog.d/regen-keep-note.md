### Added

- **A kept regeneration leaves a note for the pair's next attempt.** When the
  regen gate keeps the live implementation, its record now says why in one
  plain line (`keep_note`): the criteria the attempt scored below its
  re-score with the review's comment on each, what got worse and where, the
  adaptability or chat-readiness refusal, or that nothing visible improved.
  The keep write-back stores the note with the re-score as
  `review.last_kept`, and a write-back without a note removes an older one.
  The pair's next generation reads it in a fenced "Last kept attempt" section
  of its previous review, framed as data from that review and never as a
  change request or a weakness. Only the generator gets it: the reviewer's copy
  never holds it, because it would anchor the blind re-score. The write-back
  check in `impl-merge.yml` compares the stored note with the gate record's,
  and records written before the key existed still pass. Until now a later
  attempt learned only what the live file lacks, never why the last attempt
  failed; the owner chose this note instead of switching on the immediate
  retry, which stays off.
