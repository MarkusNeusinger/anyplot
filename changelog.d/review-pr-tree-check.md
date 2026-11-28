### Fixed

- **The review job refuses an implementation pull request that changes more than its two
  files.** The pipeline writes exactly the pair's implementation and its metadata on an
  implementation branch, but impl-review checked out whatever the branch held into the
  workspace its later steps run in. "Checkout PR code" now compares the head with `main`
  before that checkout and stops the job when it adds or changes any other path, or anything
  that isn't a regular file. 360 implementation pull requests from September to November each
  changed exactly their two files. A Python step that runs in the workspace before the review
  also keeps the workspace off its import path now. (#15196)
