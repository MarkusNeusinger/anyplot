### Fixed

- **`docs/reference/performance.md` shows the frontend at one instance with
  concurrency 80.** #11828 and #11829 edited the same infrastructure table row
  from different branches, so the frontend line still carried max-instances=3
  and concurrency 15 after both had merged; it now matches `app/cloudbuild.yaml`.
