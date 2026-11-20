### Security

- **The pipeline acts only on its own pull requests.** The pipeline's workflows
  act only on pull requests it opened itself, from this repository's own
  `implementation/<spec-id>/<library>` branches with a registered library and
  targeting `main`. Review, repair, merge and the review retry check each pull
  request with one checker, staged from the workflow's own commit (from `main`
  on a pull-request event), before they check out or write anything; the
  watchdog, impl-generate's existing-PR lookup and daily-regen's pair pick skip
  any other pull request in their listings. A refused pull request gets no
  label, comment or dispatch, only a fixed reason code in the run log, and
  anything the checker cannot read is refused. impl-merge merges only the head
  commit it checked or GitHub's own merges of `main` into it, and treats a pull
  request found merged as merged only at such a head; review and repair write
  only onto the commit that was checked and never over a branch that moved
  meanwhile; the review's write-back
  cleanup closes only the pipeline's own write-back pull requests; repair takes
  its review feedback from the reviewer's own comment only, and the automatic
  retries count only the workflows' own comments. (#13280)
- **Workflow inputs reach no run script as text.** In the pipeline's workflows,
  dispatch inputs and event values go through `env:` and are checked for their
  shape before their first use, and the watchdog takes a spec ID from an issue
  title only in the catalogue's shape. (#13280)
