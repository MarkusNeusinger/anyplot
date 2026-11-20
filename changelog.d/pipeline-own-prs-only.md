### Security

- **The pipeline acts only on its own pull requests.** The pipeline's workflows
  act only on pull requests from this repository's own
  `implementation/<spec-id>/<library>` branches, with a registered library.
  Review, repair, merge and the review retry check each pull request with one
  checker, staged from the workflow's own commit, before they fetch, check out
  or write anything; the watchdog, impl-generate's existing-PR lookup and
  daily-regen's pair pick skip any other pull request in their listings. A
  refused pull request gets no label, comment or dispatch, only a fixed reason
  code in the run log, and anything the checker cannot read is refused. impl-merge
  also merges only the head commit it checked, and repair takes its review
  feedback from the reviewer's own comment only.
