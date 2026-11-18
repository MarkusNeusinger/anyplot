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

Add a file when the owner rejects a proposal, redirects it, or picks between options in a way that
changes what gets built or what the site says. Routine choices that a reviewer would not ask about
don't need one.

1. Name the file `YYYY-MM-DD-<short-slug>.md`, with the date of the decision.
2. Write it in this form:

   ```markdown
   # The decision as one short sentence

   - Date: 2026-11-18
   - Proposed: what was on the table, built or suggested.
   - Decided: what the owner decided, and why.
   - Where: #12345
   ```

3. Add it in the pull request that carries the decision out, so "Where" can name that pull request.
   A decision that leads to no change gets a file in the next pull request that touches the topic,
   and "Where" names the place the question came up.

Keep to what happened. "Decided" gives the owner's reason when he gave one, and says so when the
reason is the agent's reading. The rules for public text apply: no private detail, nothing a visitor
wrote, and a security finding only at the level of its class.

One file per decision, and never a shared list: pull requests that are open at the same time then
never edit the same lines.
