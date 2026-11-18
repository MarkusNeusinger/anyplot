# Decision log

One small file for each decision the owner took that shaped the product, the pipeline or a public
text. The code of this repository is written by AI agents; what the owner contributes is the
direction, the standards, the push-back and the acceptance, and none of that shows in a diff. This
folder is where it shows.

## Find a decision

List the folder, or search it:

```bash
ls docs/decisions/
grep -ril "retention" docs/decisions/
```

File names start with the date, so the listing is in order of date; decisions of the same day stand
in no particular order.

## Add a decision

One question decides: would someone who asks how this project was shaped look for this decision?
If yes, it gets a file.

The kind of thing does not decide it. These are decisions of that sort, small as they look: how
many pastes a visitor may send in a day, that the chat's replies are short, that a plot's texts
stay English until the visitor picks another language. These are not: the fix of one sentence, a
pick between two near-equal variants, a value tuned inside a range that was already agreed, and
anything that only follows from a decision already in the log. Fold such things into the entry
they belong to.

The log is the pool, not the showcase. The README and the about page pick their highlights from
it, so an entry need not be a highlight; it only must not be noise.

1. Name the file `YYYY-MM-DD-<short-slug>.md`, with the date of the decision.
2. Write it in this form:

   ```markdown
   # The decision as one short sentence

   - Date: 2026-11-18
   - Proposed: what was on the table, built or suggested.
   - Decided: what the owner decided, and why.
   - Where: #12345
   ```

3. Add it in the pull request that carries the decision out, and name that pull request under
   "Where". A decision that changes nothing else still arrives through a pull request, and "Where"
   names that one. For a decision that a document of this repository already records, "Where" may
   name the file instead, in backticks: `docs/concepts/agent-network.md`.

The form is fixed and "Where" is the source, because an entry without one is a story nobody can
check. `tests/unit/test_decision_log.py` fails for a file whose name has no date, that lacks one of
the four lines or has them twice or out of order, whose date differs from its name, or whose
"Where" names neither a pull request nor an existing file of this repository.

Keep to what happened. "Decided" gives the owner's reason when he gave one, and says so when the
reason is the agent's reading. The rules for public text apply: no private detail, nothing a visitor
wrote, and a security finding only at the level of its class.

One file per decision, and never a shared list: pull requests that are open at the same time then
never edit the same lines.
