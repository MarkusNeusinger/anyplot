### Fixed

- **A merge whose renders never reach production now fails instead of
  passing.** `impl-merge.yml` promoted #12800 (waterfall-basic, MUI X)
  with nothing copied: the copy failed with its error hidden, the step
  deleted staging anyway and reported "Promoted images to production",
  so the site showed the previous code's images under the new review.
  The promotion now lists staging first, fails when either theme render
  is missing and the PR changed its implementation, retries a failed
  listing or copy and then fails with staging kept, and names the number
  of files it copied. A new step comments the fixing command on the
  merged PR: a re-render of the merged file in adopt mode, a forced
  regeneration for R and Julia, or a re-dispatch of `impl-merge.yml`
  when only the transfer failed. The step no longer sets object ACLs,
  which the bucket's uniform bucket-level access rejects on every call.
  (#12819)
